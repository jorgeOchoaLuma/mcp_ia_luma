"use client";

import { useState, useEffect, useRef } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotChat } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";
import { Mic, MicOff, Video, FileText, Globe, Gavel, Megaphone } from "lucide-react";

const AGENTS = [
  { id: "video_producer", name: "Productor de Video", icon: Video },
  { id: "transcription", name: "Transcripción", icon: FileText },
  { id: "url_expert", name: "Experto Luma (Web)", icon: Globe },
  { id: "licitaciones", name: "Licitaciones", icon: Gavel },
  { id: "campaign_expert", name: "Experto en Campañas", icon: Megaphone },
];

function MicButton() {
  const { appendMessage } = useCopilotChat();
  const [isRecording, setIsRecording] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        appendMessage(new TextMessage({ content: transcript, role: Role.User }));
      }
    };

    recognition.onend = () => setIsRecording(false);
    recognition.onerror = () => setIsRecording(false);

    recognitionRef.current = recognition;
  }, [appendMessage]);

  const toggle = () => {
    if (!recognitionRef.current) return;
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  if (!supported) return null;

  return (
    <button
      onClick={toggle}
      className={`fixed bottom-24 right-6 z-50 p-4 rounded-full shadow-lg transition-all ${
        isRecording ? "bg-red-500 scale-110" : "bg-indigo-600 hover:bg-indigo-700"
      }`}
    >
      {isRecording ? <MicOff className="text-white" /> : <Mic className="text-white" />}
    </button>
  );
}

export default function Page() {
  const [selectedAgent, setSelectedAgent] = useState(AGENTS[0].id);

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Panel de Agentes Unificados
          </h1>
          <p className="text-gray-400 mt-2">Selecciona un agente para comenzar la interacción.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setSelectedAgent(agent.id)}
              className={`p-6 rounded-xl border-2 flex items-center gap-4 transition-all ${
                selectedAgent === agent.id
                  ? "border-blue-500 bg-blue-500/10"
                  : "border-gray-800 bg-gray-800/50 hover:border-gray-700"
              }`}
            >
              <agent.icon className={selectedAgent === agent.id ? "text-blue-400" : "text-gray-500"} />
              <div className="text-left">
                <p className="font-semibold">{agent.name}</p>
                <p className="text-xs text-gray-500">{agent.id}</p>
              </div>
            </button>
          ))}
        </div>

        <div className="bg-gray-800/30 rounded-2xl p-8 border border-gray-800">
          <h2 className="text-xl font-semibold mb-4 capitalize">Agente Activo: {selectedAgent.replace("_", " ")}</h2>
          <p className="text-gray-400">Interactúa con el agente a través del sidebar a la derecha.</p>
        </div>
      </div>

      <CopilotSidebar agent={selectedAgent} defaultOpen />
      <MicButton />
    </main>
  );
}
