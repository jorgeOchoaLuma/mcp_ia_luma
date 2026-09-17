"use client";

import { useState } from "react";
import { CopilotChat, useComponent, useHumanInTheLoop, useAgent } from "@copilotkit/react-core/v2";
import { GroupPickerCard, GroupPickerCardProps } from "@/components/group-picker-card";
import { TemplatePickerCard, TemplatePickerCardProps } from "@/components/template-picker-card";
import { ProjectSummaryCard, ProjectSummaryCardProps } from "@/components/project-summary-card";
import { useProjectSuggestions } from "@/hooks/useProjectSuggestions";
import { SendHorizontal } from "lucide-react"; // 👈 nuevo import

const AGENT_ID = "agent_projects"; // debe coincidir con el name del LlmAgent / la config del runtime

export default function Page() {
  useProjectSuggestions();

  useHumanInTheLoop({
    name: "groupPicker",
    description:
      "Muestra la lista de grupos de proyectos disponibles para que el usuario elija uno. Úsalo en vez de listar los grupos en texto. El resultado es un JSON con el id y name del grupo elegido.",
    parameters: GroupPickerCardProps,
    render: ({ args, respond, status }) => {
      if (status === "complete") {
        return <div className="text-sm text-gray-500 italic">Grupo seleccionado ✓</div>;
      }
      return (
        <GroupPickerCard
          groups={args.groups}
          disabled={status !== "executing"}
          onSelect={(group) => respond?.(JSON.stringify(group))}
        />
      );
    },
  });

  useHumanInTheLoop({
    name: "templatePicker",
    description:
      "Muestra la lista de plantillas de proyecto disponibles para que el usuario elija una. Úsalo en vez de listarlas en texto. El resultado es un JSON con el id y name de la plantilla elegida.",
    parameters: TemplatePickerCardProps,
    render: ({ args, respond, status }) => {
      if (status === "complete") {
        return <div className="text-sm text-gray-500 italic">Plantilla seleccionada ✓</div>;
      }
      return (
        <TemplatePickerCard
          templates={args.templates}
          disabled={status !== "executing"}
          onSelect={(template) => respond?.(JSON.stringify(template))}
        />
      );
    },
  });

  useComponent({
    name: "projectSummary",
    description:
      "Muestra un resumen del proyecto recién creado en Zoho Projects, con link directo. Úsalo justo después de crear el proyecto exitosamente.",
    parameters: ProjectSummaryCardProps,
    render: ProjectSummaryCard,
  });

  return (
    <main>
      <div className="flex items-center justify-between px-4 py-3">
        <h1 className="font-bold">Gestión de Proyectos Luma Cloud</h1>
        <CrearProyectoButton />
      </div>
      <CopilotChat
        agentId={AGENT_ID}
        labels={{
          title: "Proyectos Luma Cloud",
          welcomeMessageText:
            "Hola, soy tu asistente de Zoho Projects. Puedo crear proyectos y tareas en tu portal, ¿en qué te ayudo hoy?",
          chatInputPlaceholder: "Escribe tu consulta...",
        }}
        input={{
          sendButton: CustomSendButton,
        }}
      />
    </main>
  );
}

function CrearProyectoButton() {
  const { agent } = useAgent({ agentId: AGENT_ID });
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (!agent) return;
    setLoading(true);
    agent.addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: "crear proyecto",
    });
    await agent.runAgent();
    setLoading(false);
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading || !agent}
      className="flex items-center gap-2 rounded-full bg-blue-900 px-4 py-2 font-semibold text-white hover:bg-blue-900 disabled:opacity-50"
    >
      <span>+</span> Crear proyecto
    </button>
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