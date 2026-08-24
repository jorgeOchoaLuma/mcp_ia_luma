"use client";

import { useRef, useState } from "react";
import { z } from "zod";
import { useHumanInTheLoop } from "@copilotkit/react-core/v2";

const OPCIONES_ASPECT_RATIO = [
    { valor: "16:9", etiqueta: "YouTube / presentación" },
    { valor: "9:16", etiqueta: "Reels / TikTok / Shorts" },
    { valor: "1:1", etiqueta: "Instagram / Facebook / LinkedIn" },
];

const OPCIONES_ESTILO = [
    { valor: "minimalista_corporativo", etiqueta: "Minimalista corporativo" },
    { valor: "ilustracion_flat", etiqueta: "Ilustración flat" },
    { valor: "fotorrealista", etiqueta: "Fotorrealista" },
    { valor: "isometrico", etiqueta: "Isométrico técnico" },
];

export function useAyudasVisualesConfig() {
    // ref: dispara respond() de forma inmediata y confiable (ya probado).
    const seleccion = useRef<{ aspect_ratio?: string; estilo_id?: string }>({});
    // state: vive en el cuerpo del hook (no dentro de render), solo para
    // resaltar visualmente el botón elegido — es válido aquí porque este
    // hook se ejecuta dentro del render normal de App.
    const [formatoElegido, setFormatoElegido] = useState<string | null>(null);
    const [estiloElegido, setEstiloElegido] = useState<string | null>(null);

    useHumanInTheLoop({
        name: "configurarAyudasVisuales",
        description: "Pide al usuario elegir el formato y el estilo visual, en un solo paso, antes de generar ayudas visuales.",
        parameters: z.object({}),
        render: ({ status, respond }) => {
            const bloqueado = status === "complete";

            const elegirFormato = (valor: string) => {
                seleccion.current.aspect_ratio = valor;
                setFormatoElegido(valor);
                if (seleccion.current.estilo_id) respond?.(seleccion.current);
            };

            const elegirEstilo = (valor: string) => {
                seleccion.current.estilo_id = valor;
                setEstiloElegido(valor);
                if (seleccion.current.aspect_ratio) respond?.(seleccion.current);
            };

            return (
                <div className="max-w-md rounded-xl border border-gray-200 bg-white p-4 shadow-sm space-y-4">
                    <div>
                        <div className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 mb-2">
                            <span>📐</span> Formato
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {OPCIONES_ASPECT_RATIO.map((op) => {
                                const activo = formatoElegido === op.valor;
                                return (
                                    <button
                                        key={op.valor}
                                        disabled={bloqueado}
                                        onClick={() => elegirFormato(op.valor)}
                                        className={[
                                            "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                                            "disabled:opacity-40 disabled:cursor-not-allowed",
                                            activo
                                                ? "bg-black text-white border-black"
                                                : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100",
                                        ].join(" ")}
                                    >
                                        {op.valor} <span className="opacity-70">— {op.etiqueta}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div className="h-px bg-gray-100" />

                    <div>
                        <div className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 mb-2">
                            <span>🎨</span> Estilo
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {OPCIONES_ESTILO.map((op) => {
                                const activo = estiloElegido === op.valor;
                                return (
                                    <button
                                        key={op.valor}
                                        disabled={bloqueado}
                                        onClick={() => elegirEstilo(op.valor)}
                                        className={[
                                            "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                                            "disabled:opacity-40 disabled:cursor-not-allowed",
                                            activo
                                                ? "bg-black text-white border-black"
                                                : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100",
                                        ].join(" ")}
                                    >
                                        {op.etiqueta}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {!bloqueado && (
                        <p className="text-[11px] text-gray-400 pt-1">
                            Se confirma automáticamente al elegir un formato y un estilo.
                        </p>
                    )}
                </div>
            );
        },
    });
}