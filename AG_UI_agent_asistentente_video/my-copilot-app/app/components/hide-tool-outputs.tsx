"use client";

import { CheckCircle2, Loader2 } from "lucide-react";
import { useDefaultRenderTool } from "@copilotkit/react-core/v2";

const ETIQUETAS: Record<string, { procesando: string; listo: string }> = {
    generar_resumen: {
        procesando: "Generando resumen",
        listo: "Resumen generado",
    },
    generar_guion_avatar: {
        procesando: "Generando guion",
        listo: "Guion generado",
    },
    generar_ayudas_visuales: {
        procesando: "Creando ayudas visuales",
        listo: "Ayudas visuales listas",
    },
    generar_imagen_visual: {
        procesando: "Generando imagen",
        listo: "Imagen generada",
    },
};

export function useHideToolOutputs() {
    useDefaultRenderTool({
        render: ({ name, status }) => {
            const etiqueta = ETIQUETAS[name] ?? {
                procesando: "Procesando",
                listo: "Listo",
            };
            const completo = status === "complete";

            return (
                <div className="inline-flex items-center gap-1.5 text-sm">
                    {completo ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                    ) : (
                        <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
                    )}
                    <span className="text-gray-700">
                        {completo ? etiqueta.listo : etiqueta.procesando}
                    </span>
                    {completo && (
                        <span className="text-green-600 font-medium">Listo</span>
                    )}
                </div>
            );
        },
    });
}