"use client";
import React from "react";
import { z } from "zod";
import {
  CopilotKit,
  CopilotChat,
  useComponent,
  useRenderTool,
  useAgent,
} from "@copilotkit/react-core/v2";
import {
  SendHorizontal,
  ClipboardList,
  Download,
  BrainCircuit,
  Check,
} from "lucide-react";
import { CandidateRankingCard } from "@/components/CandidateRankingCard";
import { ListaPerfilesCard } from "@/components/ListaPerfilesCard";
import { useReclutamientoSuggestions } from "@/app/hooks/suggestions";

// ── Mapeo de tools backend "de proceso" → paso legible ──────────────────────
const STEP_LABELS: Record<string, { label: string; icon: React.ElementType }> = {
  obtener_requisitos_perfil: { label: "Obteniendo requisitos del perfil", icon: ClipboardList },
  descargar_hojas_de_vida: { label: "Descargando hojas de vida", icon: Download },
  analisis_cvs: { label: "Analizando candidatos", icon: BrainCircuit },
};

function ProcessStep({ toolName, status }: { toolName: string; status: string }) {
  const step = STEP_LABELS[toolName];
  if (!step) return null;
  const Icon = status === "complete" ? Check : step.icon;
  return (
    <div className="flex items-center gap-2 py-1.5 text-sm text-gray-600">
      <Icon
        className={`h-4 w-4 ${status !== "complete" ? "animate-pulse text-[#223b8f]" : "text-emerald-500"
          }`}
      />
      <span>{step.label}</span>
      {status === "complete" && <span className="text-xs text-emerald-500">Listo</span>}
    </div>
  );
}

export default function AgenticChatDemo() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="reclutamiento">
      <Chat />
    </CopilotKit>
  );
}

function Chat() {
  useReclutamientoSuggestions();

  const { agent } = useAgent({ agentId: "reclutamiento" });

  useComponent({
    name: "mostrarRanking",
    description:
      "Muestra el ranking visual de candidatos con tabla de cumplimiento de requisitos. Úsalo SIEMPRE después de analizar los CVs.",
    parameters: z.object({
      nombre_perfil: z.string().describe("Nombre del perfil evaluado"),
      candidatos: z
        .array(
          z.object({
            nombre: z.string().describe("Nombre completo del candidato"),
            puntaje: z.number().describe("Puntaje 0-100"),
            email: z.string().optional().describe("Email del candidato"),
            resumen: z.string().optional().describe("Resumen del candidato"),
            requisitos: z
              .array(
                z.object({
                  requisito: z.string().describe("Nombre del requisito"),
                  cumple: z.boolean().describe("true si cumple, false si no"),
                  evidencia: z.string().describe("Cita textual del CV o Sin evidencia"),
                })
              )
              .describe("Lista de requisitos evaluados con evidencia textual"),
          })
        )
        .describe("Lista de candidatos ordenada por puntaje descendente"),
    }),
    render: CandidateRankingCard,
  });

  // ── listar_perfiles: componente de datos controlado (L3), clickeable ─────
  useRenderTool({
    name: "listar_perfiles",
    render: ({ status, result }) => (
      <ListaPerfilesCard
        status={status}
        result={result}
        onSelectPerfil={({ id, nombre }) => {
          agent.addMessage({
            id: crypto.randomUUID(),
            role: "user",
            content: `Rankea los candidatos para el perfil "${nombre}" (ID: ${id})`,
          });
          agent.runAgent();
        }}
      />
    ),
  });

  // ── Resto de tools backend: pasos de proceso, sin exponer args/result ────
  useRenderTool({
    name: "obtener_requisitos_perfil",
    render: ({ status }) => <ProcessStep toolName="obtener_requisitos_perfil" status={status} />,
  });
  useRenderTool({
    name: "descargar_hojas_de_vida",
    render: ({ status }) => <ProcessStep toolName="descargar_hojas_de_vida" status={status} />,
  });
  useRenderTool({
    name: "analisis_cvs",
    render: ({ status }) => <ProcessStep toolName="analisis_cvs" status={status} />,
  });

  // Red de seguridad: cualquier tool futura sin mapear no muestra nada
  useRenderTool({ name: "*", render: () => <></> });

  return (
    <div className="h-screen flex flex-col">
      <div className="text-xl font-bold p-4">ANÁLISIS DE HOJAS DE VIDA</div>
      <div className="flex-1">
        <CopilotChat
          agentId="reclutamiento"
          labels={{
            welcomeMessageText: "Hola, soy tu asistente. ¿En qué te ayudo hoy?",
            chatInputPlaceholder: "Escribe tu consulta...",
          }}
          input={{
            sendButton: CustomSendButton,
          }}
        />
      </div>
    </div>
  );
}

function CustomSendButton({
  onClick,
  disabled,
}: {
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="bg-[#223b8f] rounded-lg p-2 text-white shadow-md hover:bg-[#223b8f] disabled:bg-indigo-200 disabled:shadow-none"
    >
      <SendHorizontal className="h-5 w-5" />
    </button>
  );
}