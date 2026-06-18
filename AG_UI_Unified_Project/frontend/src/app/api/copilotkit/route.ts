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

const runtime = new CopilotRuntime({
    agents: {
        video_producer: new HttpAgent({ url: `${BACKEND_URL}/video_producer`, timeout: AGENT_TIMEOUT_MS }),
        transcription: new HttpAgent({ url: `${BACKEND_URL}/transcription`, timeout: AGENT_TIMEOUT_MS }),
        url_expert: new HttpAgent({ url: `${BACKEND_URL}/url_expert`, timeout: AGENT_TIMEOUT_MS }),
        soporte: new HttpAgent({ url: `${BACKEND_URL}/soporte`, timeout: AGENT_TIMEOUT_MS }),
        licitaciones: new HttpAgent({ url: `${BACKEND_URL}/licitaciones`, timeout: AGENT_TIMEOUT_MS }),
        campaign_expert: new HttpAgent({ url: `${BACKEND_URL}/campaign_expert`, timeout: AGENT_TIMEOUT_MS }),
        investigacion_fuentes: new HttpAgent({ url: `${BACKEND_URL}/investigacion_fuentes`, timeout: AGENT_TIMEOUT_MS }),
        projects: new HttpAgent({ url: `${BACKEND_URL}/projects`, timeout: AGENT_TIMEOUT_MS }),
        resumen_reuniones: new HttpAgent({
            url: `${BACKEND_URL}/resumen_reuniones`,
            timeout: AGENT_TIMEOUT_MS,
        }),
    },
});

export const maxDuration = 120;
export const runtime = "nodejs";

export const POST = async (req: NextRequest) => {
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime,
        serviceAdapter,
        endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
};
