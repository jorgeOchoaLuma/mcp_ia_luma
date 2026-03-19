import pickle
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://projects-913695724.zohomcp.com/mcp/message?key=d1cdc7d95ae0aa5252bf55db36915868",
    ),
    errlog=None
)

try:
    data = pickle.dumps(toolset)
    print("McpToolset with errlog=None is picklable!")
except Exception as e:
    import traceback
    traceback.print_exc()
