from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import google_search
from google.adk.tools.function_tool import FunctionTool
from google.genai.types import Content, Part

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools import url_context
from google.genai import types
from typing import Optional

agent = LlmAgent(
    model="gemini-2.5-flash",
    name="zoho_agent",
    description="Eres un asistente que gestiona información project",
    instruction="""Eres un asistente que gestiona información project del portal lumasas id 854075653 en Zoho. Usa las herramientas disponibles. Tener en cuenta el formato de fecha de inicio 
    y fecha de vencimiento de los proyectos es dd/mm/yyyy hh:mm aaa
    Eres un agente que crea proyectos en el sistema.
    Eres un agente que crea proyectos en Zoho Projects.

Cuando el usuario mencione crear un proyecto, extrae el nombre y detecta 
el prefijo para obtener automáticamente todos los parámetros necesarios. 
El usuario NUNCA proporcionará IDs — tú los resuelves desde la tabla.

## Tabla de configuración por prefijo

| Prefijo | Grupo de proyectos  | group_id | copy_from           |
|---------|---------------------|----------|---------------------|
| PBC_    | PROYECTOS OPERATIVOS 2026        | 2311121000004032234       | 2311121000004520029 |
| GPO_    | PROYECTOS PRUEBA    | 2311121000004461303     | 2311121000004520029                 |
| SR_     | [pendiente]         | [id]     | [id]                |

## Instrucción crítica

1. Detecta el prefijo del nombre del proyecto (todo lo que está antes del _)
2. Busca ese prefijo en la tabla y obtén group_id y copy_from
3. Llama el tool de creación con esos valores SIN pedirle nada al usuario
4. Envía copy_from SIEMPRE como string (ej: "2311121000004520029" o "2311121000000522271")

Nunca le preguntes al usuario por IDs, grupos ni copy_from.
Esa información siempre viene de la tabla.
Si el prefijo no existe en la tabla, informa al usuario que 
ese tipo de proyecto no está configurado..
    """,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://projects-913695724.zohomcp.com/mcp/message?key=d1cdc7d95ae0aa5252bf55db36915868",
            ),
            errlog=None
        )
    ],
)

adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="app_projects",
    user_id="projects_user",
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