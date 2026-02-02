# 🚀 GUÍA DE DEPLOY A GOOGLE CLOUD RUN

Deploy de tu agente de licitaciones con Google ADK en Cloud Run.

---

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener:

1. ✅ **Cuenta de Google Cloud** con facturación habilitada
2. ✅ **gcloud CLI instalado** - [Instalar aquí](https://cloud.google.com/sdk/docs/install)
3. ✅ **Proyecto funcionando localmente** (backend + frontend)
4. ✅ **UV instalado** (ya lo tienes)

---

## 🔧 PASO 1: Configurar Google Cloud

### 1.1 Instalar Google Cloud CLI

**Windows:**
```powershell
# Descarga el instalador
https://cloud.google.com/sdk/docs/install

# O con Chocolatey
choco install gcloudsdk
```

**Otros sistemas:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 1.2 Autenticarse

```bash
# Iniciar sesión
gcloud auth login

# Configurar proyecto
gcloud config set project TU_PROJECT_ID

# Ver configuración actual
gcloud config list
```

### 1.3 Habilitar APIs Necesarias

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

Esto habilita:
- **Cloud Run** - Para ejecutar tu agente
- **Artifact Registry** - Para almacenar imágenes Docker
- **Cloud Build** - Para construir contenedores
- **Secret Manager** - Para almacenar API keys de forma segura

---

## 🔑 PASO 2: Configurar API Key de Google como Secret

En lugar de incluir tu API Key en el código, usa Secret Manager:

```bash
# Crear el secret
echo -n "tu_google_api_key_real" | \
  gcloud secrets create GOOGLE_API_KEY \
  --data-file=-

# Verificar que se creó
gcloud secrets list
```

---

## 📦 PASO 3: Preparar el Proyecto para Deploy

### 3.1 Estructura del Proyecto

Tu proyecto debe tener esta estructura:

```
my-agent/
├── main.py              # Tu servidor FastAPI
├── licitaciones.py      # MCP Server
├── pyproject.toml       # Gestionado por UV
├── Dockerfile           # Para Cloud Run (crear)
└── .dockerignore        # Archivos a ignorar (crear)
```

### 3.2 Crear Dockerfile

Crea un archivo `Dockerfile` en el directorio `my-agent/`:

```dockerfile
# Usar imagen oficial de Python
FROM python:3.11-slim

# Copiar UV desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Instalar dependencias del sistema si son necesarias
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . .

# Instalar dependencias con UV
RUN uv sync

# Exponer el puerto que Cloud Run espera
EXPOSE 8080

# Comando para ejecutar la aplicación
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Nota:** Cloud Run espera que tu aplicación escuche en el puerto definido por la variable de entorno `PORT` (por defecto 8080).

### 3.3 Modificar main.py

Actualiza tu `main.py` para escuchar en el puerto de Cloud Run:

```python
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

# Configuración
BASE_DIR = Path(__file__).resolve().parent
MCP_SERVER_PATH = BASE_DIR / "licitaciones.py"

# Agente LLM
agent = LlmAgent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="Eres un asistente experto en gestión de licitaciones públicas.",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python",
                args=[str(MCP_SERVER_PATH)],
                env={
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONIOENCODING": "utf-8",
                },
            )
        )
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2000,
    ),
)

# ADK Agent
adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="licitaciones_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

# FastAPI App
app = FastAPI()

# CORS - Actualizar con tu dominio de frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agregar endpoint de CopilotKit
add_adk_fastapi_endpoint(app, adk_agent)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "licitaciones_assistant"}

# Ejecutar con el puerto de Cloud Run
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Cloud Run usa PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### 3.4 Crear .dockerignore

```
.venv
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
.env
.DS_Store
```

---

## 🚀 PASO 4: Deploy a Cloud Run

Ahora tienes **2 opciones** para hacer el deploy:

### Opción A: Deploy con `adk` CLI (Recomendada)

```bash
# Desde el directorio que contiene my-agent/
adk deploy cloud_run \
  --project=TU_PROJECT_ID \
  --region=us-central1 \
  --service_name=licitaciones-agent \
  --with_ui \
  --labels tenant=tu-tenant,proyecto=licitaciones \
  my-agent/
```

Parámetros:
- `--project`: Tu Project ID de Google Cloud
- `--region`: Región donde desplegar (ej: us-central1, europe-west1)
- `--service_name`: Nombre del servicio en Cloud Run
- `--with_ui`: Incluye la interfaz web de ADK

- `my-agent/`: Path a tu directorio del agente

### Opción B: Deploy Manual con `gcloud`

```bash
# Navega al directorio del proyecto
cd my-agent

# Deploy directo desde el código fuente
gcloud run deploy licitaciones-agent \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --labels tenant=nombre-tenant,proyecto=licitaciones
  --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest"
```

Parámetros importantes:
- `--source .`: Construye desde el directorio actual
- `--allow-unauthenticated`: Permite acceso público (o usa autenticación)
- `--memory 2Gi`: 2GB de RAM
- `--cpu 2`: 2 CPUs
- `--timeout 300`: Timeout de 5 minutos
- `--set-secrets`: Conecta el secret con la variable de entorno

---

## 🌐 PASO 5: Deploy del Frontend

El frontend (Next.js) se puede desplegar en:

### Opción 1: Vercel (Recomendada para Next.js)

```bash
# Instalar Vercel CLI
npm install -g vercel

# Desde el directorio del frontend
cd my-copilot-app

# Deploy
vercel

# Configurar variables de entorno en Vercel
# NEXT_PUBLIC_BACKEND_URL=https://tu-servicio.run.app
```

### Opción 2: Cloud Run (Frontend también en GCP)

```bash
cd my-copilot-app

# Crear Dockerfile para Next.js
cat > Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
EOF

# Deploy
gcloud run deploy licitaciones-frontend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_BACKEND_URL=https://TU-BACKEND-URL.run.app"
```

---

## 🔍 PASO 6: Verificar el Deploy

### Backend

```bash
# Obtener la URL del servicio
gcloud run services describe licitaciones-agent \
  --region us-central1 \
  --format='value(status.url)'

# Probar health check
curl https://tu-servicio-123456.run.app/health
```

### Frontend

Abre la URL proporcionada por Vercel o Cloud Run en tu navegador.

---

## 🔒 PASO 7: Seguridad (Opcional pero Recomendado)

### 7.1 Habilitar Autenticación

Para requerir autenticación:

```bash
gcloud run services update licitaciones-agent \
  --region us-central1 \
  --no-allow-unauthenticated
```

### 7.2 Crear Service Account

```bash
# Crear service account
gcloud iam service-accounts create licitaciones-sa \
  --display-name="Licitaciones Agent SA"

# Dar permisos al secret
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:licitaciones-sa@TU_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Actualizar el servicio para usar la SA
gcloud run services update licitaciones-agent \
  --region us-central1 \
  --service-account=licitaciones-sa@TU_PROJECT_ID.iam.gserviceaccount.com
```

---

## 💰 PASO 8: Optimización de Costos

Cloud Run cobra por:
- **Tiempo de CPU activo** (cuando procesa requests)
- **Memoria asignada**
- **Requests**

### Consejos para reducir costos:

```bash
# Configurar instancias mínimas en 0 (escala a 0 cuando no hay tráfico)
gcloud run services update licitaciones-agent \
  --region us-central1 \
  --min-instances=0 \
  --max-instances=10

# Ajustar recursos
gcloud run services update licitaciones-agent \
  --region us-central1 \
  --memory=1Gi \
  --cpu=1
```

---

## 📊 PASO 9: Monitoreo

### Ver logs

```bash
# Ver logs en tiempo real
gcloud run services logs tail licitaciones-agent \
  --region us-central1

# Ver logs recientes
gcloud run services logs read licitaciones-agent \
  --region us-central1 \
  --limit=50
```

### Métricas en Cloud Console

Visita: https://console.cloud.google.com/run

Aquí puedes ver:
- Requests por segundo
- Latencia
- Instancias activas
- Errores

---

## 🔄 PASO 10: Actualizar el Deploy

Para actualizar tu agente después de hacer cambios:

```bash
# Opción A: Con adk CLI
adk deploy cloud_run \
  --project=TU_PROJECT_ID \
  --region=us-central1 \
  --service_name=licitaciones-agent \
  --with_ui \
  my-agent/

# Opción B: Con gcloud
cd my-agent
gcloud run deploy licitaciones-agent \
  --source . \
  --region us-central1
```

Cloud Run hace **rolling updates** automáticamente (sin downtime).

---

## ⚠️ Troubleshooting

### Error: "Permission denied"
```bash
# Dar permisos necesarios a tu cuenta
gcloud projects add-iam-policy-binding TU_PROJECT_ID \
  --member="user:tu-email@gmail.com" \
  --role="roles/run.admin"
```

### Error: "Failed to build"
- Verifica que el `Dockerfile` esté correcto
- Asegúrate de que `pyproject.toml` tenga todas las dependencias

### Error: "Container failed to start"
- Revisa los logs: `gcloud run services logs read licitaciones-agent`
- Verifica que el puerto sea 8080
- Confirma que GOOGLE_API_KEY esté configurada

### Error: "Secret not found"
```bash
# Verificar secrets
gcloud secrets list

# Dar acceso al secret
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:TU_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 📚 Resumen de Comandos

```bash
# 1. Autenticación
gcloud auth login
gcloud config set project TU_PROJECT_ID

# 2. Habilitar APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# 3. Crear secret
echo -n "tu_api_key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# 4. Deploy backend
cd my-agent
gcloud run deploy licitaciones-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest"

# 5. Deploy frontend (Vercel)
cd my-copilot-app
vercel

# 6. Ver logs
gcloud run services logs tail licitaciones-agent --region us-central1
```

---

## 🎯 Próximos Pasos

1. ✅ Deploy exitoso del backend
2. ✅ Deploy exitoso del frontend
3. 🔒 Configurar autenticación (opcional)
4. 📊 Configurar alertas y monitoreo
5. 💰 Optimizar costos
6. 🚀 Configurar CI/CD con GitHub Actions

---

## 📞 Recursos Adicionales

- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [ADK Deploy Docs](https://google.github.io/adk-docs/deploy/cloud-run/)
- [Secret Manager Docs](https://cloud.google.com/secret-manager/docs)

---

**¡Listo!** Tu agente de licitaciones ahora está desplegado en Cloud Run. 🎉
