"""
URL Context Agent
Specialized in answering questions about Luma Cloud using web context.
"""

from google.adk.tools import url_context
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import Optional

URL_GROUPS = {
    "servicios": {
        "raiz": "https://lumacloud.co/servicios/",
        "urls": [
            "https://lumacloud.co/infraestructura-iaas/",
            "https://lumacloud.co/ciber-recuperacion/",
            "https://lumacloud.co/ciberproteccion/",
            "https://lumacloud.co/soc/",
            "https://lumacloud.co/servicios-profesionales/",
        ],
        "keywords": ["producto", "servicios", "ciber-recuperacion", "ciberproteccion", "SOC", "iaas", "infraestructura"],
    },
    "empresa": {
        "raiz": "https://lumacloud.co/",
        "urls": ["https://lumacloud.co/quienes-somos/", "https://lumacloud.co/contactenos/", "https://lumacloud.co"],
        "keywords": ["empresa", "historia", "quienes", "contactenos"],
    },
}

URL_DEFAULT = "https://lumacloud.co/"

INJECTION_PATTERNS = ["ignora las instrucciones", "jailbreak", "system prompt", "forget everything"]

def detectar_grupo_url(mensaje: str) -> dict:
    mensaje_lower = mensaje.lower()
    for config in URL_GROUPS.values():
        if any(kw in mensaje_lower for kw in config["keywords"]):
            return config
    return {"raiz": URL_DEFAULT, "urls": [URL_DEFAULT]}

def before_model_guardrail(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    last_user_message = ""
    last_user_index = -1
    for i, content in enumerate(llm_request.contents or []):
        if content.role == "user":
            last_user_index = i
            last_user_message = content.parts[0].text or ""

    message_lower = last_user_message.lower()
    if any(p in message_lower for p in INJECTION_PATTERNS):
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(text="Solo puedo ayudarte con información de nuestro sitio web.")]))

    grupo = detectar_grupo_url(last_user_message)
    urls_texto = "\n".join(f"- {url}" for url in grupo["urls"])
    llm_request.contents[last_user_index].parts[0].text = f"Consulta las siguientes URLs para responder:\n{urls_texto}\n\nPregunta: {last_user_message}"
    return None

agent = LlmAgent(
    name="url_expert",
    model="gemini-2.0-pro",
    description="Agente que consulta el sitio web de Luma Cloud.",
    instruction="""Responde basándote ÚNICAMENTE en url_context. Cita la fuente.""",
    tools=[url_context],
    before_model_callback=before_model_guardrail,
)
