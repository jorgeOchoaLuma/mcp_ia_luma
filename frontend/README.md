#  Sistema de Gestión de Licitaciones con IA
# ADK with AG-UI

**Google ADK + CopilotKit + FastMCP + UV**

Sistema completo para gestionar licitaciones públicas con un agente de IA conversacional.

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
npm install @copilotkit/react-ui

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
