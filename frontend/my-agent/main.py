from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

# =========================
# PATH CONFIGURATION
# =========================
BASE_DIR = Path(__file__).resolve().parent
MCP_SERVER_PATH = BASE_DIR / "licitaciones.py"

# =========================
# LLM AGENT
# =========================
agent = LlmAgent(
    name="assistant",
    model="gemini-2.5-flash",
    instruction="Eres un asistente experto en gestión de licitaciones públicas. Ayuda a los usuarios a consultar información sobre licitaciones, requisitos, documentos y proporciona análisis inteligentes.",
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

# =========================
# ADK AGENT WRAPPER
# =========================
adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="demo_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

# =========================
# FASTAPI APPLICATION
# =========================
app = FastAPI()

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CopilotKit endpoint
add_adk_fastapi_endpoint(app, adk_agent)

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": "licitaciones_assistant",
        "mcp_server": str(MCP_SERVER_PATH)
    }

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)