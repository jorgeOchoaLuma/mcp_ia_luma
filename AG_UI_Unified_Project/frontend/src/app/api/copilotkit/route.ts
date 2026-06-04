import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const runtime = new CopilotRuntime({
    agents: {
        video_producer: new HttpAgent({ url: `${BACKEND_URL}/video_producer` }),
        transcription: new HttpAgent({ url: `${BACKEND_URL}/transcription` }),
        url_expert: new HttpAgent({ url: `${BACKEND_URL}/url_expert` }),
        licitaciones: new HttpAgent({ url: `${BACKEND_URL}/licitaciones` }),
        campaign_expert: new HttpAgent({ url: `${BACKEND_URL}/campaign_expert` }),
        investigacion_fuentes: new HttpAgent({ url: `${BACKEND_URL}/investigacion_fuentes` }),
        projects: new HttpAgent({ url: `${BACKEND_URL}/projects` }),
        resumen_reuniones: new HttpAgent({ url: `${BACKEND_URL}/resumen_reuniones` }),
    },
});

export const POST = async (req: NextRequest) => {
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime,
        serviceAdapter,
        endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
};
