"use client";

import { useState } from "react";
import { CopilotChat, useComponent, useAgent } from "@copilotkit/react-core/v2";
import {
  EfemeridesByCategory,
  EfemeridesByCategoryProps,
} from "@/app/components/efemerides-card";
import { SendHorizontal } from "lucide-react";

const AGENT_ID = "efemerides_agent"; // debe coincidir con el name del LlmAgent

export default function Page() {
  // Registra el tool que el agente llama para mostrar las efemérides.
  // El name AQUÍ debe ser idéntico al que usa `_GENERATIVE_UI_INSTRUCTION`
  // en main.py: "efemerides_card" (sin guión, con guión bajo).
  useComponent({
    name: "efemerides_card",
    description:
      "Muestra una lista de efemérides organizadas por categoría (Nacional Colombia, Internacional, Industria). Llama siempre a este tool en lugar de responder el JSON como texto.",
    parameters: EfemeridesByCategoryProps,
    render: EfemeridesByCategory,
  });

  return (
    <main>
      <div className="flex items-center justify-between px-4 py-3">
        <h1 className="font-bold">Efemérides Luma Cloud</h1>
        <BuscarEfemeridesButton />
      </div>
      <CopilotChat
        labels={{
          welcomeMessageText:
            "Hola, soy tu asistente de búsqueda de fechas importantes. Puedo buscar aniversarios, eventos históricos y hitos de cualquier tema o mes, ¿qué quieres consultar hoy?",
          chatInputPlaceholder: "Ej: efemérides de agosto sobre ciberseguridad...",
        }}
        input={{
          sendButton: CustomSendButton,
        }}
      />
    </main>
  );
}

function BuscarEfemeridesButton() {
  const { agent } = useAgent({ agentId: AGENT_ID });
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (!agent) return;
    setLoading(true);
    agent.addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: "Busca las efemérides del mes actual",
    });
    await agent.runAgent();
    setLoading(false);
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="rounded-md bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
    >
      {loading ? "Buscando..." : "Buscar efemérides del mes"}
    </button>
  );
}

function CustomSendButton(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      className="bg-[#223b8f] rounded-lg p-2 text-white shadow-md hover:bg-[#223b8f] disabled:bg-indigo-200 disabled:shadow-none"
    >
      <SendHorizontal className="h-5 w-5" />
    </button>
  );
}
