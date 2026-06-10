"use client";

import { createContext, useContext, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";

const DEFAULT_AGENT = "video_producer";

type AgentContextValue = {
  agent: string;
  setAgent: (agent: string) => void;
};

const AgentContext = createContext<AgentContextValue>({
  agent: DEFAULT_AGENT,
  setAgent: () => {},
});

export function useSelectedAgent() {
  return useContext(AgentContext);
}

export function AgentProvider({ children }: { children: React.ReactNode }) {
  const [agent, setAgent] = useState(DEFAULT_AGENT);

  return (
    <AgentContext.Provider value={{ agent, setAgent }}>
      <CopilotKit runtimeUrl="/api/copilotkit" agent={agent} key={agent}>
        {children}
      </CopilotKit>
    </AgentContext.Provider>
  );
}
