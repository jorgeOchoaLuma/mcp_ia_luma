from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset
from google.adk.agents.llm_agent import LlmAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools import url_context
from google.genai import types
from typing import Optional

import os

import httpx
from dotenv import load_dotenv
from google.adk.agents import LlmAgent

import json
from typing import Optional

load_dotenv(override=True)  # carga variables desde el archivo .env (mismo directorio que este archivo)
from google.adk.tools import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

PORTAL_ID = "854075653"  # confirma que este es el ID real de tu portal

# MIGRADO A V3: /restapi/ -> /api/v3/  (la API vieja ya no funciona, deprecada desde 31/12/2025)
ZOHO_BASE_URL = f"https://projectsapi.zoho.com/api/v3/portal/{PORTAL_ID}"
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.com"  # ajusta a .eu / .in / .com.au si tu portal es de otra región

ZOHO_REFRESH_TOKEN = os.environ["ZOHO_REFRESH_TOKEN"]
ZOHO_CLIENT_ID = os.environ["ZOHO_CLIENT_ID"]
ZOHO_CLIENT_SECRET = os.environ["ZOHO_CLIENT_SECRET"]

# --- Config BigQuery Agent Analytics ---
GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "adk_agent_analytics")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")

_token_cache = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    """Los access tokens de Zoho duran 1 hora. Los cacheamos y renovamos
    automáticamente con el refresh token cuando falta poco para expirar."""
    import time

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    resp = httpx.post(
        f"{ZOHO_ACCOUNTS_URL}/oauth/v2/token",
        data={
            "refresh_token": ZOHO_REFRESH_TOKEN,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token",
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
    """Wrapper que SIEMPRE devuelve el cuerpo del error si algo falla,
    en vez de perderlo con raise_for_status()."""
    resp = httpx.get(url, headers=_headers(), params=params, timeout=30)
    if resp.status_code >= 400:
        return {"error": True, "status_code": resp.status_code, "body": resp.text, "url": str(resp.request.url)}
    return resp.json()


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
    """Devuelve las plantillas de proyecto configuradas manualmente.
    NOTA: La API v3 de Zoho Projects no tiene un endpoint público para listar
    plantillas de proyecto. Por lo tanto, debes agregar manualmente los IDs
    de tus plantillas aquí."""
    return {
        "templates": [
            {"id": "2311121000005241375", "name": "PAC_plantilla proyectos AC"},
            {"id": "2311121000004520029", "name": "PBC_plantilla proyectos BC"},
            {"id": "2311121000004458166", "name": "GPO_plantilla"},
            {"id": "2311121000002440013", "name": "Proyecto Hostbill"}
        ]
    }

def fix_zoho_create_project_payload(
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

    # Ya NO seteamos owner aquí
    body.pop("owner", None)

    args["body"] = body
    args["path_variables"] = path_variables
    return None

def log_zoho_response(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    print(f"TOOL NAME REAL: {tool.name}")
    print("=== RESPUESTA DE ZOHO ===")
    print(json.dumps(tool_response, indent=2, default=str, ensure_ascii=False))

    # Si viene envuelto en el formato MCP (content/structuredContent/isError),
    # lo aplanamos para que ag_ui_adk no se atore con la estructura anidada.
    if isinstance(tool_response, dict) and "structuredContent" in tool_response:
        data = tool_response.get("structuredContent", {}).get("data")
        if data is not None:
            return {"status": "success", "result": data}
        return {"status": "success" if not tool_response.get("isError") else "error"}

    return None

agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="agent_projects",
    description="Asistente que gestiona proyectos y tareas en Zoho Projects",
    instruction=f"""
Eres un asistente que gestiona proyectos y tareas del portal lumasas (id {PORTAL_ID}) en Zoho Projects.
Formato de fechas para start_date/end_date: dd/mm/yyyy hh:mm aaa (ej: 07/08/2026 09:00 AM).

## Herramientas disponibles
- `get_project_groups`: lista los grupos de proyectos vigentes (nombre -> id). Tool propia.
- `get_project_templates`: lista los proyectos marcados como plantilla (nombre -> id). Tool propia.
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
Si no puedes invocar el componente, no muestres la lista de ninguna forma — indica que
hubo un problema y vuelve a intentarlo.
Espera a que el usuario seleccione un grupo mediante el componente. NUNCA asumas,
infieras, adivines o reutilices un group_id de un intento anterior o de la conversación
sin que exista una selección explícita del usuario en `groupPicker` en ESTE flujo.

Paso 3 — Plantilla (solo si eligió Opción B):
Llama `get_project_templates` e invoca `templatePicker`. Mismas reglas que el grupo:
nunca en texto, nunca adivinada.

Paso 4 — Nombre y fechas:
Pide el nombre del proyecto (obligatorio, siempre debes tenerlo antes de crear).
NO preguntes por start_date, end_date ni owner — estos tienen valores por defecto
(ver Paso 5) y solo deben pedirse si el usuario los menciona espontáneamente o
pide personalizarlos explícitamente.

Paso 5 — Defaults (no preguntar, solo informar al confirmar):
- start_date: si el usuario no la da, NO lo incluyas en el payload.
- end_date: si el usuario no la da, NO lo incluyas en el payload.
- owner: si el usuario no lo da, NO lo incluyas en el payload y NO menciones el
  propietario en el resumen de confirmación — omite esa línea por completo en vez
  de decir "sin asignar".
Si aplicaste algún default, menciónalo en el resumen final (`projectSummary`), no antes.

Paso 6 — Crear:
Con nombre + group_id (+ template_id si aplica), llama la tool del MCP que crea proyectos.
Al confirmar la creación exitosa, usa el componente `projectSummary` con los datos del
proyecto creado (NO confirmes solo en texto).

## Flujo para crear tareas
1. Si no tienes project_id, resuélvelo con `get_projects_list` (búscalo por nombre) o `get_project_detail` si ya tienes el id.
2. Si el usuario quiere organizar la tarea en una lista específica y esta no existe, créala primero con `create_a_task` o `create_task_list`.
3. Si necesitas asignar la tarea a alguien, resuelve el usuario con `get_project_user_details`.
4. Llama a `create_a_task` con project_id, tasklist_id (si aplica), nombre y fechas.

## Reglas generales
- Nunca pidas IDs al usuario: se resuelven con tools.
- Si un grupo o plantilla mencionado no existe en el listado actual, informa cuáles sí existen.
- Cuando el usuario deba elegir entre varias opciones (grupos, plantillas), usa SIEMPRE el
  componente correspondiente (`groupPicker`, `templatePicker`), nunca texto plano.
- Nunca combines dos preguntas distintas (ej. estructura A/B + grupo) en el mismo turno.
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
        # 🪁 Expone al agente los componentes registrados en el frontend
        # con useComponent(): groupPicker, templatePicker, projectSummary.
        # Sin esto el agente no puede invocarlos (ver L3).
        AGUIToolset(),
    ],
    before_tool_callback=fix_zoho_create_project_payload,
    after_tool_callback=log_zoho_response,
)

# --- BigQuery Agent Analytics Plugin ---
# Requiere: google-adk[bigquery-analytics]>=1.21.0
# Variables de entorno usadas: GOOGLE_CLOUD_PROJECT, BQ_DATASET_ID, BQ_LOCATION
bq_config = BigQueryLoggerConfig(
    enabled=True,
    table_id="agent_events",  # se crea automáticamente si no existe
)

bq_analytics_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=GOOGLE_CLOUD_PROJECT,
    dataset_id=BQ_DATASET_ID,
    table_id=bq_config.table_id,
    config=bq_config,
    location=BQ_LOCATION,
)

# App envuelve el root_agent + plugins (patrón requerido por el plugin)
# resumability_config=True es OBLIGATORIO porque AGUIToolset() expone tools
# del cliente (groupPicker, templatePicker, projectSummary) como long-running
# tools: el agente pausa su ejecución esperando la respuesta del frontend y
# ADK necesita poder persistir/reanudar ese estado. Sin esto, el run se
# cancela ("Root node ... was cancelled") en cuanto el usuario interactúa
# con un componente.
app_zoho = App(
    name="app_projects",
    root_agent=agent,
    plugins=[bq_analytics_plugin],
    resumability_config=ResumabilityConfig(is_resumable=True),
)

# ADKAgent se construye a partir del App (así el plugin queda enganchado al runner)
adk_agent = ADKAgent.from_app(
    app_zoho,
    user_id="projects_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8001)