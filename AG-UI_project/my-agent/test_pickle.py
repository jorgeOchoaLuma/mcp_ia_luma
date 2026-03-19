import pickle
import sys
from main import agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

def __getstate__(self):
    state = self.__dict__.copy()
    state.pop('_errlog', None)
    return state

def __setstate__(self, state):
    self.__dict__.update(state)
    self._errlog = sys.stderr

McpToolset.__getstate__ = __getstate__
McpToolset.__setstate__ = __setstate__

try:
    data = pickle.dumps(agent)
    print("Agent is picklable after monkey patch!")
except Exception as e:
    import traceback
    traceback.print_exc()
