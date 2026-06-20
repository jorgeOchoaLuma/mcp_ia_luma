# Zoho Desk Agent (Backend)

Agente ADK conectado al MCP remoto de Zoho Desk vía Streamable HTTP.

## Setup

```bash
cd my-agent
cp .env.example .env
# Editar GOOGLE_API_KEY (o Vertex AI)

uv sync
uv run main.py
```

Servidor: `http://localhost:8000` — health: `GET /health`

## MCP

Variable `ZOHO_DESK_MCP_URL` apunta al endpoint Zoho MCP:

```
https://desk-ticket-operations-919104689.zohomcp.com/mcp/225c24a933bdd2eeebffab1e38742b72/message
```
