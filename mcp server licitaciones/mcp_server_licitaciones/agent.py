from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.genai import types

# =========================
# PATH RELATIVO SEGURO
# =========================
BASE_DIR = Path(__file__).resolve().parent
MCP_SERVER_PATH = BASE_DIR / "licitaciones.py"

# =========================
# AGENTE ADK
# =========================
root_agent = LlmAgent(
    name="licitaciones_assistant",
    model="gemini-3-flash-preview",
    instruction="Asistente experto en gestión de licitaciones",
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
        max_output_tokens=1500,
    ),
)

# =========================
# LOOP SIMPLE
# =========================
def main():
    print("🤖 Asistente de Licitaciones (ADK + MCP)\n")
    while True:
        msg = input("👤 Tú: ").strip()
        if msg.lower() in {"salir", "exit"}:
            break
        response = root_agent.generate_content(msg)
        print("\n🤖:", response.text, "\n")

if __name__ == "__main__":
    main()
