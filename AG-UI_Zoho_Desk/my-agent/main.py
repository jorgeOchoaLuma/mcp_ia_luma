"""
Zoho Desk Ticket Operations — agente AG-UI + MCP remoto (Streamable HTTP).
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from gcp_credentials import setup_gcp_credentials

setup_gcp_credentials(base_dir=Path(__file__).resolve().parent)

if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1", "YES"):
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from zoho_auth import get_access_token, mcp_auth_headers

log = logging.getLogger(__name__)

MCP_KEY = os.getenv("ZOHO_DESK_MCP_KEY", "225c24a933bdd2eeebffab1e38742b72")
MCP_HOST = os.getenv(
    "ZOHO_DESK_MCP_HOST",
    "https://desk-ticket-operations-919104689.zohomcp.com",
)
ZOHO_DESK_MCP_URL = os.getenv(
    "ZOHO_DESK_MCP_URL",
    f"{MCP_HOST}/mcp/message?key={MCP_KEY}",
)

_mcp_headers: dict[str, str] = {}
try:
    _mcp_headers = mcp_auth_headers()
    log.info("Zoho OAuth OK para MCP Desk")
except Exception as exc:
    log.error("Zoho OAuth no configurado — MCP Desk fallará: %s", exc)

agent = LlmAgent(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    name="zoho_desk_agent",
    description="Asistente de operaciones de tickets en Zoho Desk.",
    instruction="""
Eres un asistente experto en Zoho Desk. Tienes herramientas MCP reales — ÚSALAS siempre.

## Herramientas disponibles (nombres exactos)
- getTickets / listOfTickets — listar tickets (limit, filtros)
- searchTickets — buscar tickets (estado, fechas, campos)
- getTicket — un ticket por ID
- createTicket / updateTicket — crear o actualizar
- createTicketComment / sendReply — comentarios y respuestas email
- getTicketComments / getTicketConversations / getThreads / getThread
- getDepartments / getOrganizations / getAccessibleOrganizations
- doSearch — búsqueda global en módulos

## Ejemplos de uso
- "Tickets abiertos de hoy" → searchTickets o getTickets con status Open y fecha de hoy (YYYY-MM-DD).
- "Detalle ticket #123" → getTicket
- "Comentar ticket" → createTicketComment

## Reglas CRÍTICAS
1. NUNCA escribas código Python ni pseudocódigo. Llama la herramienta MCP directamente.
2. NUNCA inventes nombres como zoho_desk_get_tickets — usa getTickets o searchTickets.
3. Si una tool falla, muestra el error y sugiere el siguiente paso.
4. Responde en español, claro y profesional.
5. No expongas tokens ni URLs internas.
""",
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=ZOHO_DESK_MCP_URL,
                headers=_mcp_headers or None,
                timeout=30.0,
                sse_read_timeout=120.0,
            ),
            errlog=None,
        )
    ],
)

adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="zoho_desk_app",
    user_id="desk_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(title="Zoho Desk MCP Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_adk_fastapi_endpoint(app, adk_agent, path="/")


@app.get("/health")
def health():
    oauth_ok = False
    oauth_error = None
    try:
        get_access_token()
        oauth_ok = True
    except Exception as exc:
        oauth_error = str(exc)

    return {
        "status": "ok" if oauth_ok else "degraded",
        "agent": "zoho_desk_agent",
        "mcp_url": ZOHO_DESK_MCP_URL.split("?")[0] + "?key=...",
        "zoho_oauth": oauth_ok,
        "zoho_oauth_error": oauth_error,
        "vertex_ai": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1", "YES"),
        "project_id": os.environ.get("GOOGLE_CLOUD_PROJECT"),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
