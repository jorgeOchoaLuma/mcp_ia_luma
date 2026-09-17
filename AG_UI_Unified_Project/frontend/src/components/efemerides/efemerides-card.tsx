"use client";

import { z } from "zod";

export const EfemerideSchema = z.object({
    fecha: z.string().describe("Fecha del evento, ej. '1 Agosto'"),
    evento: z.string().describe("Nombre del evento o hito"),
    categoria: z
        .enum(["Nacional Colombia", "Internacional", "Industria"])
        .describe("Categoría del evento"),
    descripcion: z.string().describe("Resumen de 1 frase"),
});

export const EfemeridesByCategoryProps = z.object({
    efemerides: z.array(EfemerideSchema),
});

export type EfemeridesByCategoryProps = z.infer<
    typeof EfemeridesByCategoryProps
>;

const CATEGORY_STYLES: Record<
    z.infer<typeof EfemerideSchema>["categoria"],
    { badge: string; header: string }
> = {
    "Nacional Colombia": {
        badge: "bg-yellow-100 text-yellow-800 border-yellow-300",
        header: "text-yellow-800",
    },
    Internacional: {
        badge: "bg-blue-100 text-blue-800 border-blue-300",
        header: "text-blue-800",
    },
    Industria: {
        badge: "bg-green-100 text-green-800 border-green-300",
        header: "text-green-800",
    },
};

const CATEGORIES = ["Nacional Colombia", "Internacional", "Industria"] as const;

export function EfemeridesByCategory({
    efemerides,
}: EfemeridesByCategoryProps) {
    if (!efemerides || efemerides.length === 0) {
        return (
            <div className="rounded-lg border bg-white p-4 text-sm text-gray-500">
                No se encontraron efemérides que cumplan los criterios.
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full">
            {CATEGORIES.map((categoria) => {
                const items = efemerides.filter((e) => e.categoria === categoria);
                if (items.length === 0) return null;

                const style = CATEGORY_STYLES[categoria];

                return (
                    <div key={categoria} className="space-y-2">
                        <div className={`text-sm font-semibold ${style.header}`}>
                            {categoria}
                        </div>
                        {items.map((item, idx) => (
                            <div
                                key={`${categoria}-${idx}`}
                                className="rounded-lg border bg-white p-3 space-y-1"
                            >
                                <div className="flex items-center justify-between gap-2">
                                    <span className="font-medium text-sm">{item.evento}</span>
                                    <span
                                        className={`text-xs px-2 py-0.5 rounded-full border ${style.badge}`}
                                    >
                                        {item.fecha}
                                    </span>
                                </div>
                                <div className="text-xs text-gray-600">
                                    {item.descripcion}
                                </div>
                            </div>
                        ))}
                    </div>
                );
            })}
        </div>
    );
}
