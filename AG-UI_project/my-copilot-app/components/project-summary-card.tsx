"use client";
import { z } from "zod";

export const ProjectSummaryCardProps = z.object({
  project_name: z.string().describe("Nombre del proyecto creado"),
  project_id: z.string().describe("ID del proyecto en Zoho Projects"),
  portal_id: z.string().describe("ID del portal de Zoho (lumasas)"),
  group_name: z.string().describe("Nombre del grupo de proyectos usado"),
  template_name: z
    .string()
    .optional()
    .describe("Nombre de la plantilla usada, si aplica"),
  start_date: z.string().optional().describe("Fecha de inicio del proyecto"),
  end_date: z.string().optional().describe("Fecha de fin del proyecto"),
});

export type ProjectSummaryCardProps = z.infer<typeof ProjectSummaryCardProps>;

export function ProjectSummaryCard({
  project_name,
  project_id,
  portal_id,
  group_name,
  template_name,
  start_date,
  end_date,
}: ProjectSummaryCardProps) {
  const projectUrl = `https://projects.zoho.com/portal/${portal_id}#projects/${project_id}`;

  return (
    <div className="rounded-lg border bg-white p-3 space-y-2 max-w-md">
      <div className="flex items-center gap-2">
        <span className="text-green-600">✓</span>
        <div className="font-semibold">{project_name}</div>
      </div>
      <div className="rounded border p-2 text-sm space-y-1">
        <div>
          <span className="text-gray-500">Grupo: </span>
          {group_name}
        </div>
        {template_name && (
          <div>
            <span className="text-gray-500">Plantilla: </span>
            {template_name}
          </div>
        )}
        {(start_date || end_date) && (
          <div>
            <span className="text-gray-500">Fechas: </span>
            {start_date ?? "—"} → {end_date ?? "—"}
          </div>
        )}
        <div className="text-xs text-gray-400">ID: {project_id}</div>
      </div>
      <a
        href={projectUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block text-sm font-medium text-blue-600 hover:underline"
      >
        Abrir en Zoho Projects →
      </a>
    </div>
  );
}
