"""
Análisis HV / Reclutamiento — Zoho Recruit + ranking de CVs.
Portado desde AG-UI_AnalisisHV.
"""

import os

from ag_ui_adk import ADKAgent
from google.adk.agents.llm_agent import Agent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.adk.tools.agent_tool import AgentTool

from agents.analisis_hv.analysis_agent import analisis_agent
from agents.analisis_hv.tools.recruit_tools import (
    descargar_hojas_de_vida,
    listar_perfiles,
    obtener_requisitos_perfil,
)
from agents.analisis_hv.tools.sheet_tools import exportar_ranking_a_zoho_sheet

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
DATASET_ID = os.getenv("BQ_DATASET_ID", "reclutamiento_analytics")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "")

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

plugins = []
if PROJECT_ID and DATASET_ID:
    plugins.append(
        BigQueryAgentAnalyticsPlugin(
            project_id=PROJECT_ID,
            dataset_id=DATASET_ID,
            table_id="agent_events",
            config=bq_config,
            location=BQ_LOCATION,
        )
    )

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

adk_app = App(
    name="reclutamiento",
    root_agent=root_agent,
    plugins=plugins,
)

adk_agent = ADKAgent.from_app(
    adk_app,
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)
