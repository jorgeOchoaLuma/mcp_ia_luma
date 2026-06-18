"""
Live voice transcription WebSocket — gemini-live-2.5-flash.
Portado desde AG_UI_agent_transcripción-bigquery (/live/ws).
"""

import asyncio
import base64
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.agents import LlmAgent, LiveRequestQueue
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.models import LlmRequest, LlmResponse
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

log = logging.getLogger(__name__)

LANGUAGE_CODE = "es-ES"
LIVE_MODEL = "gemini-live-2.5-flash"
APP_NAME = "voice_transcription_live"


def _block_model_response(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    return LlmResponse(content=types.Content(role="model", parts=[]), turn_complete=True)


live_agent = LlmAgent(
    model=Gemini(model=LIVE_MODEL),
    name="live_transcriber",
    instruction="Solo escucha. No respondas nada.",
    before_model_callback=_block_model_response,
)

live_session_service = InMemorySessionService()
live_runner = Runner(
    agent=live_agent,
    app_name=APP_NAME,
    session_service=live_session_service,
)

live_run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["TEXT"],
    input_audio_transcription=types.AudioTranscriptionConfig(
        language_codes=[LANGUAGE_CODE],
    ),
)


def register_transcription_live_ws(app) -> None:
    """Mount WebSocket at /transcription/live/ws."""

    @app.websocket("/transcription/live/ws")
    async def live_transcription_ws(websocket: WebSocket):
        await websocket.accept()
        log.info("[transcription/live] Cliente conectado")

        session = await live_session_service.create_session(
            app_name=APP_NAME,
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
                        queue.close()
                        break
            except WebSocketDisconnect:
                queue.close()

        async def receive_from_runner():
            try:
                async for event in live_runner.run_live(
                    user_id="live_user",
                    session_id=session.id,
                    live_request_queue=queue,
                    run_config=live_run_config,
                ):
                    if event.input_transcription and event.input_transcription.text:
                        text = event.input_transcription.text.strip()
                        if not text:
                            continue
                        is_final = getattr(event.input_transcription, "is_final", True)
                        await websocket.send_text(
                            json.dumps({
                                "type": "transcript",
                                "text": text,
                                "partial": not is_final,
                            })
                        )
                await websocket.send_text(json.dumps({"type": "done"}))
            except Exception as e:
                log.error("[transcription/live] Error: %s", e)
                try:
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": str(e)})
                    )
                except Exception:
                    pass

        try:
            await asyncio.gather(receive_from_browser(), receive_from_runner())
        finally:
            log.info("[transcription/live] Sesión cerrada")
