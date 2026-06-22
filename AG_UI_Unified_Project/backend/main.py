"""
Unified AG-UI Backend
Un solo servidor FastAPI con un endpoint por agente.
"""

import os
from pathlib import Path
 
from dotenv import load_dotenv
from fastapi import FastAPI
from gcp_credentials import setup_gcp_credentials, get_service_account_email

load_dotenv()
setup_gcp_credentials(base_dir=Path(__file__).resolve().parent)

# Vertex AI: no mezclar API key con credenciales de service account
if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1", "YES"):
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)

from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from agents.video_agent import adk_agent as video_adk
from agents.transcription_agent import adk_agent as transcription_adk
from agents.transcription_live import register_transcription_live_ws
from agents.url_context_agent import adk_agent as url_adk
from agents.licitaciones_agent import agent as licitaciones_agent
from agents.campaign_agent import agent as campaign_agent
from agents.investigacion_agent import adk_agent as investigacion_adk
from agents.projects_agent import agent as projects_agent
from agents.resumen_reuniones_agent import adk_agent as resumen_reuniones_adk
from agents.soporte_agent import adk_agent as soporte_adk
from agents.analisis_hv.analisis_hv_agent import adk_agent as analisis_hv_adk

app = FastAPI(title="Unified AG-UI Project")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agentes con App + plugins (from_app)
agents = {
    "video_producer": video_adk,
    "url_expert": url_adk,
    "resumen_reuniones": resumen_reuniones_adk,
    "soporte": soporte_adk,
    "analisis_hv": analisis_hv_adk,
    # Agentes LlmAgent simples
    "transcription": transcription_adk,
    "licitaciones": ADKAgent(adk_agent=licitaciones_agent, app_name="licitaciones_app"),
    "campaign_expert": ADKAgent(adk_agent=campaign_agent, app_name="campaign_app"),
    "investigacion_fuentes": investigacion_adk,
    "projects": ADKAgent(adk_agent=projects_agent, app_name="projects_app"),
}

for agent_id, adk_wrapper in agents.items():
    add_adk_fastapi_endpoint(app, adk_wrapper, path=f"/{agent_id}")

register_transcription_live_ws(app)


def _gcp_project_misconfigured(project: str) -> bool:
    if not project:
        return True
    invalid = {
        "global",
        "google_cloud_project",
        "tu-proyecto-gcp",
        "your-project-id",
    }
    if project.lower() in invalid:
        return True
    if project.upper() == "GOOGLE_CLOUD_PROJECT":
        return True
    if project.startswith("GOOGLE_") or project.startswith("${"):
        return True
    return False


@app.get("/health")
def health():
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    gcp_misconfigured = _gcp_project_misconfigured(project)
    return {
        "status": "ok" if not gcp_misconfigured else "degraded",
        "agents": list(agents.keys()),
        "websocket": ["/transcription/live/ws"],
        "gcp": {
            "project_set": bool(project),
            "project_id": project or None,
            "location": os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
            "vertex_ai_mode": os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1", "YES"),
            "service_account": get_service_account_email(),
            "credentials_source": (
                "GOOGLE_APPLICATION_CREDENTIALS_BASE64"
                if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
                else "GOOGLE_APPLICATION_CREDENTIALS"
                if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                else "ADC"
            ),
            "datastore_id": os.environ.get("DATASTORE_ID") or None,
            "vertex_search_location": os.environ.get("VERTEX_SEARCH_LOCATION", "global"),
            "soporte_datastore_id": os.environ.get("SOPORTE_DATASTORE_ID") or os.environ.get("DATASTORE_ID") or None,
            "discovery_engine_role_needed": "roles/discoveryengine.user",
            "misconfigured": gcp_misconfigured,
            "hint": (
                "GOOGLE_CLOUD_PROJECT debe ser el ID real del proyecto GCP "
                "(ej. zippy-sublime-488620-q2), NO el texto 'GOOGLE_CLOUD_PROJECT'."
            )
            if gcp_misconfigured
            else None,
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
