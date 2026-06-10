import os
from pathlib import Path
from dotenv import load_dotenv
from gcp_credentials import setup_gcp_credentials
from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext



load_dotenv()
setup_gcp_credentials(base_dir=Path(__file__).resolve().parent)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")

# --- Plugin BigQuery ---
bq_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=BQ_DATASET_ID,
    location=BQ_LOCATION,
    config=BigQueryLoggerConfig(
        enabled=True,
        batch_size=1,
        batch_flush_interval=0.5,
        log_session_metadata=True,
        custom_tags={"agent": "resumenVideo_audio_reuniones", "env": "prod"},
    ),
)

# --- Tool: analizar archivo desde GCS ---
def analizar_archivo_gcs(gcs_uri: str, mime_type: str, instruccion: str) -> str:
    """
    Analiza un archivo almacenado en Google Cloud Storage.
    Úsalo cuando el usuario comparta una URI gs:// de un archivo de audio, video, imagen o PDF.

    Args:
        gcs_uri: URI del archivo en GCS. Ejemplo: gs://bucket/archivo.mp4
        mime_type: Tipo MIME. Ejemplo: video/mp4, audio/mpeg, application/pdf, image/jpeg
        instruccion: Qué hacer con el archivo. Ejemplo: "genera un resumen", "transcribe el audio"

    Returns:
        Análisis completo del archivo
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
            model="gemini-3.1-flash-lite",
            contents=[genai_types.Content(parts=[file_part, text_part], role="user")],
        )
        return response.text

    except Exception as e:
        return f"Error al procesar el archivo: {str(e)}"


# --- Agente ---
root_agent = Agent(
    name="resumenVideo_audio_reuniones",
    model="gemini-3.1-flash-lite",
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

# --- App con plugin ---
adk_app = App(
    name="resumenVideo_audio_reuniones",
    root_agent=root_agent,
    plugins=[bq_plugin],
)

# --- AG-UI ---
adk_agent = ADKAgent.from_app(
    app=adk_app,
    user_id="demo_user",
    session_timeout_seconds=3600,
)

app = FastAPI()
add_adk_fastapi_endpoint(app, adk_agent, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, timeout_keep_alive=120)