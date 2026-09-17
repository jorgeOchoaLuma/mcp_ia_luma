"""
Wrapper ADKAgent + App para el agente de Deep Research.
Importa el agente definido en researcher.py y lo envuelve con BigQuery plugin.
"""

import os

from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from ag_ui_adk import ADKAgent

from .researcher import deep_researcher

# ─── Config ───────────────────────────────────────────────────────────────────
PROJECT_ID    = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "agente_analytics_db")
BQ_LOCATION   = os.environ.get("BQ_LOCATION", "us-central1")

# ─── BigQuery Plugin ──────────────────────────────────────────────────────────
_bq_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=BQ_DATASET_ID,
    location=BQ_LOCATION,
)

# ─── App ──────────────────────────────────────────────────────────────────────
_app = App(
    name="app_deepsearch_recomendation",
    root_agent=deep_researcher,
    plugins=[_bq_plugin],
)

# ─── ADKAgent exportado ───────────────────────────────────────────────────────
adk_agent = ADKAgent.from_app(
    app=_app,
    user_id="user_deepsearch_recomendation",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)
