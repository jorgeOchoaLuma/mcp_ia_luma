import { z } from "zod";

// Una sola plantilla (viene de get_project_templates)
const ProjectTemplateSchema = z.object({
  id: z.string().describe("ID de la plantilla de proyecto en Zoho"),
  name: z.string().describe("Nombre visible de la plantilla"),
});

export const TemplatePickerCardProps = z.object({
  templates: z
    .array(ProjectTemplateSchema)
    .describe("Lista de plantillas de proyecto disponibles para elegir"),
});

export type TemplatePickerCardProps = z.infer<typeof TemplatePickerCardProps>;

type TemplatePickerCardComponentProps = TemplatePickerCardProps & {
  onSelect: (template: { id: string; name: string }) => void;
  disabled?: boolean;
  selectedId?: string | null;
};

export function TemplatePickerCard({
  templates,
  onSelect,
  disabled,
  selectedId,
}: TemplatePickerCardComponentProps) {
  const items = templates ?? [];

  return (
    <div className="rounded-lg border bg-white p-3 space-y-2 max-w-md">
      <div className="font-semibold text-sm text-gray-800">
        ¿Con qué plantilla quieres crear el proyecto?
      </div>
      <div className="flex flex-col gap-2">
        {items.map((template) => (
          <button
            key={template.id}
            disabled={disabled}
            onClick={() => onSelect(template)}
            className={`text-left rounded border px-3 py-2 text-sm transition-colors ${
              selectedId === template.id
                ? "bg-blue-50 border-blue-300"
                : disabled
                ? "opacity-50 cursor-not-allowed"
                : "hover:bg-blue-50 hover:border-blue-300"
            }`}
          >
            {template.name}
          </button>
        ))}
      </div>
      {items.length === 0 && (
        <div className="text-sm text-gray-500">
          No hay plantillas configuradas.
        </div>
      )}
    </div>
  );
}
