"use client";

import { z } from "zod";

export const VisualAidCardProps = z.object({
    momento: z.string(),
    elemento_visual: z.string(),
    texto_overlay: z.string(),
    image_url: z.string(),
    requiere_revision: z.boolean(),
});

type VisualAidCardProps = z.infer<typeof VisualAidCardProps>;

function VisualAidCard({
    momento,
    elemento_visual,
    texto_overlay,
    image_url,
    requiere_revision,
}: VisualAidCardProps) {
    return (
        <div className="rounded-lg border bg-white overflow-hidden">
            <div className="relative">
                <img src={image_url} alt={elemento_visual} className="w-full h-auto" />
                {requiere_revision && (
                    <span className="absolute top-2 right-2 bg-amber-100 text-amber-800 text-xs font-medium px-2 py-1 rounded-full border border-amber-300">
                        ⚠️ Revisar calidad
                    </span>
                )}
            </div>
            <div className="p-3 space-y-1">
                <div className="text-xs font-medium text-gray-500">{momento}</div>
                <div className="text-sm font-semibold">{elemento_visual}</div>
                <div className="text-sm text-gray-600 border-t pt-1 mt-1">
                    Overlay: <span className="italic">"{texto_overlay}"</span>
                </div>
            </div>
        </div>
    );
}

export const VisualAidGalleryProps = z.object({
    imagenes: z.array(VisualAidCardProps).optional(),
});

type VisualAidGalleryProps = z.infer<typeof VisualAidGalleryProps>;

export function VisualAidGallery({ imagenes }: VisualAidGalleryProps) {
    if (!imagenes || imagenes.length === 0) {
        return (
            <div className="text-sm text-gray-400 italic">
                Generando ayudas visuales…
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl">
            {imagenes.map((img, i) => (
                <VisualAidCard key={img.image_url ?? i} {...img} />
            ))}
        </div>
    );
}