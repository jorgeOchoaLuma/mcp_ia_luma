"""
Servidor AG-UI para el agente de reclutamiento.
Expone root_agent vía protocolo AG-UI + métricas de tokens en BigQuery.
"""
import os
from fastapi import FastAPI
from dotenv import load_dotenv

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)

from analysis_agent import analisis_agent
from tools.recruit_tools import listar_perfiles, descargar_hojas_de_vida, obtener_requisitos_perfil
from tools.sheet_tools import exportar_ranking_a_zoho_sheet

load_dotenv()

# ── Configuración GCP ──────────────────────────────────────────────────────────
PROJECT_ID  = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET_ID  = os.getenv("BQ_DATASET_ID", "reclutamiento_analytics")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
GCS_BUCKET  = os.getenv("GCS_BUCKET_NAME", "")

# ── BigQuery Analytics Plugin ──────────────────────────────────────────────────
bq_config = BigQueryLoggerConfig(
    enabled=True,
    event_allowlist=[
        "LLM_REQUEST",
        "LLM_RESPONSE",
        "LLM_ERROR",
        "TOOL_STARTING",
        "TOOL_COMPLETED",
        "TOOL_ERROR",
        "INVOCATION_STARTING",
        "INVOCATION_COMPLETED",
        "AGENT_RESPONSE",
    ],
    custom_tags={
        "app": "reclutamiento",
        "env": os.getenv("ENV", "dev"),
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

# ── Root Agent ─────────────────────────────────────────────────────────────────
root_agent = Agent(
    model="gemini-3.1-flash-lite",
    name="reclutamiento",
    description="Agente que descarga y rankea hojas de vida desde Zoho Recruit.",
    instruction="""
Eres un experto en selección de personal. Sigue SIEMPRE este orden:

1. Si el usuario no especifica el perfil exacto → usa listar_perfiles
2. Obtén los requisitos del perfil con obtener_requisitos_perfil usando el ID
3. Descarga los CVs con descargar_hojas_de_vida
4. Pasa al agente analisis_cvs:
   - La 'ruta' con los CVs descargados
   - Los 'requisitos' obtenidos del perfil
   Para que evalúe cada CV contra CADA requisito específico indicando
   CUMPLE ✅ o NO CUMPLE ❌ por requisito
5. Muestra tabla TOP 10 en markdown con puntaje y cumplimiento de requisitos
6. Exporta con exportar_ranking_a_zoho_sheet y comparte el link

Responde siempre en español.
""",
    tools=[
        listar_perfiles,
        obtener_requisitos_perfil,
        descargar_hojas_de_vida,
        AgentTool(agent=analisis_agent),
        exportar_ranking_a_zoho_sheet,
    ],
)

# ── App con plugin BigQuery ────────────────────────────────────────────────────
adk_app = App(
    name="reclutamiento",
    root_agent=root_agent,
    plugins=[bq_plugin],
)

# ── Middleware AG-UI usando from_app() ─────────────────────────────────────────
# from_app() acepta App con plugins — el constructor directo solo acepta Agent
ag_reclutamiento_agent = ADKAgent.from_app(
    adk_app,
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

# ── FastAPI ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Reclutamiento AG-UI Agent")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "bq_dataset": f"{PROJECT_ID}.{DATASET_ID}.agent_events",
    }

add_adk_fastapi_endpoint(app, ag_reclutamiento_agent, path="/")

if __name__ == "__main__":
    import uvicorn

    if not PROJECT_ID:
        print("⚠️  GOOGLE_CLOUD_PROJECT no está configurado en .env")

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)