# AG-UI Zoho Desk

React (Next.js + CopilotKit) + backend Python (Google ADK) conectado al MCP de **Zoho Desk Ticket Operations**.

## Estructura

```
AG-UI_Zoho_Desk/
├── my-agent/          # Backend FastAPI + ADK + MCP
└── my-copilot-app/  # Frontend React (Next.js)
```

## Inicio rápido

### 1. Backend

```bash
cd my-agent
cp .env.example .env
# GOOGLE_API_KEY=...
uv sync
uv run main.py
```

### 2. Frontend

```bash
cd my-copilot-app
npm install
cp .env.example .env.local
npm run dev
```

Abre **http://localhost:3000**

## MCP

Endpoint configurado en `ZOHO_DESK_MCP_URL`:

`https://desk-ticket-operations-919104689.zohomcp.com/mcp/225c24a933bdd2eeebffab1e38742b72/message`

## Coolify

- Backend: `PORT=8000`, env de Gemini + `ZOHO_DESK_MCP_URL`
- Frontend: `BACKEND_URL=http://backend:8000`
