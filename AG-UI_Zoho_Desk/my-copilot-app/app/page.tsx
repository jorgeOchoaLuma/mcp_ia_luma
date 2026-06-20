"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { Headphones, Ticket, MessageSquare, Search } from "lucide-react";

const SUGGESTIONS = [
  "Lista los tickets abiertos de hoy",
  "Busca tickets con prioridad alta",
  "Resume el ticket #12345",
  "¿Cuántos tickets hay sin asignar?",
];

export default function Page() {
  return (
    <main className="min-h-screen bg-[#0f1419] text-white">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-orange-500/20 border border-orange-500/30">
              <Headphones className="w-8 h-8 text-orange-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Zoho Desk</h1>
              <p className="text-gray-400 text-sm">Ticket Operations · MCP</p>
            </div>
          </div>
          <p className="text-gray-300 leading-relaxed">
            Asistente conectado al MCP de Zoho Desk. Consulta, gestiona y opera tickets
            desde el chat lateral.
          </p>
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          {[
            { icon: Ticket, label: "Tickets", desc: "Crear y actualizar" },
            { icon: Search, label: "Buscar", desc: "Filtrar por estado" },
            { icon: MessageSquare, label: "Comentarios", desc: "Seguimiento" },
          ].map(({ icon: Icon, label, desc }) => (
            <div
              key={label}
              className="p-4 rounded-xl border border-gray-800 bg-gray-900/50"
            >
              <Icon className="w-5 h-5 text-orange-400 mb-2" />
              <p className="font-medium">{label}</p>
              <p className="text-xs text-gray-500">{desc}</p>
            </div>
          ))}
        </div>

        <section>
          <p className="text-sm text-gray-500 mb-3">Prueba con:</p>
          <ul className="space-y-2">
            {SUGGESTIONS.map((s) => (
              <li
                key={s}
                className="text-sm text-gray-400 px-3 py-2 rounded-lg bg-gray-900/60 border border-gray-800"
              >
                “{s}”
              </li>
            ))}
          </ul>
        </section>
      </div>

      <CopilotSidebar
        defaultOpen
        labels={{
          title: "Zoho Desk Assistant",
          initial: "¿En qué ticket te ayudo?",
        }}
      />
    </main>
  );
}
