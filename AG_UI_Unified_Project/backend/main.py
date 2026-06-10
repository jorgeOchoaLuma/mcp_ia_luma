"""
Unified AG-UI Backend
Un solo servidor FastAPI con un endpoint por agente.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from gcp_credentials import setup_gcp_credentials

load_dotenv()
setup_gcp_credentials(base_dir=Path(__file__).resolve().parent)
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from agents.video_agent import agent as video_agent
from agents.transcription_agent import agent as transcription_agent
from agents.url_context_agent import agent as url_agent
from agents.licitaciones_agent import agent as licitaciones_agent
from agents.campaign_agent import agent as campaign_agent
from agents.investigacion_agent import agent as investigacion_agent
from agents.projects_agent import agent as projects_agent
from agents.resumen_reuniones_agent import adk_agent as resumen_reuniones_adk

app = FastAPI(title="Unified AG-UI Project")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK wrappers for each agent
agents = {
    "video_producer": ADKAgent(adk_agent=video_agent, app_name="video_app"),
    "transcription": ADKAgent(adk_agent=transcription_agent, app_name="transcription_app"),
    "url_expert": ADKAgent(adk_agent=url_agent, app_name="url_app"),
    "licitaciones": ADKAgent(adk_agent=licitaciones_agent, app_name="licitaciones_app"),
    "campaign_expert": ADKAgent(adk_agent=campaign_agent, app_name="campaign_app"),
    "investigacion_fuentes": ADKAgent(adk_agent=investigacion_agent, app_name="investigacion_app"),
    "projects": ADKAgent(adk_agent=projects_agent, app_name="projects_app"),
    "resumen_reuniones": resumen_reuniones_adk,
}

# Add endpoints for each agent
for agent_id, adk_wrapper in agents.items():
    add_adk_fastapi_endpoint(app, adk_wrapper, path=f"/{agent_id}")

@app.get("/health")
 async def health():
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    gcp_misconfigured = not project or project.lower() == "global"
    return {
        "status": "ok" if not gcp_misconfigured else "degraded",
        "agents": list(agents.keys()),
        "gcp": {
            "project_set": bool(project),
            "project_id": project or None,
            "location": os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
            "misconfigured": gcp_misconfigured,
            "hint": (
                "GOOGLE_CLOUD_PROJECT debe ser el ID del proyecto (ej. zippy-sublime-488620-q2), "
                "no 'global'. 'global' va en GOOGLE_CLOUD_LOCATION si aplica, pero se recomienda us-central1."
            )
            if gcp_misconfigured
            else None,
        },
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
