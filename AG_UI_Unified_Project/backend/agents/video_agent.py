"""
Video Producer Agent for Luma Cloud
Specialized in creating educational IA content for non-technical audiences.
"""

from ag_ui_adk import ADKAgent
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

# =========================
# TOOL IMPLEMENTATIONS
# =========================

def generar_resumen(transcripcion: str) -> dict:
    """
    Genera un resumen profesional pero claro y sencillo del concepto.
    Enfocado en ser comprensible para audiencias no técnicas.
    """
    return {
        "status": "success",
        "tipo": "resumen",
        "contenido": transcripcion,
        "formato": "resumen_educativo"
    }


def generar_guion_avatar(transcripcion: str) -> dict:
    """
    Genera un guion limpio y listo para ser narrado por el avatar de IA.
    Optimizado para voz e imagen del presentador. El guion puede ser generado con varios tonos si el usuario lo solicita.
    """
    return {
        "status": "success",
        "tipo": "guion_avatar",
        "contenido": transcripcion,
        "formato": "guion_narrable"
    }


def generar_ayudas_visuales(transcripcion: str) -> dict:
    """
    Genera sugerencias de elementos visuales para el video.
    Incluye gráficos, textos en pantalla e imágenes de apoyo.
    """
    return {
        "status": "success",
        "tipo": "ayudas_visuales",
        "contenido": transcripcion,
        "formato": "elementos_visuales"
    }


# =========================
# LLM AGENT DEFINITION
# =========================

agent = LlmAgent(
    model="gemini-2.0-flash", # Updated to a more standard model name if needed, keeping 2.5 if available but 2.0 is common
    name="video_producer",
    description="Asistente de producción de contenido para videos educativos sobre IA.",
    instruction="""Eres el asistente de producción de contenido para el canal educativo de Luma Cloud sobre Inteligencia Artificial.

<contexto>
Eres un estratega en inteligencia artificial aplicada a empresas.
Asistente de producción de contenido para videos educativos sobre IA. Especializado en crear material accesible para audiencias no técnicas de empresas sobre una transcripción o texto.
</contexto>

<instrucciones>
1. Siempre analiza primero la intención del usuario antes de generar contenido.
2. Nunca generes las tres opciones (Resumen, Guion y Ayudas Visuales) al mismo tiempo. Solo la seleccionada.
3. No expliques el proceso interno.
4. El contenido debe ser claro para audiencias no técnicas y con enfoque empresarial.
5. Mantén estructura visual clara.
6. Si el usuario pide ajustes, modifica únicamente el contenido actual.
7. No agregues información que no esté implícita en la transcripción.
8. Siempre ofrece pregunta final de ajuste.
</instrucciones>

TU FLUJO DE TRABAJO:
1. Al recibir transcripción, ofrecer menú: 1) Resumen, 2) Guion para Avatar, 3) Ayudas Visuales.
2. Usar la herramienta apropiada según la respuesta.
3. Preguntar por ajustes o siguiente paso.
""",
    tools=[generar_resumen, generar_guion_avatar, generar_ayudas_visuales],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2000,
    ),
)
