"""
Licitaciones Assistant
Integrated with MCP server for managing tenders.
"""

from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "mcp server licitaciones" / "mcp_server_licitaciones"
MCP_SERVER_PATH = BASE_DIR / "licitaciones.py"

agent = LlmAgent(
    name="licitaciones_assistant",
    model="gemini-2.5-flash",
    instruction="Asistente experto en gestión de licitaciones. Usa las herramientas MCP para listar y detallar licitaciones.",
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python",
                args=[str(MCP_SERVER_PATH)],
                env={"PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
            )
        )
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1500,
    ),
)
