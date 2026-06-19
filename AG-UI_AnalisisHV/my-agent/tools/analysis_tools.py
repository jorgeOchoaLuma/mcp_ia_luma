"""
Herramientas de soporte para el agente de análisis de CVs.
"""
import os
import json
import base64
from pathlib import Path
from typing import Optional
import time

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}


def leer_cv_como_bytes(ruta_carpeta: str, nombre_archivo: Optional[str] = None) -> dict:
    """
    Lee uno o todos los CVs de una carpeta y los devuelve como bytes en base64
    para que el agente pueda analizarlos directamente con visión multimodal.

    Llámala primero SIN nombre_archivo para listar qué archivos hay.
    Luego llámala CON nombre_archivo para leer cada uno.

    Args:
        ruta_carpeta: Ruta absoluta de la carpeta con los CVs descargados.
        nombre_archivo: Nombre de un archivo específico a leer. Si es None,
                        devuelve solo la lista de archivos disponibles.

    Returns:
        Si nombre_archivo es None: dict con lista de archivos disponibles.
        Si nombre_archivo tiene valor: dict con contenido en base64 y mime_type.
    """
    # Pequeña pausa defensiva para no saturar RPM de Vertex AI
    if nombre_archivo is not None:
        time.sleep(1.5)
                   
    carpeta = Path(ruta_carpeta)

    if not carpeta.exists():
        return {"error": f"Carpeta no encontrada: {ruta_carpeta}", "archivos": []}

    archivos_disponibles = [
        f.name for f in sorted(carpeta.iterdir())
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not archivos_disponibles:
        return {"error": "No hay archivos PDF/DOCX en la carpeta.", "archivos": []}

    # Solo listar
    if nombre_archivo is None:
        return {
            "archivos": archivos_disponibles,
            "total": len(archivos_disponibles),
            "ruta_carpeta": str(carpeta.resolve()),
            "instruccion": "Llama esta función de nuevo con cada nombre_archivo para leer el contenido.",
        }

    # Leer archivo específico
    archivo = carpeta / nombre_archivo
    if not archivo.exists():
        return {"error": f"Archivo no encontrado: {nombre_archivo}"}

    suffix = archivo.suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
    }

    with open(archivo, "rb") as f:
        contenido_b64 = base64.b64encode(f.read()).decode()

    return {
        "nombre_archivo": nombre_archivo,
        "mime_type": mime_map.get(suffix, "application/octet-stream"),
        "contenido_base64": contenido_b64,
        "instruccion": (
            "Analiza este documento usando tus capacidades multimodales. "
            "Evalúa el CV y asigna puntaje 0-100 con justificación."
        ),
    }


def guardar_ranking(
    ruta_carpeta: str,
    ranking: list[dict],
) -> dict:
    """
    Persiste el ranking de candidatos como JSON en la carpeta de descarga.

    Args:
        ruta_carpeta: Misma ruta usada en leer_cv_como_bytes.
        ranking: Lista de dicts ordenada por puntaje descendente. Cada dict debe tener:
                 - nombre_candidato (str)
                 - archivo (str)
                 - puntaje (int, 0-100)
                 - requisitos_evaluados (list[dict]): cada uno con
                   {"requisito": str, "cumple": bool, "evidencia": str}
                   El campo 'evidencia' debe ser una cita textual del CV o
                   "Sin evidencia en el documento" si no cumple.
                 - resumen (str)

    Returns:
        dict con ruta del archivo guardado y confirmación.
    """
    carpeta = Path(ruta_carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    output_path = carpeta / "ranking_candidatos.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"ranking": ranking, "total": len(ranking)},
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "guardado_en": str(output_path.resolve()),
        "total_candidatos": len(ranking),
        "top_candidato": ranking[0].get("nombre_candidato") if ranking else None,
        "mensaje": f"✅ Ranking de {len(ranking)} candidatos guardado.",
    }

