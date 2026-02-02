# ADK with AG-UI

### Estructura Final del Proyecto
proyecto-licitaciones/
│
├── my-agent/                    # Backend
│   ├── .venv/                   # Entorno virtual (creado por UV)
│   ├── main.py                  # Servidor FastAPI + ADK
│   ├── licitaciones.py          # MCP Server
│   ├── .env                     # API Key
│   └── pyproject.toml           # Dependencias (gestionado por UV)
│
└── my-copilot-app/              # Frontend
    ├── app/
    │   ├── api/copilotkit/
    │   │   └── route.ts
    │   ├── layout.tsx
    │   └── page.tsx
    └── package.json

### Instalacion de UV

    PASO 1: Instalar UV
    - Windows:
         powershellpowershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    - Otros sistemas:
        bashcurl -LsSf https://astral.sh/uv/install.sh | sh
        
    - Verifica la instalación:
    uv --version

### Creaacion ambiente virtual

    uv init my-agent    # Crea todo automáticamente
    uv add paquetes     # Instala dependencias
    uv run main.py      # Ejecuta tu código

## Pasos crear el ambiente virtual
    - En la carpeta C:\AG_UI_agent_mcp_licitaciones
    se ejecuta **uv init my-agent** y crea auromaticamente la carpeta my-agente y el ambiente virtual
    uv init my-agent
    - cd my-agent
    uv add ag-ui-adk google-adk uvicorn fastapi
    - uv run main.py

### Create your frontend

    - npx create-next-app@latest my-copilot-app
    cd my-copilot-app

    - npm install @copilotkit/react-ui @copilotkit/react-core @copilotkit/runtime @ag-ui/client

    - C:\AG_UI_agent_mcp_licitaciones\my-copilot-app> npm run dev

    ### Creacion  Archivo .env (recomendado)
    bash
    - Crea archivo .env en el directorio my-agent/
    echo "GOOGLE_API_KEY=tu_api_key_real" > .env


###  Comandos Útiles de UV

    # Ver dependencias instaladas
uv pip list

#### Ejecutar cualquier script Python
uv run python script.py

#### Ejecutar el servidor
uv run main.py

#### Agregar nueva dependencia
uv add nombre-paquete

#### Actualizar dependencia
uv add --upgrade nombre-paquete

#### Remover dependencia
uv remove nombre-paquete

#### Sincronizar dependencias del pyproject.toml
uv sync


## DEPLOY - Google ADK

## Arquitectura

┌─────────────────────────────────────────┐
│          USUARIO (Navegador)            │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTPS
                  │
┌─────────────────▼───────────────────────┐
│    Frontend (Vercel / Cloud Run)        │
│    - Next.js                            │
│    - CopilotKit UI                      │
└─────────────────┬───────────────────────┘
                  │
                  │ API Calls
                  │
┌─────────────────▼───────────────────────┐
│    Backend (Google Cloud Run)                │
│    - FastAPI                            │
│    - Google ADK                         │
│    - MCP Server (licitaciones.py)       │
│    - Escala automáticamente             │
└─────────────────┬───────────────────────┘
                  │
                  │ LLM
                  │
┌─────────────────▼───────────────────────┐
│                       │
│    (Vertex AI o AI Studio)              │
└─────────────────────────────────────────┘

### El diagrama muestra tres capas principales:

 **Frontend Layer (CopilotKit)**

Provider y Sidebar para la interfaz de chat
Hook useCoAgent para sincronización de estado
Generative UI para renderizado dinámico

 **AG-UI Protocol Layer**

Protocolo de comunicación bidireccional
Streaming en tiempo real
Sincronización de estado y herramientas

 **Backend Layer (ADK Agent)**

Framework ADK de Google
Modelo Gemini (LLM)
Herramientas personalizadas y FastAPI


