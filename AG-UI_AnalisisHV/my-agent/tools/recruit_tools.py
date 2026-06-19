"""
Herramienta 1: Descarga de hojas de vida desde Zoho Recruit.
"""
import os
import requests
from dotenv import load_dotenv
from .zoho_auth import get_headers

load_dotenv()

RECRUIT_BASE = "https://recruit.zoho.com/recruit/v2"
DOWNLOAD_PATH = os.getenv("DOWNLOAD_BASE_PATH", "./cvs_descargados")


def listar_perfiles() -> dict:
    """
    Lista todos los Job Openings en Zoho Recruit con ID, nombre, estado y fecha.
    Úsala cuando el usuario no especifique el perfil o haya varias convocatorias
    del mismo cargo. Muestra la lista para que el usuario elija por ID.

    Returns:
        dict con lista de perfiles (id, nombre, estado, fecha_apertura) y total.
    """
    perfiles = []
    page = 1
    while True:
        res = requests.get(
            f"{RECRUIT_BASE}/Job_Openings",
            headers=get_headers(),
            params={
                "fields": "Job_Opening_Name,Job_Opening_Status,Date_Opened,Target_Date",
                "per_page": 200,
                "page": page,
            },
        )
        res.raise_for_status()
        data = res.json()
        if "data" not in data:
            break
        for job in data["data"]:
            perfiles.append({
                "id": job.get("id"),
                "nombre": job.get("Job_Opening_Name", "Sin nombre"),
                "estado": job.get("Job_Opening_Status", ""),
                "fecha_apertura": job.get("Date_Opened", ""),
                "fecha_cierre": job.get("Target_Date", ""),
            })
        if not data.get("info", {}).get("more_records", False):
            break
        page += 1

    from collections import defaultdict
    agrupados = defaultdict(list)
    for p in perfiles:
        agrupados[p["nombre"]].append(p)

    advertencias = [
        f"⚠️ '{nombre}' tiene {len(convs)} convocatorias — usar ID para diferenciar"
        for nombre, convs in agrupados.items()
        if len(convs) > 1
    ]

    return {
        "perfiles": perfiles,
        "total": len(perfiles),
        "advertencias": advertencias,
        "mensaje": (
            f"Encontré {len(perfiles)} perfiles. "
            + (" | ".join(advertencias) if advertencias else "Sin duplicados.")
            + " Indica el ID del perfil que deseas procesar."
        ),
    }


def _buscar_aplicaciones_por_perfil(nombre_perfil: str, job_opening_id: str) -> tuple[list, str]:
    """
    Busca aplicaciones por nombre de perfil.
    Nota: Zoho Recruit devuelve Job_Opening_Name como string plano en Applications,
    por lo que no es posible filtrar por Job Opening ID directamente.
    Se retornan todas las aplicaciones del perfil sin importar la convocatoria.
    """
    criterio = f"(Job_Opening_Name:equals:{nombre_perfil})"
    todas_las_apps = []
    page = 1

    while True:
        res = requests.get(
            f"{RECRUIT_BASE}/Applications/search",
            headers=get_headers(),
            params={
                "criteria": criterio,
                "fields": "id,Candidate_Name,Email,Job_Opening_Name",
                "per_page": 200,
                "page": page,
            },
        )

        if res.status_code == 204 or not res.text.strip():
            break
        if res.status_code != 200:
            break

        data = res.json()
        if "data" not in data or not data["data"]:
            break

        todas_las_apps.extend(data["data"])

        if not data.get("info", {}).get("more_records", False):
            break
        page += 1

    return todas_las_apps, criterio


def descargar_hojas_de_vida(job_opening_id: str, nombre_perfil: str) -> dict:
    """
    Descarga todas las hojas de vida (PDF, DOCX, DOC) de los candidatos
    que aplicaron a un Job Opening específico, identificado por su ID único.

    Usar SIEMPRE el ID (no solo el nombre) para evitar mezclar candidatos
    de distintas convocatorias del mismo cargo.

    Args:
        job_opening_id: ID único del Job Opening en Zoho Recruit.
                        Obtenlo de listar_perfiles → campo 'id'.
        nombre_perfil:  Nombre del perfil (para nombrar la carpeta y buscar).
                        Obtenlo de listar_perfiles → campo 'nombre'.

    Returns:
        dict con:
          - ruta (str): ruta absoluta de la carpeta. Pasar al agente analisis_cvs.
          - archivos_descargados (list)
          - total (int)
          - errores (list)
          - mensaje (str)
    """
    carpeta_nombre = (
        f"{nombre_perfil}_{job_opening_id}"
        .replace(" ", "_")
        .replace("/", "-")
    )
    carpeta = os.path.join(DOWNLOAD_PATH, carpeta_nombre)
    os.makedirs(carpeta, exist_ok=True)

    # ── Paso 1: obtener aplicaciones ───────────────────────────────────────
    aplicaciones, criterio_usado = _buscar_aplicaciones_por_perfil(
        nombre_perfil, job_opening_id
    )

    if not aplicaciones:
        return {
            "mensaje": (
                f"No se encontraron candidatos para '{nombre_perfil}' "
                f"(ID: {job_opening_id}). "
                "Verifica que el perfil tenga aplicaciones en Zoho Recruit."
            ),
            "archivos_descargados": [],
            "ruta": os.path.abspath(carpeta),
            "total": 0,
            "errores": [],
            "criterio_usado": criterio_usado or "ninguno",
        }

    # ── Paso 2: descargar adjuntos de cada candidato ───────────────────────
    archivos_descargados = []
    errores = []

    for app in aplicaciones:
        candidate_ref = app.get("Candidate_Name") or {}
        candidate_id = (
            candidate_ref.get("id") if isinstance(candidate_ref, dict) else None
        )
        candidate_name = (
            candidate_ref.get("name") if isinstance(candidate_ref, dict) else None
        )
        if not candidate_name:
            email = app.get("Email", "")
            candidate_name = (
                email.split("@")[0] if email else f"Candidato_{app['id']}"
            )

        try:
            modules_to_try = [("Applications", app["id"])]
            if candidate_id:
                modules_to_try.insert(0, ("Candidates", candidate_id))

            descargado = False
            for module, pid in modules_to_try:
                if descargado:
                    break

                att_res = requests.get(
                    f"{RECRUIT_BASE}/{module}/{pid}/Attachments",
                    headers=get_headers(),
                )

                if att_res.status_code == 204 or not att_res.text.strip():
                    continue
                if att_res.status_code != 200:
                    continue

                att_data = att_res.json().get("data", [])
                attachments = [
                    a for a in att_data
                    if any(
                        a.get("File_Name", "").lower().endswith(ext)
                        for ext in [".pdf", ".docx", ".doc"]
                    )
                ]

                for att in attachments:
                    dl = requests.get(
                        f"{RECRUIT_BASE}/{module}/{pid}/Attachments/{att['id']}",
                        headers=get_headers(),
                    )
                    if dl.status_code == 200 and dl.content:
                        safe_name = (
                            candidate_name
                            .replace("/", "-")
                            .replace("\\", "-")
                        )
                        path = os.path.join(
                            carpeta, f"{safe_name}_{att['File_Name']}"
                        )
                        with open(path, "wb") as f:
                            f.write(dl.content)
                        archivos_descargados.append({
                            "candidato": candidate_name,
                            "archivo": path,
                            "email": app.get("Email", ""),
                        })
                        descargado = True
                        break

        except Exception as e:
            errores.append(f"{candidate_name}: {str(e)}")

    ruta_absoluta = os.path.abspath(carpeta)

    return {
        "nombre_perfil": nombre_perfil,
        "job_opening_id": job_opening_id,
        "criterio_usado": criterio_usado,
        "ruta": ruta_absoluta,
        "archivos_descargados": archivos_descargados,
        "total": len(archivos_descargados),
        "errores": errores[:5],
        "mensaje": (
            f"✅ {len(archivos_descargados)} hojas de vida descargadas "
            f"para '{nombre_perfil}' (ID: {job_opening_id}). "
            f"Pasar 'ruta' al agente analisis_cvs: {ruta_absoluta}"
        ),
    }

def obtener_requisitos_perfil(job_opening_id: str) -> dict:
    """
    Obtiene los requisitos y descripción de un Job Opening específico.
    Úsala ANTES de analizar CVs para obtener los criterios de evaluación.

    Args:
        job_opening_id: ID del Job Opening obtenido de listar_perfiles.

    Returns:
        dict con requisitos, descripción y competencias del perfil.
    """
    res = requests.get(
        f"{RECRUIT_BASE}/Job_Openings/{job_opening_id}",
        headers=get_headers(),
        params={
            "fields": "Job_Opening_Name,Job_Description,Requirements,Skills,Industry"
        },
    )

    if res.status_code != 200 or not res.text.strip():
        return {"error": f"No se pudo obtener el perfil ID {job_opening_id}"}

    data = res.json().get("data", [{}])
    perfil = data[0] if isinstance(data, list) and data else data

    return {
        "job_opening_id": job_opening_id,
        "nombre": perfil.get("Job_Opening_Name", ""),
        "descripcion": perfil.get("Job_Description", ""),
        "requisitos": perfil.get("Requirements", ""),
        "habilidades": perfil.get("Skills", ""),
        "industria": perfil.get("Industry", ""),
        "mensaje": (
            "Usar estos requisitos como criterios de evaluación al analizar cada CV. "
            "Para cada requisito indicar si el candidato CUMPLE ✅ o NO CUMPLE ❌."
        ),
    }