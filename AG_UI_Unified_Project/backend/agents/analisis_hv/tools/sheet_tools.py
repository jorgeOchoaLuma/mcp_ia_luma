"""
Herramienta 3: Exportar ranking a Zoho Sheet.
Crea o actualiza una hoja de cálculo con el ranking de candidatos.
"""
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from .zoho_auth import get_headers

load_dotenv()

SHEET_BASE = "https://sheet.zoho.com/api/v2"
WORKBOOK_ID = os.getenv("ZOHO_SHEET_WORKBOOK_ID", "")

# Columnas del ranking — alineadas con el output real de analisis_cvs
COLUMNAS = [
    "Posición", "Nombre", "Email", "Archivo", "Puntaje (%)",
    "Requisitos Cumplidos", "Total Requisitos", "Resumen",
]


def exportar_ranking_a_zoho_sheet(nombre_perfil: str, ranking: list[dict]) -> dict:
    """
    Exporta el ranking de candidatos a Zoho Sheet.
    Inserta filas en la hoja 'Hoja1'. Requiere que 'Hoja1' ya tenga los encabezados creados.

    Args:
        nombre_perfil: Nombre del perfil evaluado (para referencia).
        ranking: Lista de dicts retornada por analisis_cvs, con el formato:
                 nombre_candidato, archivo, puntaje, requisitos_evaluados
                 (lista de {requisito, cumple, evidencia}), resumen.
    """
    if not WORKBOOK_ID:
        return {
            "error": "ZOHO_SHEET_WORKBOOK_ID no configurado en el .env",
            "mensaje": "Configura el ID del workbook en tu .env para exportar a Zoho Sheet.",
        }

    if not ranking:
        return {"mensaje": "No hay datos para exportar.", "filas_escritas": 0}

    nombre_hoja = "Hoja1"

    # ── Preparar filas — tolerante a distintos esquemas de campo ───────────
    filas = []
    for i, c in enumerate(ranking, start=1):
        # Nombre: soporta tanto 'nombre_candidato' (analisis_cvs) como 'nombre' (legacy)
        nombre = c.get("nombre_candidato") or c.get("nombre") or c.get("candidato_zoho", "")

        # Puntaje: soporta 'puntaje' (analisis_cvs) como 'score_total' (legacy)
        puntaje = c.get("puntaje", c.get("score_total", ""))

        # Requisitos evaluados (formato nuevo de analisis_cvs)
        requisitos = c.get("requisitos_evaluados", [])
        if isinstance(requisitos, list) and requisitos:
            cumplidos = sum(1 for r in requisitos if r.get("cumple") is True or r.get("cumple") == "✅")
            total_req = len(requisitos)
        else:
            cumplidos = ""
            total_req = ""

        filas.append({
            "Posición": str(i),
            "Nombre": nombre,
            "Email": c.get("email", c.get("email_zoho", "")),
            "Archivo": c.get("archivo", ""),
            "Puntaje (%)": str(puntaje),
            "Requisitos Cumplidos": str(cumplidos),
            "Total Requisitos": str(total_req),
            "Resumen": c.get("resumen", ""),
        })

    # ── Escribir en lotes de 100 ────────────────────────────────────────────
    filas_escritas = 0
    errores = []
    for i in range(0, len(filas), 100):
        lote = filas[i:i + 100]
        res = requests.post(
            f"{SHEET_BASE}/{WORKBOOK_ID}",
            headers=get_headers(),
            data={
                "method": "worksheet.records.add",
                "worksheet_name": nombre_hoja,
                "insert_data": json.dumps(lote),
            },
        )

        try:
            res_data = res.json()
            if res.status_code == 200 and res_data.get("status") == "success":
                filas_escritas += len(lote)
            else:
                error_msg = res_data.get("error_message", res.text)
                if res_data.get("error_code") == 2884:
                    return {
                        "error": True,
                        "mensaje": (
                            "⚠️ La 'Hoja1' en Zoho Sheet está vacía. "
                            "Debes crear la primera fila con los encabezados: "
                            + ", ".join(COLUMNAS)
                        ),
                    }
                errores.append(f"Lote {i // 100 + 1}: {error_msg}")
        except Exception:
            errores.append(f"Lote {i // 100 + 1}: error {res.status_code} - {res.text}")

    url = f"https://sheet.zoho.com/sheet/open/{WORKBOOK_ID}"

    if errores and filas_escritas == 0:
        return {
            "error": True,
            "errores": errores,
            "mensaje": f"Hubo un error al exportar: {errores[0]}",
        }

    return {
        "nombre_hoja": nombre_hoja,
        "workbook_id": WORKBOOK_ID,
        "filas_escritas": filas_escritas,
        "url": url,
        "errores": errores,
        "mensaje": (
            f"✅ Ranking exportado a Zoho Sheet: '{nombre_hoja}', "
            f"{filas_escritas} candidatos. "
            f"Abre aquí: {url}"
        ),
    }