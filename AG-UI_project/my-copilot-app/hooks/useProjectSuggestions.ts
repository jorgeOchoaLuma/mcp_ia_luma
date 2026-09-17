// hooks/useProjectSuggestions.ts
import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export function useProjectSuggestions() {
  useConfigureSuggestions({
    suggestions: [
      { title: "Crear una tarea", message: "Quiero crear una tarea nueva" },
      // { title: "Ver mis proyectos", message: "Muéstrame la lista de proyectos existentes" },
      { title: "Crear Proyecto", message: "Quiero crear un nuevo proyecto" },
      { title: "Crear Lista de Tareas", message: "Quiero crear una nueva lista de tareas" },
    ],
    available: "always",
  });
}