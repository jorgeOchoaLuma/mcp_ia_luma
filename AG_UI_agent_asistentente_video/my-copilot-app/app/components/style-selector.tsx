"use client";

import { z } from "zod";
import { useHumanInTheLoop } from "@copilotkit/react-core/v2";

const OPCIONES_ESTILO = [
    { valor: "minimalista_corporativo", etiqueta: "Minimalista corporativo" },
    { valor: "ilustracion_flat", etiqueta: "Ilustración flat" },
    { valor: "fotorrealista", etiqueta: "Fotorrealista" },
    { valor: "isometrico", etiqueta: "Isométrico técnico" },
];

export function useStyleSelector() {
    useHumanInTheLoop({
        name: "styleSelector",
        description: "Pide al usuario elegir el estilo visual antes de generar ayudas visuales.",
        parameters: z.object({}),
        render: ({ status, respond }) => (
            <div className="grid grid-cols-2 gap-2 max-w-md">
                {OPCIONES_ESTILO.map((op) => (
                    <button
                        key={op.valor}
                        disabled={status === "complete"}
                        onClick={() => respond?.(op.valor)}
                        className="rounded-lg border bg-white hover:bg-gray-50 disabled:opacity-50 overflow-hidden text-left transition-colors p-2 text-sm font-medium"
                    >
                        {op.etiqueta}
                    </button>
                ))}
            </div>
        ),
    });
}