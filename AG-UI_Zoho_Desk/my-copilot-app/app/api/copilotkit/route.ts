import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const AGENT_TIMEOUT_MS = 120_000;

const copilotRuntime = new CopilotRuntime({
  agents: {
    zoho_desk: new HttpAgent({
      url: `${BACKEND_URL}/`,
      timeout: AGENT_TIMEOUT_MS,
    }),
  },
});

export const maxDuration = 120;
export const runtime = "nodejs";

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: copilotRuntime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
