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
        video_producer: new HttpAgent({ url: `${BACKEND_URL}/video_producer` }) as any,
        transcription: new HttpAgent({ url: `${BACKEND_URL}/transcription` }) as any,
        url_expert: new HttpAgent({ url: `${BACKEND_URL}/url_expert` }) as any,
        soporte: new HttpAgent({ url: `${BACKEND_URL}/soporte` }) as any,
        analisis_hv: new HttpAgent({ url: `${BACKEND_URL}/analisis_hv` }) as any,
        licitaciones: new HttpAgent({ url: `${BACKEND_URL}/licitaciones` }) as any,
        campaign_expert: new HttpAgent({ url: `${BACKEND_URL}/campaign_expert` }) as any,
        investigacion_fuentes: new HttpAgent({ url: `${BACKEND_URL}/investigacion_fuentes` }) as any,
        projects: new HttpAgent({ url: `${BACKEND_URL}/projects` }) as any,
        efemerides: new HttpAgent({ url: `${BACKEND_URL}/efemerides` }) as any,
        deepsearch: new HttpAgent({ url: `${BACKEND_URL}/deepsearch` }) as any,
        resumen_reuniones: new HttpAgent({ url: `${BACKEND_URL}/resumen_reuniones` }) as any,
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
