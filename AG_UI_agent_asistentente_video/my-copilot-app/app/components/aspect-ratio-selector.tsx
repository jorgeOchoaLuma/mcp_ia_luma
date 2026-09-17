"use client";

import { z } from "zod";
import { useHumanInTheLoop } from "@copilotkit/react-core/v2";

const OPCIONES_ASPECT_RATIO = [
    { valor: "16:9", etiqueta: "YouTube / presentación" },
    { valor: "9:16", etiqueta: "Reels / TikTok / Shorts" },
    { valor: "1:1", etiqueta: "Instagram / Facebook / LinkedIn" },
];

export function useAspectRatioSelector() {
    useHumanInTheLoop({
        name: "aspectRatioSelector",
        description: "Pide al usuario elegir el formato/aspect ratio del video antes de generar ayudas visuales.",
        parameters: z.object({}),
        render: ({ status, respond }) => (
            <div className="flex flex-col gap-2 max-w-sm">
                <div className="text-sm font-medium">📐 ¿Para qué formato necesitas las ayudas visuales?</div>
                {OPCIONES_ASPECT_RATIO.map((op) => (
                    <button
                        key={op.valor}
                        disabled={status === "complete"}
                        onClick={() => respond?.(op.valor)}
                        className="text-left rounded-lg border bg-white hover:bg-gray-50 disabled:opacity-50 px-3 py-2 text-sm transition-colors"
                    >
                        <span className="font-semibold">{op.valor}</span> — {op.etiqueta}
                    </button>
                ))}
            </div>
        ),
    });
}