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


# =============================================================================
# FASTAPI APP
# =============================================================================
app = FastAPI(title="Voice Transcription Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_adk_fastapi_endpoint(app, adk_agent, path="/")


# =============================================================================
# WEBSOCKET /live/ws — ADK Runner.run_live() con gemini-live-2.5-flash
# =============================================================================
@app.websocket("/live/ws")
async def live_transcription_ws(websocket: WebSocket):
    """
    Protocolo de mensajes (JSON):

    Browser → Server:
        { "type": "audio", "data": "<base64 PCM 16kHz 16-bit mono>" }
        { "type": "stop" }

    Server → Browser:
        { "type": "transcript", "text": "...", "partial": true|false }
        { "type": "done" }
        { "type": "error", "message": "..." }
    """
    await websocket.accept()
    log.info("🔌 [Live WS] Cliente conectado")

    session = await live_session_service.create_session(
        app_name=APP_NAME + "_live",
        user_id="live_user",
    )

    queue = LiveRequestQueue()

    async def receive_from_browser():
        try:
            while True:
                raw = await websocket.receive_text()
                msg = json.loads(raw)

                if msg["type"] == "audio":
                    pcm_bytes = base64.b64decode(msg["data"])
                    queue.send_realtime(
                        types.Blob(
                            data=pcm_bytes,
                            mime_type="audio/pcm;rate=16000",
                        )
                    )

                elif msg["type"] == "stop":
                    log.info("🛑 [Live WS] Stop — cerrando queue")
                    queue.close()
                    break

        except WebSocketDisconnect:
            log.info("🔌 [Live WS] Cliente desconectado")
            queue.close()

    async def receive_from_runner():
        try:
            async for event in live_runner.run_live(
                user_id="live_user",
                session_id=session.id,
                live_request_queue=queue,
                run_config=live_run_config,
            ):
                # ── Debug ────────────────────────────────────────────────
                has_input_tr  = event.input_transcription is not None
                has_content   = bool(event.content and event.content.parts)
                content_text  = ""
                if has_content:
                    content_text = " | ".join(
                        p.text for p in event.content.parts if getattr(p, "text", None)
                    )
                log.debug(
                    "[event] author=%r input_tr=%s content=%r(%r) partial=%s turn_complete=%s",
                    event.author, has_input_tr, has_content,
                    content_text[:60], event.partial, event.turn_complete,
                )
                # ─────────────────────────────────────────────────────────

                # ✅ SOLO input_transcription — nunca content del modelo
                if event.input_transcription and event.input_transcription.text:
                    text = event.input_transcription.text.strip()
                    if not text:
                        continue
                    is_final = getattr(event.input_transcription, "is_final", True)
                    log.info("📝 [STT is_final=%s] %s", is_final, text)
                    await websocket.send_text(
                        json.dumps({
                            "type": "transcript",
                            "text": text,
                            "partial": not is_final,
                        })
                    )
                # ❌ Ignorar cualquier content conversacional del modelo

            await websocket.send_text(json.dumps({"type": "done"}))

        except Exception as e:
            log.error("❌ [Live WS] Error en runner: %s", e)
            try:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": str(e)})
                )
            except Exception:
                pass

    try:
        await asyncio.gather(
            receive_from_browser(),
            receive_from_runner(),
        )
    except Exception as e:
        log.error("❌ [Live WS] Error general: %s", e)
    finally:
        log.info("🔌 [Live WS] Sesión cerrada")


# =============================================================================
# MAIN
# =============================================================================
print("=" * 65)
print("🎙️  Voice Transcription Agent")
print(f"   Voz        : {VOICE_NAME}")
print(f"   Idioma     : {LANGUAGE_CODE}")
print(f"   Live model : {LIVE_MODEL}  → ws://localhost:8000/live/ws")
print(f"   AG-UI model: {AGUI_MODEL}  → http://localhost:8000/")
print(f"   BigQuery   : {PROJECT_ID}.{BQ_DATASET} ({BQ_LOCATION})")
print("   Salida     : ~/Documents/transcripciones_voz/")
print("=" * 65)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)