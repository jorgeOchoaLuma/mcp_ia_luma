import {
    CopilotRuntime,
    ExperimentalEmptyAdapter,
    copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
    agents: {
        video_producer: new HttpAgent({ url: "http://localhost:8000/video_producer" }),
        transcription: new HttpAgent({ url: "http://localhost:8000/transcription" }),
        url_expert: new HttpAgent({ url: "http://localhost:8000/url_expert" }),
        licitaciones: new HttpAgent({ url: "http://localhost:8000/licitaciones" }),
        campaign_expert: new HttpAgent({ url: "http://localhost:8000/campaign_expert" }),
        investigacion_fuentes: new HttpAgent({ url: "http://localhost:8000/investigacion_fuentes" }),
    }
});

export const POST = async (req: NextRequest) => {
    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
        runtime,
        serviceAdapter,
        endpoint: "/api/copilotkit",
    });

    return handleRequest(req);
};
