"""
Herramientas de soporte para el agente de análisis de CVs.
Usa ADK Artifacts con GcsArtifactService para pasar PDFs al modelo de forma nativa.
"""
import os
import json
from pathlib import Path
from typing import Optional

import google.genai.types as types
from google.adk.tools.tool_context import ToolContext

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

MIME_MAP = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc":  "application/msword",
}


async def cargar_cvs_como_artefactos(
    tool_context: ToolContext,
    ruta_carpeta: str,
) -> dict:
    """
    Lee todos los CVs de la carpeta y los guarda como ADK Artifacts en GCS.
    Llama esta función UNA SOLA VEZ al inicio del análisis.
    Los artefactos quedan persistidos en GCS y disponibles para que el modelo
    los lea directamente con sus capacidades multimodales nativas.

    Args:
        ruta_carpeta: Ruta absoluta de la carpeta con los CVs descargados.
                      Usar el valor de 'ruta' retornado por descargar_hojas_de_vida.

    Returns:
        dict con lista de artefactos registrados en GCS y nombres de archivo.
    """
    carpeta = Path(ruta_carpeta)
    if not carpeta.exists():
        return {"error": f"Carpeta no encontrada: {ruta_carpeta}", "artefactos": []}

    archivos = [
        f for f in sorted(carpeta.iterdir())
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not archivos:
        return {"error": "No hay archivos PDF/DOCX en la carpeta.", "artefactos": []}

    artefactos_guardados = []

    for archivo in archivos:
        mime_type = MIME_MAP.get(archivo.suffix.lower(), "application/octet-stream")
        try:
            with open(archivo, "rb") as f:
                contenido = f.read()

            parte = types.Part(
                inline_data=types.Blob(
                    data=contenido,
                    mime_type=mime_type,
                )
            )

            # Guardar en GCS vía ADK ArtifactService
            version = await tool_context.save_artifact(
                filename=archivo.name,
                artifact=parte,
            )

            artefactos_guardados.append({
                "nombre_archivo": archivo.name,
                "mime_type": mime_type,
                "version": version,
                "bytes": len(contenido),
            })
            print(f"[ARTIFACT] Guardado en GCS: {archivo.name} (v{version}, {len(contenido)} bytes)")

        except Exception as e:
            print(f"[ARTIFACT ERROR] {archivo.name}: {e}")
            artefactos_guardados.append({
                "nombre_archivo": archivo.name,
                "error": str(e),
            })

    exitosos = [a for a in artefactos_guardados if "error" not in a]

    return {
        "ruta_carpeta": str(carpeta.resolve()),
        "artefactos": artefactos_guardados,
        "total": len(artefactos_guardados),
        "exitosos": len(exitosos),
        "instruccion": (
            f"{len(exitosos)} CVs guardados como artefactos en GCS. "
            "Usa load_artifacts con cada nombre_archivo para cargar y leer "
            "el contenido REAL de cada CV. "
            "SOLO evalúa lo que está escrito en el documento — "
            "NUNCA inventes ni asumas información que no aparezca explícitamente."
        ),
    }


async def guardar_ranking(
    tool_context: ToolContext,
    ruta_carpeta: str,
    ranking: list[dict],
) -> dict:
    """
    Persiste el ranking de candidatos como JSON en disco y como artefacto en GCS.
    Llámala DESPUÉS de haber analizado todos los CVs y construido el ranking completo.

    Args:
        ruta_carpeta: Misma ruta usada en cargar_cvs_como_artefactos.
        ranking: Lista de dicts ordenada por puntaje descendente. Cada dict debe tener:
                 - nombre_candidato (str)
                 - archivo (str)
                 - puntaje (int, 0-100)
                 - requisitos_evaluados (list[dict]): cada uno con:
                   {"requisito": str, "cumple": bool, "evidencia": str}
                   donde evidencia es cita textual del CV o
                   "Sin evidencia en el documento" si no cumple.
                 - resumen (str)
                 - email (str, opcional)

    Returns:
        dict con ruta del archivo guardado y confirmación.
    """
    carpeta = Path(ruta_carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    ranking_data = {"ranking": ranking, "total": len(ranking)}

    # Guardar como JSON en disco local
    output_path = carpeta / "ranking_candidatos.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ranking_data, f, ensure_ascii=False, indent=2)

    # Guardar también como artefacto en GCS
    try:
        json_bytes = json.dumps(ranking_data, ensure_ascii=False, indent=2).encode("utf-8")
        parte_json = types.Part(
            inline_data=types.Blob(
                data=json_bytes,
                mime_type="application/json",
            )
        )
        version = await tool_context.save_artifact(
            filename="ranking_candidatos.json",
            artifact=parte_json,
        )
        print(f"[ARTIFACT] Ranking guardado en GCS como artefacto (v{version})")
    except Exception as e:
        print(f"[ARTIFACT ERROR] No se pudo guardar ranking en GCS: {e}")

    return {
        "guardado_en": str(output_path.resolve()),
        "total_candidatos": len(ranking),
        "top_candidato": ranking[0].get("nombre_candidato") if ranking else None,
        "mensaje": f"✅ Ranking de {len(ranking)} candidatos guardado en disco y GCS.",
    }