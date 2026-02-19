#  Sistema de Gestión de Licitaciones con IA
# ADK with AG-UI

**Google ADK + CopilotKit + FastMCP + UV**

Sistema completo para gestionar licitaciones públicas con un agente de IA conversacional.
https://docs.copilotkit.ai/integrations/adk/quickstart?agent=bring-your-own

---

## 📦 ¿Qué incluye?

✅ **Backend Python** con Google ADK + FastAPI + UV  
✅ **Frontend Next.js** con CopilotKit UI  
✅ **13 herramientas MCP** para gestión de licitaciones  
✅ **Interfaz de chat** interactiva  
✅ **Análisis inteligente** con Gemini 3.0  

---

## 📋 Archivos Incluidos

### 📚 DOCUMENTACIÓN
- **GUIA_INSTALACION_UV.md** ⭐ Guía completa paso a paso
- **RESUMEN_ARCHIVOS.txt** - Mapa de archivos

### 🐍 BACKEND
- **backend_main_updated.py** → Renombrar a `main.py`
- **licitaciones.py** → MCP Server
- **env_example.txt** → Configurar API Key

### ⚛️ FRONTEND
- **frontend_route.ts** → `app/api/copilotkit/route.ts`
- **frontend_layout.tsx** → `app/layout.tsx`
- **frontend_page.tsx** → `app/page.tsx`
- **frontend_package.json** → Referencia

### 🛠️ OTROS
- **gitignore.txt** → Renombrar a `.gitignore`

---

## 🚀 Inicio Rápido

### 1️⃣ Instalar UV

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Otros:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2️⃣ Backend

```bash
# Inicializar proyecto (crea .venv automáticamente)
uv init my-agent
cd my-agent

# Instalar dependencias
uv add ag-ui-adk google-adk uvicorn fastapi

# Copiar archivos:
# - backend_main_updated.py → main.py
# - licitaciones.py → licitaciones.py

# Configurar API Key
export GOOGLE_API_KEY="tu_api_key"
# o crear .env:
echo "GOOGLE_API_KEY=tu_api_key" > .env

# Ejecutar
uv run main.py
```

### 3️⃣ Frontend

```bash
# En otra terminal
cd ..
npx create-next-app@latest my-copilot-app --typescript
cd my-copilot-app

# Instalar CopilotKit

npm install @copilotkit/react-ui @copilotkit/react-core @copilotkit/runtime @ag-ui/client

# Copiar archivos frontend en sus ubicaciones
# Ejecutar
npm run dev
```

### 4️⃣ Acceder

**http://localhost:3000**

---

## 📁 Estructura

```
proyecto/
├── my-agent/              # Backend
│   ├── .venv/            # Creado por UV automáticamente
│   ├── main.py
│   ├── licitaciones.py
│   ├── .env
│   └── pyproject.toml    # Gestionado por UV
│
└── my-copilot-app/       # Frontend
    ├── app/
    │   ├── api/copilotkit/route.ts
    │   ├── layout.tsx
    │   └── page.tsx
    └── package.json
```

---

## 💬 Funcionalidades

- 📋 Listar licitaciones
- 🔍 Ver detalles completos
- 💰 Consultar requisitos financieros
- 🎓 Revisar requisitos de experiencia
- 📄 Listar documentos requeridos
- 🤖 Generar resúmenes con IA
- 📧 Ver correos originales
- ⚙️ Analizar requisitos técnicos

---

## 🧪 Verificación

```bash
# Backend
curl http://localhost:8000/health

# Debe responder:
# {"status": "healthy", "agent": "licitaciones_assistant"}
```

---

## ⚡ ¿Por qué UV en vez de venv?

UV es **10-100x más rápido** que pip y gestiona entornos automáticamente:

| Tarea | venv + pip | UV |
|-------|------------|-----|
| Crear entorno | `python -m venv .venv` | `uv init` |
| Activar | `source .venv/bin/activate` | No necesario |
| Instalar | `pip install paquete` | `uv add paquete` |
| Ejecutar | `python main.py` | `uv run main.py` |

**Con UV no necesitas activar el entorno manualmente.**

---

## 🆘 Problemas Comunes

### "GOOGLE_API_KEY not set"
```bash
export GOOGLE_API_KEY="tu_clave"
# o
echo "GOOGLE_API_KEY=tu_clave" > .env
```

### "Module not found"
```bash
cd my-agent
uv add ag-ui-adk google-adk uvicorn fastapi
```

### "Cannot connect to backend"
→ Verifica que esté en puerto 8000

---

## 📝 Comandos Útiles

**UV (Backend):**
```bash
uv pip list              # Ver dependencias
uv run main.py           # Ejecutar servidor
uv add paquete           # Agregar dependencia
```

**npm (Frontend):**
```bash
npm run dev              # Desarrollo
npm run build            # Producción
```

---

## 📚 Recursos

- [UV Docs](https://docs.astral.sh/uv/)
- [CopilotKit](https://docs.copilotkit.ai/)
- [Google ADK](https://ai.google.dev/adk)

---

**Lee GUIA_INSTALACION_UV.md para instrucciones detalladas.** 🚀


Prerequisites
Before you begin, you'll need the following:

A Google Gemini API key
Node.js 20+
Python 3.9+
Your favorite package manager
Getting started
Choose your starting point

You can either start fresh with our starter template or integrate CopilotKit into your existing ADK agent.

Start from scratch

Get started quickly with our ready-to-go starter application.

Use an existing agent

I already have an ADK agent and want to add CopilotKit.

Initialize your agent project
If you don't already have a Python project set up, create one using uv:


uv init my-agent
cd my-agent
Install ADK with AG-UI
Add ADK with AG-UI support and uvicorn to your project:


uv add ag-ui-adk google-adk uvicorn fastapi
What is AG-UI?

AG-UI is an open protocol for frontend-agent communication. The ag-ui-adk package provides ADK integration that CopilotKit can connect to.

Configure your environment
Set your Google API key as an environment variable:


export GOOGLE_API_KEY=your_google_api_key
What about other models?

This example uses Gemini 2.5 Flash, but you can modify it to use any language model supported by ADK.

Expose your agent via AG-UI
Update your agent file to expose it as an AG-UI ASGI application:

main.py

from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent
agent = LlmAgent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="Be helpful and fun!"
)
adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="demo_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)
app = FastAPI()
add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
Create your frontend
CopilotKit works with any React-based frontend. We'll use Next.js for this example.


npx create-next-app@latest my-copilot-app
cd my-copilot-app
Install CopilotKit packages
npm
pnpm
yarn
bun

npm install @copilotkit/react-ui @copilotkit/react-core @copilotkit/runtime @ag-ui/client
Setup Copilot Runtime
Create an API route to connect CopilotKit to your ADK agent:

app/api/copilotkit/route.ts

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";
const serviceAdapter = new ExperimentalEmptyAdapter();
const runtime = new CopilotRuntime({
  agents: {
    my_agent: new HttpAgent({ url: "http://localhost:8000/" }),
  }
});
export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
Configure CopilotKit Provider
Wrap your application with the CopilotKit provider:

app/layout.tsx

import { CopilotKit } from "@copilotkit/react-core"; 
import "@copilotkit/react-ui/styles.css";
// ...
export default function RootLayout({ children }: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit" agent="my_agent">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
Add the chat interface
Add the CopilotSidebar component to your page:

app/page.tsx

import { CopilotSidebar } from "@copilotkit/react-ui"; 
export default function Page() {
  return (
    <main>
      <h1>Your App</h1>
      <CopilotSidebar />
    </main>
  );
}
Start your agent
From your agent directory, start the agent server:


uv run main.py
Your agent will be available at http://localhost:8000.

Start your UI
In a separate terminal, navigate to your frontend directory and start the development server:

npm
pnpm
yarn
bun

cd my-copilot-app
npm run dev
