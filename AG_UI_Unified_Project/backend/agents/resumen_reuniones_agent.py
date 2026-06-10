"""
Resumen de reuniones — audio, video, PDF e imágenes vía GCS.
Portado desde AG_UI_agente_resumen_reuniones.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.tools import FunctionTool
from ag_ui_adk import ADKAgent

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")


def analizar_archivo_gcs(gcs_uri: str, mime_type: str, instruccion: str) -> str:
    """
    Analiza un archivo almacenado en Google Cloud Storage.
    Úsalo cuando el usuario comparta una URI gs:// de un archivo de audio, video, imagen o PDF.
    """
    try:
        from google.genai import types as genai_types
        from google.genai import Client

        client = Client(
            vertexai=True,
            project=PROJECT_ID,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

        file_part = genai_types.Part.from_uri(file_uri=gcs_uri, mime_type=mime_type)
        text_part = genai_types.Part.from_text(text=instruccion)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[genai_types.Content(parts=[file_part, text_part], role="user")],
        )
        print(f"[resumen_reuniones] Archivo procesado: {gcs_uri[:80]}...")
        return response.text or "(Sin contenido en la respuesta del modelo)"

    except Exception as e:
        print(f"[resumen_reuniones] Error GCS/Vertex: {e}")
        return f"Error al procesar el archivo: {str(e)}"


root_agent = Agent(
    name="resumen_reuniones",
    model="gemini-2.5-flash",
    description="Agente multimodal para resumir reuniones desde audio, video, PDF e imágenes.",
    instruction=(
        "Eres un asistente especializado en resumir reuniones y contenido multimedia.\n\n"
        "Cuando el mensaje del usuario contenga [METADATA:uri=...,mime=...], extrae la URI y el mime_type "
        "de ese bloque y llama INMEDIATAMENTE al tool 'analizar_archivo_gcs'. "
        "NUNCA menciones la URI gs://, el bucket, GCS ni detalles técnicos en tu respuesta al usuario.\n\n"
        "La instrucción para el tool es la parte del mensaje ANTES del [METADATA:...].\n\n"
        "Para videos/audio de reuniones presenta:\n"
        "- Resumen ejecutivo\n"
        "- Puntos clave discutidos\n"
        "- Compromisos y tareas identificadas\n"
        "- Transcripción si se solicita\n\n"
        "Responde siempre en español, de forma clara y profesional."
    ),
    tools=[FunctionTool(func=analizar_archivo_gcs)],
)

plugins = []
if PROJECT_ID and BQ_DATASET_ID:
    plugins.append(
        BigQueryAgentAnalyticsPlugin(
            project_id=PROJECT_ID,
            dataset_id=BQ_DATASET_ID,
            location=BQ_LOCATION,
            config=BigQueryLoggerConfig(
                enabled=True,
                batch_size=1,
                batch_flush_interval=0.5,
                log_session_metadata=True,
                custom_tags={"agent": "resumen_reuniones", "env": "unified"},
            ),
        )
    )

adk_app = App(
    name="resumen_reuniones_app",
    root_agent=root_agent,
    plugins=plugins,
)

adk_agent = ADKAgent.from_app(
    app=adk_app,
    user_id="resumen_user",
    session_timeout_seconds=3600,
)
