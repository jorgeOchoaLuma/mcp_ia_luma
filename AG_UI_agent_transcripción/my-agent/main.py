# ./adk_agent_samples/voice_transcription_agent/agent.py
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import ToolContext
from google.genai import types
from dotenv import load_dotenv
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types


from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import Optional

load_dotenv()

# ─── CONFIGURA AQUÍ ────────────────────────────────────────────────────────
VOICE_NAME    = "Aoede"   # Aoede, Leda, Zephyr, Puck, Charon, Kore, Fenrir, Orus
LANGUAGE_CODE = "es-ES"   # "es-ES", "es-US", "en-US", "en-GB", "pt-BR"
# ───────────────────────────────────────────────────────────────────────────


# =============================================================================
# TOOL: guarda la transcripción directo desde Python
# =============================================================================
def store_transcription(transcription: str, tool_context: ToolContext) -> dict:
    """Store and save the full transcription to a Markdown file on disk.

    Call this tool immediately when the user says they are done speaking.
    Trigger words: 'ya terminé', 'guarda', 'fin', 'terminar', 'save', 'done'.

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
        print(f"\n✅ [SAVED] {fpath}\n")
        return {"status": "saved", "path": str(fpath)}
    except Exception as e:
        print(f"\n❌ [ERROR] {e}\n")
        return {"status": "error", "error": str(e)}


# =============================================================================
# Instancia Gemini con voz configurada — la forma correcta según docs ADK
# =============================================================================
gemini_with_voice = Gemini(
    model="gemini-live-2.5-flash",
    speech_config=types.SpeechConfig(
        language_code=LANGUAGE_CODE,
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=VOICE_NAME
            )
        ),
    ),
)

# =============================================================================
# AGENTE RAÍZ
# =============================================================================
agent = LlmAgent(
    model=gemini_with_voice,   # instancia Gemini, no string
    name="voice_transcription_agent",
    tools=[store_transcription],
    instruction=f"""Eres un asistente de transcripción de voz en tiempo real.
Tu voz es {VOICE_NAME} y hablas en español.

ESCUCHA todo lo que dice el usuario y recuérdalo exactamente.

Cuando el usuario diga "ya terminé", "guarda", "fin", "terminar", "save" o "done":
1. Llama INMEDIATAMENTE a `store_transcription` con TODO el texto transcrito.
2. Confirma al usuario la ruta donde se guardó el archivo.

Reglas:
- Transcribe con puntuación natural.
- Fragmentos inaudibles: [inaudible]
- Varios hablantes: "Speaker 1:", "Speaker 2:"
- NUNCA inventes contenido.
""",
)

print("=" * 65)
print("🎙️  Voice Transcription Agent")
print(f"   Voz    : {VOICE_NAME}")
print(f"   Idioma : {LANGUAGE_CODE}")
print(f"   Modelo : gemini-2.0-flash-live-preview-04-09")
print("   Salida : ~/Documents/transcripciones_voz/")
print("   Di 'ya terminé' para guardar")
print("=" * 65)


adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="app_url_contexto_luma",
    user_id="campana_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)


app = FastAPI()
add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)





