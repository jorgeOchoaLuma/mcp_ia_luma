"""
Agente de Proyectos Zoho — versión completa para AG_UI_Unified_Project.
Incluye:
  - MCP Zoho Projects (crear proyectos, tareas, etc.)
  - Tools propias (get_project_groups, get_project_templates)
  - AGUIToolset → groupPicker, templatePicker, projectSummary (Human-in-the-Loop)
  - BigQuery Analytics Plugin
  - ResumabilityConfig (requerido para Human-in-the-Loop)
"""

import os
import json
import time
from typing import Optional

import httpx
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App, ResumabilityConfig
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)

from ag_ui_adk import ADKAgent, AGUIToolset

load_dotenv()

# ─── Constantes Zoho ──────────────────────────────────────────────────────────
PORTAL_ID = "854075653"
ZOHO_BASE_URL = f"https://projectsapi.zoho.com/api/v3/portal/{PORTAL_ID}"
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.com"

ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
ZOHO_CLIENT_ID     = os.environ.get("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")

# ─── Config BQ ────────────────────────────────────────────────────────────────
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "adk_agent_analytics")
BQ_LOCATION   = os.environ.get("BQ_LOCATION", "US")

# ─── Token cache ──────────────────────────────────────────────────────────────
_token_cache: dict = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    """Renueva el access token de Zoho automáticamente con el refresh token."""
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    resp = httpx.post(
        f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token",
        data={
            "refresh_token": ZOHO_REFRESH_TOKEN,
            "client_id":     ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "grant_type":    "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise ValueError(f"Error al obtener access_token de Zoho: {data}")
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
    return _token_cache["access_token"]


def _headers() -> dict:
    return {
        "Authorization": f"Zoho-oauthtoken {_get_access_token()}",
        "Content-Type": "application/json",
    }


def _get(url: str, params: dict | None = None) -> dict:
    resp = httpx.get(url, headers=_headers(), params=params, timeout=30)
    if resp.status_code >= 400:
        return {"error": True, "status_code": resp.status_code, "body": resp.text, "url": str(resp.request.url)}
    return resp.json()


# ─── Tools propias ────────────────────────────────────────────────────────────

def get_project_groups() -> dict:
    """Lista los grupos de proyectos del portal."""
    url = f"{ZOHO_BASE_URL}/project-groups"
    result = _get(url)
    if result.get("error"):
        return result
    groups = [
        {
            "id": g["id"],
            "name": g["name"],
            "associated_projects": g.get("associated_projects", "0"),
        }
        for g in result.get("project-groups", [])
    ]
    return {"groups": groups}


def get_project_templates() -> dict:
    """Devuelve las plantillas de proyecto configuradas manualmente."""
    return {
        "templates": [
            {"id": "2311121000005241375", "name": "PAC_plantilla proyectos AC"},
            {"id": "2311121000004520029", "name": "PBC_plantilla proyectos BC"},
            {"id": "2311121000004458166", "name": "GPO_plantilla"},
            {"id": "2311121000002440013", "name": "Proyecto Hostbill"},
        ]
    }


# ─── Callbacks ────────────────────────────────────────────────────────────────

def _fix_zoho_create_project_payload(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    if tool.name != "ZohoProjects_create_a_project":
        return None

    body = args.get("body", {})
    path_variables = args.get("path_variables", {})
    path_variables["portal_id"] = PORTAL_ID
    args.pop("portal_id", None)

    if "group_id" in args:
        body["project_group"] = {"id": str(args.pop("group_id"))}
    elif "group_id" in body:
        body["project_group"] = {"id": str(body.pop("group_id"))}

    if "template_id" in args:
        body["copy_from"] = str(args.pop("template_id"))
    elif "template_id" in body:
        body["copy_from"] = str(body.pop("template_id"))

    body.pop("owner", None)
    args["body"] = body
    args["path_variables"] = path_variables
    return None


def _log_zoho_response(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    print(f"TOOL NAME REAL: {tool.name}")
    print("=== RESPUESTA DE ZOHO ===")
    print(json.dumps(tool_response, indent=2, default=str, ensure_ascii=False))

    if isinstance(tool_response, dict) and "structuredContent" in tool_response:
        data = tool_response.get("structuredContent", {}).get("data")
        if data is not None:
            return {"status": "success", "result": data}
        return {"status": "success" if not tool_response.get("isError") else "error"}
    return None


# ─── LLM Agent ────────────────────────────────────────────────────────────────

_agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="agent_projects",
    description="Asistente que gestiona proyectos y tareas en Zoho Projects",
    instruction=f"""
Eres un asistente que gestiona proyectos y tareas del portal lumasas (id {PORTAL_ID}) en Zoho Projects.
Formato de fechas para start_date/end_date: dd/mm/yyyy hh:mm aaa (ej: 07/08/2026 09:00 AM).

## Herramientas disponibles
- `get_project_groups`: lista los grupos de proyectos vigentes (nombre → id). Tool propia.
- `get_project_templates`: lista los proyectos marcados como plantilla (nombre → id). Tool propia.
- Tools del MCP de Zoho Projects:
  - `get_projects_list`: lista los proyectos del portal (para resolver project_id por nombre).
  - `get_project_detail`: detalle de un proyecto específico dado su project_id.
  - `create_a_project`: crea un proyecto nuevo.
  - `create_task_list`: crea una lista de tareas dentro de un proyecto (task list / tasklist).
  - `create_a_task`: crea una tarea dentro de un proyecto (y opcionalmente dentro de un tasklist).
  - `get_project_user_details`: obtiene detalles de un usuario del proyecto (para asignar tareas).

## Flujo OBLIGATORIO para crear un proyecto (sigue este orden EXACTO, un paso a la vez)

Paso 1 — Estructura:
Pregunta SOLO si el usuario quiere Opción A (grupo) u Opción B (grupo + plantilla).
No hagas ninguna otra pregunta ni llames ninguna tool en este mismo turno.
Espera la respuesta del usuario antes de continuar.

Paso 2 — Grupo:
Una vez tengas la respuesta A/B, llama `get_project_groups` e invoca INMEDIATAMENTE
el componente `groupPicker` con el resultado.
NUNCA escribas los nombres de los grupos como texto en tu respuesta, ni siquiera como
confirmación o resumen. La única forma válida de mostrarlos es a través de `groupPicker`.
Espera a que el usuario seleccione un grupo mediante el componente. NUNCA asumas,
infieras, adivines o reutilices un group_id de un intento anterior.

Paso 3 — Plantilla (solo si eligió Opción B):
Llama `get_project_templates` e invoca `templatePicker`. Mismas reglas que el grupo.

Paso 4 — Nombre y fechas:
Pide el nombre del proyecto (obligatorio, siempre debes tenerlo antes de crear).
NO preguntes por start_date, end_date ni owner — estos tienen valores por defecto
y solo deben pedirse si el usuario los menciona espontáneamente.

Paso 5 — Defaults:
- start_date: si el usuario no la da, NO lo incluyas en el payload.
- end_date: si el usuario no la da, NO lo incluyas en el payload.
- owner: si el usuario no lo da, NO lo incluyas en el payload.

Paso 6 — Crear:
Con nombre + group_id (+ template_id si aplica), llama la tool del MCP que crea proyectos.
Al confirmar la creación exitosa, usa el componente `projectSummary` con los datos del
proyecto creado (NO confirmes solo en texto).

## Flujo para crear tareas
1. Si no tienes project_id, resuélvelo con `get_projects_list` o `get_project_detail`.
2. Si el usuario quiere organizar la tarea en una lista específica y esta no existe, créala primero.
3. Si necesitas asignar la tarea a alguien, resuelve el usuario con `get_project_user_details`.
4. Llama a `create_a_task` con project_id, tasklist_id (si aplica), nombre y fechas.

## Reglas generales
- Nunca pidas IDs al usuario: se resuelven con tools.
- Cuando el usuario deba elegir entre varias opciones (grupos, plantillas), usa SIEMPRE el
  componente correspondiente (`groupPicker`, `templatePicker`), nunca texto plano.
- Nunca combines dos preguntas distintas en el mismo turno.
- Nunca asumas un group_id/template_id sin una selección explícita del usuario en este flujo.
""",
    tools=[
        FunctionTool(get_project_groups),
        FunctionTool(get_project_templates),
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://projects-913695724.zohomcp.com/mcp/message?key=d1cdc7d95ae0aa5252bf55db36915868",
            )
        ),
        AGUIToolset(),
    ],
    before_tool_callback=_fix_zoho_create_project_payload,
    after_tool_callback=_log_zoho_response,
)

# ─── BigQuery Plugin ──────────────────────────────────────────────────────────
_bq_config = BigQueryLoggerConfig(
    enabled=True,
    table_id="agent_events",
)
_bq_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=GOOGLE_CLOUD_PROJECT,
    dataset_id=BQ_DATASET_ID,
    table_id=_bq_config.table_id,
    config=_bq_config,
    location=BQ_LOCATION,
)

# ─── App (ResumabilityConfig OBLIGATORIO para Human-in-the-Loop) ─────────────
_app_zoho = App(
    name="app_projects",
    root_agent=_agent,
    plugins=[_bq_plugin],
    resumability_config=ResumabilityConfig(is_resumable=True),
)

# ─── ADKAgent exportado ───────────────────────────────────────────────────────
adk_agent = ADKAgent.from_app(
    _app_zoho,
    user_id="projects_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)
