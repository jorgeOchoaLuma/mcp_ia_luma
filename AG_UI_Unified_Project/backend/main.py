"""
Unified AG-UI Backend
Combines four specialized agents into a single endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from agents.video_agent import agent as video_agent
from agents.transcription_agent import agent as transcription_agent
from agents.url_context_agent import agent as url_agent
from agents.licitaciones_agent import agent as licitaciones_agent
from agents.campaign_agent import agent as campaign_agent
from agents.investigacion_agent import agent as investigacion_agent

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
}

# Add endpoints for each agent
for agent_id, adk_wrapper in agents.items():
    add_adk_fastapi_endpoint(app, adk_wrapper, path=f"/{agent_id}")

@app.get("/health")
async def health():
    return {"status": "ok", "agents": list(agents.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
