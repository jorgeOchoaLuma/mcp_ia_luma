import { useConfigureSuggestions } from "@copilotkit/react-core/v2";

export function useReclutamientoSuggestions() {
    useConfigureSuggestions({
        suggestions: [
            { title: "Ver perfiles abiertos", message: "Muéstrame los perfiles abiertos" },
            { title: "Rankear candidatos", message: "Rankea los candidatos para el perfil que me interesa" },
        ],
        available: "always",
    });
}