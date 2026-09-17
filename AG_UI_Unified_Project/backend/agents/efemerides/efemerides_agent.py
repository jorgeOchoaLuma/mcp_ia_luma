"""
Agente de Efemérides — módulo para AG_UI_Unified_Project.
Busca efemérides (nacionales, internacionales, de industria) usando google_search
y las muestra mediante el componente generativo 'efemerides_card' del frontend.
"""

import os
import asyncio
import logging

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

from ag_ui_adk import ADKAgent, AGUIToolset

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
PROJECT_ID    = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "agente_analytics_db")

# ─── 1. BigQuery Plugin ────────────────────────────────────────────────────────
_bq_plugin = BigQueryAgentAnalyticsPlugin(
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

# ─── 2. Skill de efemérides ───────────────────────────────────────────────────
_SKILL_PATH = os.path.join(
    os.path.dirname(__file__), "skills", "efemerides-searcher"
)
_efemerides_skill = load_skill_from_dir(_SKILL_PATH)

# ─── 3. Instrucción de Generative UI ──────────────────────────────────────────
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

# ─── 4. Helper async ──────────────────────────────────────────────────────────
def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except Exception as e:
        logger.warning(f"[EFEMERIDES BQ] _run_async error: {e}")

# ─── 5. Callbacks ─────────────────────────────────────────────────────────────
def _before_model(callback_context: CallbackContext, llm_request: LlmRequest):
    try:
        _run_async(_bq_plugin.before_model_callback(
            callback_context=callback_context,
            llm_request=llm_request,
        ))
    except Exception as e:
        logger.warning(f"[EFEMERIDES BQ] before_model error: {e}")
    return None


def _stop_on_terminal_text(callback_context: CallbackContext, llm_response: LlmResponse):
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
            pass
    return None


def _after_model(callback_context: CallbackContext, llm_response: LlmResponse):
    try:
        _run_async(_bq_plugin.after_model_callback(
            callback_context=callback_context,
            llm_response=llm_response,
        ))
    except Exception as e:
        logger.warning(f"[EFEMERIDES BQ] after_model error: {e}")
    return _stop_on_terminal_text(callback_context, llm_response)

# ─── 6. Agentes ───────────────────────────────────────────────────────────────
_search_agent = Agent(
    name="efemerides_search_agent",
    model="gemini-3.1-flash-lite",
    description="Busca efemérides en la web siguiendo el skill de cobertura.",
    instruction=(
        _efemerides_skill.instructions
        + "\n\nEn esta llamada específica, devuelve al menos 4-5 "
        "efemérides distintas y concretas (con fecha exacta) para la "
        "categoría y el mes/tema que te pidan — no menos."
    ),
    tools=[google_search],
)

_root_agent = Agent(
    name="efemerides_agent",
    model="gemini-3.7-flash",
    description="Agente especializado en buscar efemérides de cualquier tema.",
    instruction=(
        "Para cualquier pedido de efemérides, llama a la tool `efemerides_search_agent` "
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
        AgentTool(agent=_search_agent),
        AGUIToolset(),
    ],
    before_model_callback=_before_model,
    after_model_callback=_after_model,
)

# ─── 7. App ───────────────────────────────────────────────────────────────────
_app_adk = App(
    name="efemerides_app",
    root_agent=_root_agent,
    plugins=[_bq_plugin],
)

adk_agent = ADKAgent.from_app(
    _app_adk,
    user_id="user_efemerides",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)
