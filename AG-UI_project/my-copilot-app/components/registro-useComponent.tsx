// Agrega esto en tu page.tsx (donde montas <CopilotChat />), junto a tus
// otros useComponent() como el de SourcesCard.

import { useComponent } from "@copilotkit/react-core/v2";

import { GroupPickerCard, GroupPickerCardProps } from "@/components/group-picker-card";
import { TemplatePickerCard, TemplatePickerCardProps } from "@/components/template-picker-card";
import { ProjectSummaryCard, ProjectSummaryCardProps } from "@/components/project-summary-card";

// 🪁 Muestra los grupos de get_project_groups como opciones seleccionables
useComponent({
  name: "groupPicker",
  description:
    "Muestra la lista de grupos de proyectos disponibles para que el usuario elija uno, en vez de responder en texto.",
  parameters: GroupPickerCardProps,
  render: GroupPickerCard,
});

// 🪁 Muestra las plantillas de get_project_templates como opciones seleccionables
useComponent({
  name: "templatePicker",
  description:
    "Muestra la lista de plantillas de proyecto disponibles para que el usuario elija una, en vez de responder en texto.",
  parameters: TemplatePickerCardProps,
  render: TemplatePickerCard,
});

// 🪁 Confirma la creación del proyecto con una tarjeta resumen
useComponent({
  name: "projectSummary",
  description:
    "Muestra un resumen del proyecto recién creado en Zoho Projects, con link directo. Úsalo justo después de crear el proyecto exitosamente.",
  parameters: ProjectSummaryCardProps,
  render: ProjectSummaryCard,
});
