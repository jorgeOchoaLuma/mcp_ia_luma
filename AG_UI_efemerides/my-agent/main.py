import os
import asyncio
import logging
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.skills import load_skill_from_dir
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

os.environ["GOOGLE_CLOUD_LOCATION"]     = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

PROJECT_ID    = os.environ["GOOGLE_CLOUD_PROJECT"]
BQ_DATASET_ID = os.getenv("BQ_DATASET_ID", "agente_analytics_db")

# ─── 1. Plugin ────────────────────────────────────────────────────────────────
plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=BQ_DATASET_ID,
    table_id="agent_events",
    location="us-central1",
    config=BigQueryLoggerConfig(
        enabled=True,
        batch_size=1,
        shutdown_timeout=10.0,
        create_views=True,
        log_session_metadata=True,
    ),
)

# ─── 2. Skill ─────────────────────────────────────────────────────────────────
# load_skill_from_dir lee la carpeta directamente (no la importa como paquete
# Python), así que el nombre puede seguir con guión: "efemerides-searcher".
skill_path = os.path.join(os.path.dirname(__file__), 'skills', 'efemerides-searcher')
efemerides_skill = load_skill_from_dir(skill_path)

_GENERATIVE_UI_INSTRUCTION = """
Cuando encuentres efemérides, llama SIEMPRE a la tool `efemerides_card`
pasando el array completo (fecha, evento, categoria, descripcion) para que
el frontend las muestre como tarjetas — nunca respondas el JSON como texto
plano ni en formato markdown. Después de llamar `efemerides_card`, agrega un
mensaje breve en texto conversacional (1-2 frases) resumiendo lo que
encontraste. Si no hay resultados, llama a `efemerides_card` con una lista
vacía y explica brevemente por qué.

No te conformes con la primera búsqueda: sigue las instrucciones de
cobertura mínima del skill (varias búsquedas, mínimo ~9 efemérides
repartidas entre las 3 categorías) antes de llamar `efemerides_card`.
"""

# ─── 3. Helper async ──────────────────────────────────────────────────────────
def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except Exception as e:
        logging.warning(f"[BQ_PLUGIN] _run_async error: {e}")

# ─── 4. Callbacks — keyword-only como exige la firma del plugin ───────────────

def before_model(callback_context: CallbackContext, llm_request: LlmRequest):
    """Registra LLM_REQUEST en BigQuery."""
    try:
        _run_async(plugin.before_model_callback(
            callback_context=callback_context,
            llm_request=llm_request,
        ))
        logging.info("[BQ_PLUGIN] LLM_REQUEST enviado a BigQuery")
    except Exception as e:
        logging.warning(f"[BQ_PLUGIN] before_model error: {e}")
    return None


def _stop_on_terminal_text(callback_context: CallbackContext, llm_response: LlmResponse):
    """Termina el loop agentic en un turno final de solo texto.

    NO viene incluido en ag_ui_adk — sin esto, Gemini puede volver a llamar
    la misma tool (p.ej. showEfemerides) indefinidamente después de que el
    frontend la resuelve.
    """
    content = llm_response.content
    if not content or not content.parts or getattr(llm_response, "partial", False):
        return None

    finish_reason = getattr(llm_response, "finish_reason", None)
    finish_reason_name = getattr(finish_reason, "name", None) if finish_reason is not None else None
    if finish_reason_name != "STOP" and finish_reason != "STOP":
        return None

    has_text = any(getattr(part, "text", None) for part in content.parts)
    has_function_call = any(getattr(part, "function_call", None) for part in content.parts)
    if content.role != "model" or not has_text or has_function_call:
        return None

    invocation_context = getattr(callback_context, "_invocation_context", None)
    if invocation_context is not None:
        try:
            invocation_context.end_invocation = True
        except AttributeError:
            logger.debug("_stop_on_terminal_text: no se pudo fijar end_invocation")
    return None


def after_model(callback_context: CallbackContext, llm_response: LlmResponse):
    """Registra LLM_RESPONSE en BigQuery y aplica el guard de terminación."""
    try:
        _run_async(plugin.after_model_callback(
            callback_context=callback_context,
            llm_response=llm_response,
        ))
        logging.info("[BQ_PLUGIN] LLM_RESPONSE enviado a BigQuery")
    except Exception as e:
        logging.warning(f"[BQ_PLUGIN] after_model error: {e}")

    return _stop_on_terminal_text(callback_context, llm_response)


# ─── 5. Agentes ───────────────────────────────────────────────────────────────
# search_agent: SOLO tiene google_search, sin restricciones — puede hacer
# tantas búsquedas como necesite el skill (mínimo ~9 efemérides). Separarlo
# evita el bypass_multi_tools_limit, que limitaba cuántas búsquedas hacía
# el modelo al combinar Google Search con otro tool en el mismo agente.
search_agent = Agent(
    name="search_agent",
    model="gemini-3.1-flash-lite",
    description="Busca efemérides en la web siguiendo el skill de cobertura.",
    instruction=(
        efemerides_skill.instructions
        + "\n\nEn esta llamada específica, devuelve al menos 4-5 "
        "efemérides distintas y concretas (con fecha exacta) para la "
        "categoría y el mes/tema que te pidan — no menos."
    ),
    tools=[google_search],
)

root_agent = Agent(
    name="efemerides_agent",
    model="gemini-3.1-flash-lite",
    description="Un agente especializado en buscar efemérides de cualquier tema.",
    instruction=(
        "Para cualquier pedido de efemérides, llama a la tool `search_agent` "
        "TRES veces por separado (nunca una sola vez para todo):\n"
        "  1. Pidiéndole específicamente efemérides NACIONALES DE COLOMBIA "
        "del mes/tema solicitado.\n"
        "  2. Pidiéndole específicamente efemérides INTERNACIONALES del "
        "mes/tema solicitado.\n"
        "  3. Pidiéndole específicamente efemérides de INDUSTRIA/tecnología "
        "(o del tema pedido) del mes/tema solicitado.\n"
        "Junta los tres resultados, clasifica cada uno en su categoría "
        "correspondiente, y NO respondas hasta haber hecho las tres "
        "llamadas.\n\n"
        + _GENERATIVE_UI_INSTRUCTION
    ),
    tools=[
        AgentTool(agent=search_agent),
        AGUIToolset(),
    ],
    before_model_callback=before_model,
    after_model_callback=after_model,
)

# ─── 6. App ───────────────────────────────────────────────────────────────────
app_adk = App(
    name="efemerides_app",
    root_agent=root_agent,
    plugins=[plugin],
)

# ─── 7. ADKAgent ──────────────────────────────────────────────────────────────
adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="efemerides_app",
    user_id="user_efemerides",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

# ─── 8. FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)