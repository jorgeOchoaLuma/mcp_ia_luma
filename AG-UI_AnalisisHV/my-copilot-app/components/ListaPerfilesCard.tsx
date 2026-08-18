import React from "react";
import { Briefcase, ArrowRight, AlertTriangle, Calendar } from "lucide-react";

type Perfil = {
    id: string;
    nombre: string;
    estado: string;
    fecha_apertura: string;
    fecha_cierre: string;
};

type ListarPerfilesResult = {
    perfiles: Perfil[];
    total: number;
    advertencias: string[];
    mensaje: string;
};

function parseResult<T>(result: unknown): T | undefined {
    if (typeof result !== "string" || result.length === 0) return undefined;
    try {
        return JSON.parse(result) as T;
    } catch {
        return undefined;
    }
}

function EstadoBadge({ estado }: { estado: string }) {
    const abierto = estado.toLowerCase().includes("open") || estado.toLowerCase().includes("abiert");
    return (
        <span
            className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ${abierto ? "bg-emerald-50 text-emerald-600" : "bg-gray-100 text-gray-500"
                }`}
        >
            {estado || "—"}
        </span>
    );
}

export function ListaPerfilesCard({
    status,
    result,
    onSelectPerfil,
}: {
    status: string;
    result?: unknown;
    onSelectPerfil?: (perfil: { id: string; nombre: string }) => void;
}) {
    if (status !== "complete") {
        return (
            <div className="flex items-center gap-2 py-1.5 text-sm text-gray-500">
                <Briefcase className="h-4 w-4 animate-pulse text-[#223b8f]" />
                <span>Buscando perfiles disponibles…</span>
            </div>
        );
    }

    const data = parseResult<ListarPerfilesResult>(result);
    const perfiles = data?.perfiles ?? [];

    if (perfiles.length === 0) {
        return (
            <div className="rounded-xl border border-gray-200 p-3 text-sm text-gray-500">
                No hay perfiles abiertos en este momento.
            </div>
        );
    }

    const conteoPorNombre = perfiles.reduce<Record<string, number>>((acc, p) => {
        acc[p.nombre] = (acc[p.nombre] ?? 0) + 1;
        return acc;
    }, {});

    return (
        <div className="rounded-xl border border-gray-200 overflow-hidden my-1">
            <div className="px-3 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Perfiles abiertos ({data?.total ?? perfiles.length})
            </div>

            {data?.advertencias && data.advertencias.length > 0 && (
                <div className="px-3 py-2 bg-amber-50 border-b border-amber-100 flex items-start gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
                    <span className="text-xs text-amber-700">
                        Hay perfiles con el mismo nombre — se muestra el ID para diferenciarlos.
                    </span>
                </div>
            )}

            <div className="divide-y divide-gray-100">
                {perfiles.map((perfil) => {
                    const duplicado = conteoPorNombre[perfil.nombre] > 1;
                    return (
                        <button
                            key={perfil.id}
                            onClick={() => onSelectPerfil?.({ id: perfil.id, nombre: perfil.nombre })}
                            className="w-full flex items-center justify-between gap-3 px-3 py-2.5 text-left hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-center gap-2 min-w-0">
                                <Briefcase className="h-4 w-4 text-[#223b8f] shrink-0" />
                                <div className="min-w-0">
                                    <div className="flex items-center gap-1.5">
                                        <span className="text-sm font-medium text-gray-800 truncate">{perfil.nombre}</span>
                                        <EstadoBadge estado={perfil.estado} />
                                    </div>
                                    <div className="flex items-center gap-2 text-[11px] text-gray-400 mt-0.5">
                                        {duplicado && <span className="font-mono">ID: {perfil.id}</span>}
                                        {perfil.fecha_apertura && (
                                            <span className="flex items-center gap-0.5">
                                                <Calendar className="h-3 w-3" /> {perfil.fecha_apertura}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <ArrowRight className="h-3.5 w-3.5 text-gray-300 shrink-0" />
                        </button>
                    );
                })}
            </div>
        </div>
    );
}