"use client";

import { SendHorizontal } from "lucide-react";
import { CopilotChat, useComponent } from "@copilotkit/react-core/v2";

import { VisualAidGallery, VisualAidGalleryProps } from "@/app/components/VisualAids";
import { useAyudasVisualesConfig } from "@/app/components/ayudas-visuales-config";
import { useHideToolOutputs } from "@/app/components/hide-tool-outputs";

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

export default function App() {

  useComponent({
    name: "visualAidGallery",
    description: "Muestra todas las ayudas visuales generadas para el video, en una sola galería.",
    parameters: VisualAidGalleryProps,
    render: VisualAidGallery,
  });

  useAyudasVisualesConfig();
  useHideToolOutputs();

  return (
    <CopilotChat
      agentId="my_agent"
      labels={{
        welcomeMessageText: "Hola, soy un experto en generar guiones y ayudas visuales (imágenes) en relación al texto que me compartas",
        chatInputPlaceholder: "Pega el texto, para generar el guion y las imágenes.",
      }}
      input={{
        sendButton: CustomSendButton,
      }}
    />
  );
}