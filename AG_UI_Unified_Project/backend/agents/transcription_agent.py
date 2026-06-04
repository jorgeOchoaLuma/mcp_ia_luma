"""
Voice Transcription Agent
Captures live audio and saves it to a Markdown file.
"""

import re
from datetime import datetime
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import ToolContext
from google.genai import types

# CONFIG
VOICE_NAME    = "Aoede"
LANGUAGE_CODE = "es-ES"

def store_transcription(transcription: str, tool_context: ToolContext) -> dict:
    """Store and save the full transcription to a Markdown file on disk."""
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
        return {"status": "saved", "path": str(fpath)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

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

agent = LlmAgent(
    model=gemini_with_voice,
    name="transcription_specialist",
    tools=[store_transcription],
    instruction=f"""Eres un asistente de transcripción de voz en tiempo real.
Tu voz es {VOICE_NAME} y hablas en español.
ESCUCHA todo lo que dice el usuario y recuérdalo exactamente.

Cuando el usuario diga "ya terminé", "guarda", "fin", "terminar", "save" o "done":
1. Llama INMEDIATAMENTE a `store_transcription` con TODO el texto transcrito.
2. Confirma al usuario la ruta donde se guardó el archivo.
""",
)
