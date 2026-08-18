"""
Servidor AG-UI para el agente de reclutamiento.
"""
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset
from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.apps import App
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)

from analysis_agent import analisis_agent
from tools.recruit_tools import listar_perfiles, descargar_hojas_de_vida, obtener_requisitos_perfil

load_dotenv()

PROJECT_ID  = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET_ID  = os.getenv("BQ_DATASET_ID", "reclutamiento_analytics")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
GCS_BUCKET  = os.getenv("GCS_BUCKET_NAME", "")
ENV         = os.getenv("ENV", "dev")

# ── Artifact Service ───────────────────────────────────────────────────────────
if ENV == "prod" and GCS_BUCKET:
    artifact_service = GcsArtifactService(bucket_name=GCS_BUCKET)
    print(f"✅ ArtifactService: GCS bucket '{GCS_BUCKET}'")
else:
    artifact_service = InMemoryArtifactService()
    print("✅ ArtifactService: InMemory (dev)")

# ── BigQuery Plugin ────────────────────────────────────────────────────────────
bq_config = BigQueryLoggerConfig(
    enabled=True,
    event_allowlist=[
        "LLM_REQUEST", "LLM_RESPONSE", "LLM_ERROR",
        "TOOL_STARTING", "TOOL_COMPLETED", "TOOL_ERROR",
        "INVOCATION_STARTING", "INVOCATION_COMPLETED", "AGENT_RESPONSE",
    ],
    custom_tags={
        "app": "reclutamiento",
        "env": ENV,
        "client": os.getenv("CLIENT_ID", "default"),
    },
    gcs_bucket_name=GCS_BUCKET if GCS_BUCKET else None,
    max_content_length=500 * 1024,
    batch_size=1,
    shutdown_timeout=10.0,
    create_views=True,
    auto_schema_upgrade=True,
)

bq_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=DATASET_ID,
    table_id="agent_events",
    config=bq_config,
    location=BQ_LOCATION,
)

# ── AGUI Toolset ───────────────────────────────────────────────────────────────
agui_toolset = AGUIToolset(
    tool_filter=["mostrarRanking"]
)

# ── Root Agent ─────────────────────────────────────────────────────────────────
root_agent = Agent(
    model="gemini-3.6-flash",
    name="reclutamiento",
    description="Agente que descarga y rankea hojas de vida desde Zoho Recruit.",
    instruction="""
Eres un experto en selección de personal. Sigue SIEMPRE este orden:

1. Si el usuario no especifica el perfil exacto → usa listar_perfiles
2. Obtén los requisitos del perfil con obtener_requisitos_perfil usando el ID
3. Descarga los CVs con descargar_hojas_de_vida
4. Pasa al agente analisis_cvs la 'ruta' y los 'requisitos'
5. Con los resultados de analisis_cvs, llama SIEMPRE la herramienta
   mostrarRanking con:
   - nombre_perfil: nombre del perfil evaluado
   - candidatos: lista con nombre, puntaje, email, requisitos evaluados y resumen
   de cada candidato, ordenada por puntaje descendente

Responde siempre en español.
""",
    tools=[
        listar_perfiles,
        obtener_requisitos_perfil,
        descargar_hojas_de_vida,
        AgentTool(agent=analisis_agent),
        agui_toolset,
    ],
)

# ── App con BigQuery ───────────────────────────────────────────────────────────
adk_app = App(
    name="reclutamiento",
    root_agent=root_agent,
    plugins=[bq_plugin],
)

# ── ADKAgent — from_app() para BigQuery + artifact_service para Artifacts ──────
ag_reclutamiento_agent = ADKAgent.from_app(
    adk_app,
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
    artifact_service=artifact_service,
)

# ── FastAPI ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Reclutamiento AG-UI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_adk_fastapi_endpoint(app, ag_reclutamiento_agent, path="/")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        timeout_keep_alive=300,
        h11_max_incomplete_event_size=None,
    )