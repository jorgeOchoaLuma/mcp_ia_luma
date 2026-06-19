"""
Voice Transcription Agent — modo acumulación (bigquery variant).
Acumula fragmentos de voz; guarda en disco solo con palabra clave.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.tools import ToolContext

from ag_ui_adk import ADKAgent

log = logging.getLogger(__name__)

VOICE_NAME = "Aoede"
LANGUAGE_CODE = "es-ES"
AGUI_MODEL = "gemini-2.5-flash"
APP_NAME = "voice_transcription_app"

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET = os.getenv("BQ_DATASET_ID", "")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")


def store_transcription(transcription: str, tool_context: ToolContext) -> dict:
    """Store and save the full transcription to a Markdown file on disk."""
    tool_context.state["transcription_text"] = transcription

    try:
        fecha = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        words = re.sub(r"[^\w\s]", "", transcription).split()
        title = " ".join(words[:5]) if words else "transcripcion_voz"
        safe = re.sub(r'[<>:"/\\|?*\s\x00-\x1f]', "_", title)
        out_dir = Path.home() / "Documents" / "transcripciones_voz"
        out_dir.mkdir(parents=True, exist_ok=True)
        fpath = out_dir / f"{safe}_{fecha}.md"
        fpath.write_text(
            f"# 🎙️ {title}\n\n"
            f"> **Fecha:** {fecha}  \n"
            f"> **Hora:** {hora}  \n"
            f"> **Voz:** {VOICE_NAME} | **Idioma:** {LANGUAGE_CODE}  \n\n"
            f"---\n\n"
            f"## 📝 Transcripción\n\n"
            f"{transcription.strip()}\n\n"
            f"---\n*Fin — {fecha} {hora}*\n",
            encoding="utf-8",
        )
        log.info("Transcription saved: %s", fpath)
        return {"status": "saved", "path": str(fpath)}
    except Exception as e:
        log.error("Transcription save error: %s", e)
        return {"status": "error", "error": str(e)}


agui_agent = LlmAgent(
    model=AGUI_MODEL,
    name="voice_transcription_agent",
    tools=[store_transcription],
    instruction="""Eres un sistema de acumulación de transcripciones de voz.

MODO ACUMULACIÓN (la mayoría del tiempo):
- El usuario te envía fragmentos de texto transcrito desde el micrófono.
- Acumula cada fragmento en el estado interno de la sesión.
- NO respondas nada. Silencio absoluto. Cero confirmaciones. Cero "Entendido".
- NUNCA repitas el texto que recibiste.
- NUNCA digas que estás esperando más texto.

MODO GUARDADO (solo cuando detectas palabra clave):
- Palabras clave: "ya terminé", "guarda", "guardar", "fin", "terminar", "save", "done".
- Cuando detectes una palabra clave: llama a `store_transcription` con TODO el texto acumulado.
- Después de guardar: confirma SOLO la ruta del archivo. Nada más.

REGLA DE ORO: si el mensaje NO contiene una palabra clave → NO respondas NADA.
""",
)

plugins = []
if PROJECT_ID and BQ_DATASET:
    bq_plugin = BigQueryAgentAnalyticsPlugin(
        project_id=PROJECT_ID,
        dataset_id=BQ_DATASET,
        location=BQ_LOCATION,
        config=BigQueryLoggerConfig(
            enabled=True,
            batch_size=1,
            batch_flush_interval=0.5,
            shutdown_timeout=10.0,
            log_session_metadata=True,
            auto_schema_upgrade=True,
            create_views=True,
            custom_tags={
                "app": APP_NAME,
                "env": os.environ.get("ENV", "dev"),
            },
        ),
    )
    plugins.append(bq_plugin)

agui_app = App(
    name=APP_NAME,
    root_agent=agui_agent,
    plugins=plugins,
)

adk_agent = ADKAgent.from_app(
    app=agui_app,
    user_id="voice_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

# Compatibilidad si algo importa `agent`
agent = agui_agent
