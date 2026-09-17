
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
uv add ag-ui-adk google-adk uvicorn fastapi google-cloud-bigquery google-cloud-storage google-adk[bigquery] google-cloud-bigquery-storage pyarrow

uv add "google-adk[mcp]" mcp


### 3️⃣ Frontend

```bash
# En otra terminal
cd ..
npx create-next-app@latest my-copilot-app 
cd my-copilot-app

# Instalar CopilotKit

npm install @copilotkit/react-ui @copilotkit/react-core @copilotkit/runtime @ag-ui/client zod
npx shadcn@latest add popover command button



# Copiar archivos frontend en sus ubicaciones
# Ejecutar
npm run dev