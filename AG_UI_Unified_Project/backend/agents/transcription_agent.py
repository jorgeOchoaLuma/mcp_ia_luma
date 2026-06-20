"""
Voice Transcription Agent
─────────────────────────
/          → AG-UI (ADKAgent.from_app())  — recibe texto transcrito, llama store_transcription
             BigQueryAgentAnalyticsPlugin logea todos los eventos del agente AG-UI
/live/ws   → WebSocket ADK — recibe audio PCM base64 del browser,
             usa Runner.run_live() + gemini-live-2.5-flash,
             devuelve SOLO event.input_transcription (lo que dijo el usuario)
             El before_model_callback bloquea cualquier respuesta conversacional.

.env requerido:
    GOOGLE_CLOUD_PROJECT=
    GOOGLE_CLOUD_LOCATION=
    GOOGLE_GENAI_USE_VERTEXAI=True
    BQ_DATASET_ID=
    BQ_LOCATION=
"""

import asyncio
import base64
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.apps import App
from google.adk.models import LlmResponse, LlmRequest
from google.adk.models.google_llm import Gemini
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

load_dotenv()

# ─── LOGGING ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ─── CONFIG ────────────────────────────────────────────────────────────────
VOICE_NAME    = "Aoede"   # Aoede, Leda, Zephyr, Puck, Charon, Kore, Fenrir, Orus
LANGUAGE_CODE = "es-ES"   # "es-ES", "es-US", "en-US", "en-GB", "pt-BR"
LIVE_MODEL    = "gemini-live-2.5-flash"
AGUI_MODEL    = "gemini-2.5-flash"
APP_NAME      = "voice_transcription_app"

# GCP / BigQuery — leídos del .env
PROJECT_ID  = os.environ["GOOGLE_CLOUD_PROJECT"]
BQ_DATASET  = os.environ["BQ_DATASET_ID"]
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")
# ───────────────────────────────────────────────────────────────────────────


# =============================================================================
# CALLBACK LIVE: bloquea la respuesta conversacional del modelo Live
# =============================================================================
def block_model_response(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Cancels every model response — transcription comes from input_transcription only."""
    return LlmResponse(
        content=types.Content(role="model", parts=[]),
        turn_complete=True,
    )


# =============================================================================
# TOOL AG-UI: guarda la transcripción en disco
# =============================================================================
def store_transcription(transcription: str, tool_context: ToolContext) -> dict:
    """Store and save the full transcription to a Markdown file on disk.

    Call this tool immediately when the user says they are done speaking.
    Trigger words: 'ya terminé', 'guarda', 'fin', 'terminar', 'save', 'done', 'guardar'.

    Args:
        transcription: The complete transcribed text of everything said in this session.

    Returns:
        dict with 'status' and 'path' of the saved file.
    """
    tool_context.state["transcription_text"] = transcription

    try:
        fecha   = datetime.now().strftime("%Y-%m-%d")
        hora    = datetime.now().strftime("%H:%M:%S")
        words   = re.sub(r'[^\w\s]', '', transcription).split()
        title   = " ".join(words[:5]) if words else "transcripcion_voz"
        safe    = re.sub(r'[<>:"/\\|?*\s\x00-\x1f]', "_", title)
        out_dir = Path.home() / "Documents" / "transcripciones_voz"
        out_dir.mkdir(parents=True, exist_ok=True)
        fpath   = out_dir / f"{safe}_{fecha}.md"
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
        log.info("✅ [SAVED] %s", fpath)
        return {"status": "saved", "path": str(fpath)}
    except Exception as e:
        log.error("❌ [ERROR] %s", e)
        return {"status": "error", "error": str(e)}


# =============================================================================
# BIGQUERY PLUGIN
# =============================================================================
bq_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=BQ_DATASET,
    location=BQ_LOCATION,
    config=BigQueryLoggerConfig(
        enabled=True,
        batch_size=1,                    # baja latencia
        batch_flush_interval=0.5,
        shutdown_timeout=10.0,
        log_session_metadata=True,
        auto_schema_upgrade=True,
        create_views=True,               # crea vistas por tipo de evento (ADK ≥1.27)
        custom_tags={
            "app": APP_NAME,
            "env": os.environ.get("ENV", "dev"),
        },
    ),
)


# =============================================================================
# AGENTE AG-UI — acumula texto transcrito, llama store_transcription con keyword
# =============================================================================
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

# App ADK — requerido para que el plugin de BigQuery funcione correctamente
agui_app = App(
    name=APP_NAME,
    root_agent=agui_agent,
    plugins=[bq_plugin],
)

# ADKAgent via from_app() para que el plugin se ejecute en cada invocación
adk_agent = ADKAgent.from_app(
    app=agui_app,
    user_id="voice_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)


# =============================================================================
# AGENTE LIVE — gemini-live-2.5-flash via ADK Runner
# before_model_callback bloquea respuestas conversacionales.
# Solo usamos event.input_transcription.
# =============================================================================
live_agent = LlmAgent(
    model=Gemini(model=LIVE_MODEL),
    name="live_transcriber",
    instruction="Solo escucha. No respondas nada.",
    before_model_callback=block_model_response,
)

live_session_service = InMemorySessionService()
live_runner = Runner(
    agent=live_agent,
    app_name=APP_NAME + "_live",
    session_service=live_session_service,
)

live_run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["TEXT"],
    input_audio_transcription=types.AudioTranscriptionConfig(
        language_codes=[LANGUAGE_CODE],
    ),
)
