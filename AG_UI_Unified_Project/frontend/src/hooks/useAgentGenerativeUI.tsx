"use client";

import React from "react";
import { z } from "zod";
import {
  useComponent,
  useHumanInTheLoop,
  useRenderTool,
  useAgent,
  useConfigureSuggestions,
} from "@copilotkit/react-core/v2";
import { VisualAidGallery, VisualAidGalleryProps } from "@/components/video/VisualAids";
import { useAyudasVisualesConfig } from "@/components/video/ayudas-visuales-config";
import { useHideToolOutputs } from "@/components/video/hide-tool-outputs";
import { GroupPickerCard, GroupPickerCardProps } from "@/components/projects/group-picker-card";
import { TemplatePickerCard, TemplatePickerCardProps } from "@/components/projects/template-picker-card";
import { ProjectSummaryCard, ProjectSummaryCardProps } from "@/components/projects/project-summary-card";
import { EfemeridesByCategory, EfemeridesByCategoryProps } from "@/components/efemerides/efemerides-card";
import { CandidateRankingCard } from "@/components/analisis-hv/CandidateRankingCard";
import { ListaPerfilesCard } from "@/components/analisis-hv/ListaPerfilesCard";
import { ClipboardList, Download, BrainCircuit, Check } from "lucide-react";

// Pasos legibles para el análisis de hojas de vida
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
    <div className="flex items-center gap-2 py-1.5 text-sm text-gray-300">
      <Icon
        className={`h-4 w-4 ${
          status !== "complete" ? "animate-pulse text-blue-400" : "text-emerald-400"
        }`}
      />
      <span>{step.label}</span>
      {status === "complete" && <span className="text-xs text-emerald-400 font-medium">Listo</span>}
    </div>
  );
}

export function useAgentGenerativeUI(selectedAgent: string) {
  // -------------------------------------------------------------
  // 1. VIDEO PRODUCER
  // -------------------------------------------------------------
  useComponent({
    name: "visualAidGallery",
    description: "Muestra todas las ayudas visuales generadas para el video, en una sola galería.",
    parameters: VisualAidGalleryProps,
    render: VisualAidGallery,
  });

  useAyudasVisualesConfig();
  useHideToolOutputs();

  // -------------------------------------------------------------
  // 2. PROJECTS (ZOHO PROJECTS)
  // -------------------------------------------------------------
  useHumanInTheLoop({
    name: "groupPicker",
    description:
      "Muestra la lista de grupos de proyectos disponibles para que el usuario elija uno. Úsalo en vez de listar los grupos en texto. El resultado es un JSON con el id y name del grupo elegido.",
    parameters: GroupPickerCardProps,
    render: ({ args, respond, status }) => {
      if (status === "complete") {
        return <div className="text-sm text-gray-400 italic">Grupo seleccionado ✓</div>;
      }
      return (
        <GroupPickerCard
          groups={args.groups || []}
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
        return <div className="text-sm text-gray-400 italic">Plantilla seleccionada ✓</div>;
      }
      return (
        <TemplatePickerCard
          templates={args.templates || []}
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

  // -------------------------------------------------------------
  // 3. EFEMÉRIDES
  // -------------------------------------------------------------
  useComponent({
    name: "efemerides_card",
    description:
      "Muestra una lista de efemérides organizadas por categoría (Nacional Colombia, Internacional, Industria). Llama siempre a este tool en lugar de responder el JSON como texto.",
    parameters: EfemeridesByCategoryProps,
    render: EfemeridesByCategory,
  });

  // -------------------------------------------------------------
  // 4. ANÁLISIS HV / RECLUTAMIENTO
  // -------------------------------------------------------------
  const { agent: hvAgent } = useAgent({ agentId: "analisis_hv" });

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

  useRenderTool({
    name: "listar_perfiles",
    parameters: z.object({
      perfiles: z
        .array(
          z.object({
            id: z.string(),
            nombre: z.string(),
          })
        )
        .describe("Lista de perfiles disponibles para reclutamiento"),
    }),
    render: ({ status, result }) => (
      <ListaPerfilesCard
        status={status}
        result={result}
        onSelectPerfil={({ id, nombre }) => {
          if (!hvAgent) return;
          hvAgent.addMessage({
            id: crypto.randomUUID(),
            role: "user",
            content: `Rankea los candidatos para el perfil "${nombre}" (ID: ${id})`,
          });
          hvAgent.runAgent();
        }}
      />
    ),
  });

  const processSchema = z.object({}).passthrough();
  useRenderTool({
    name: "obtener_requisitos_perfil",
    parameters: processSchema,
    render: ({ status }) => <ProcessStep toolName="obtener_requisitos_perfil" status={status} />,
  });
  useRenderTool({
    name: "descargar_hojas_de_vida",
    parameters: processSchema,
    render: ({ status }) => <ProcessStep toolName="descargar_hojas_de_vida" status={status} />,
  });
  useRenderTool({
    name: "analisis_cvs",
    parameters: processSchema,
    render: ({ status }) => <ProcessStep toolName="analisis_cvs" status={status} />,
  });

  // -------------------------------------------------------------
  // 5. SUGGESTIONS SEGÚN AGENTE
  // -------------------------------------------------------------
  const suggestions = React.useMemo(() => {
    switch (selectedAgent) {
      case "projects":
        return [
          { title: "Crear una tarea", message: "Quiero crear una tarea nueva en Zoho Projects" },
          { title: "Crear Proyecto", message: "Quiero crear un nuevo proyecto" },
          { title: "Crear Lista de Tareas", message: "Quiero crear una nueva lista de tareas" },
        ];
      case "analisis_hv":
        return [
          { title: "Ver perfiles abiertos", message: "Muéstrame los perfiles abiertos" },
          { title: "Rankear candidatos", message: "Rankea los candidatos para el perfil que me interesa" },
        ];
      case "efemerides":
        return [
          { title: "Efemérides del mes", message: "Busca las efemérides del mes actual" },
          { title: "Efemérides de tecnología", message: "Efemérides sobre ciberseguridad y tecnología este mes" },
        ];
      case "video_producer":
        return [
          { title: "Generar guion y visuales", message: "Crea un guion para video y genera ayudas visuales a partir de este tema:" },
        ];
      default:
        return [];
    }
  }, [selectedAgent]);

  useConfigureSuggestions({
    suggestions,
    available: suggestions.length > 0 ? "always" : "disabled",
  });
}
