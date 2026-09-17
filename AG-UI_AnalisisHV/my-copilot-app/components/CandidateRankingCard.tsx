import React from "react";

interface Requisito {
    requisito: string;
    cumple: boolean;
    evidencia: string;
}

interface Candidato {
    nombre: string;
    puntaje: number;
    email?: string;
    requisitos: Requisito[];
    resumen?: string;
}

interface CandidateRankingCardProps {
    nombre_perfil: string;
    candidatos: Candidato[];
}

export function CandidateRankingCard({
    nombre_perfil,
    candidatos = [],
}: CandidateRankingCardProps) {
    console.log("[DEBUG] nombre_perfil:", nombre_perfil);
    console.log("[DEBUG] candidatos:", JSON.stringify(candidatos, null, 2));

    // Guard completo antes de renderizar
    if (!candidatos || !Array.isArray(candidatos) || candidatos.length === 0) {
        return (
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                <h2 className="text-lg font-bold text-[#223b8f]">
                    Ranking — {nombre_perfil}
                </h2>
                <p className="text-sm text-gray-400 mt-2">
                    Cargando candidatos...
                </p>
            </div>
        );
    }

    return (
        <div className="rounded-xl border border-gray-200 bg-white p-4 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-[#223b8f]">
                    Ranking — {nombre_perfil}
                </h2>
                <span className="text-sm text-gray-500">
                    {candidatos?.length ?? 0} candidato{(candidatos?.length ?? 0) !== 1 ? "s" : ""}
                </span>
            </div>

            {candidatos.map((candidato, index) => {
                const requisitos = candidato?.requisitos ?? [];
                const cumplidos = requisitos.filter((r) => r?.cumple === true).length;
                const total = requisitos.length;
                const porcentaje = total > 0
                    ? Math.round((cumplidos / total) * 100)
                    : (candidato?.puntaje ?? 0);

                return (
                    <div key={index} className="border border-gray-100 rounded-lg p-3 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-bold text-gray-400">#{index + 1}</span>
                                <div>
                                    <div className="font-semibold text-gray-800">
                                        {candidato?.nombre ?? "Sin nombre"}
                                    </div>
                                    {candidato?.email && (
                                        <div className="text-xs text-gray-400">{candidato.email}</div>
                                    )}
                                </div>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-sm font-bold ${porcentaje >= 75 ? "bg-green-100 text-green-700"
                                    : porcentaje >= 50 ? "bg-yellow-100 text-yellow-700"
                                        : "bg-red-100 text-red-700"
                                }`}>
                                {porcentaje}%
                            </div>
                        </div>

                        <div className="w-full bg-gray-100 rounded-full h-1.5">
                            <div
                                className={`h-1.5 rounded-full transition-all ${porcentaje >= 75 ? "bg-green-500"
                                        : porcentaje >= 50 ? "bg-yellow-500"
                                            : "bg-red-500"
                                    }`}
                                style={{ width: `${porcentaje}%` }}
                            />
                        </div>

                        {candidato?.resumen && (
                            <p className="text-xs text-gray-500 italic">{candidato.resumen}</p>
                        )}

                        {requisitos.length > 0 && (
                            <table className="w-full text-xs border-collapse">
                                <thead>
                                    <tr className="bg-gray-50">
                                        <th className="text-left p-1.5 text-gray-500 font-medium border-b">Requisito</th>
                                        <th className="text-center p-1.5 text-gray-500 font-medium border-b w-16">Cumple</th>
                                        <th className="text-left p-1.5 text-gray-500 font-medium border-b">Evidencia</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {requisitos.map((req, i) => (
                                        <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                                            <td className="p-1.5 text-gray-700 font-medium">
                                                {req?.requisito ?? ""}
                                            </td>
                                            <td className="p-1.5 text-center">
                                                {req?.cumple === true
                                                    ? <span className="text-green-600 font-bold">✅</span>
                                                    : <span className="text-red-500 font-bold">❌</span>
                                                }
                                            </td>
                                            <td className="p-1.5 text-gray-500 italic">
                                                {req?.evidencia ?? ""}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}

                        <div className="text-xs text-right text-gray-400">
                            {cumplidos}/{total} requisitos cumplidos
                        </div>
                    </div>
                );
            })}
        </div>
    );
}