from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

# Cambiar import relativo por absoluto
from agents.researcher import deep_researcher, search_agent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin

# --- Configuración del plugin de BigQuery Agent Analytics ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "agente_analytics_db")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "us-central1")

if not PROJECT_ID:
    raise ValueError("Falta la variable de entorno GOOGLE_CLOUD_PROJECT en tu .env")

bq_analytics_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=BQ_DATASET_ID,
    location=BQ_LOCATION,
)

app_instance = App(
    name="app_deedsearcher_recomendation",
    root_agent=deep_researcher,
    plugins=[bq_analytics_plugin],
)

adk_agent = ADKAgent.from_app(
    app=app_instance,
    user_id="user_deedsearcher_recomendation",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_adk_fastapi_endpoint(app, adk_agent, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

