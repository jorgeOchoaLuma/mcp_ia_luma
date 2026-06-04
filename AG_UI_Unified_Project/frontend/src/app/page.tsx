"use client";

import { useState, useEffect, useRef } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotChat } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";
import {
  Mic,
  MicOff,
  Video,
  FileText,
  Globe,
  Gavel,
  Megaphone,
  Search,
  FolderKanban,
  Users,
  Paperclip,
} from "lucide-react";

const AGENTS = [
  { id: "video_producer", name: "Productor de Video", icon: Video, source: "AG_UI_agent_asistentente_video" },
  { id: "url_expert", name: "Experto Luma (Web)", icon: Globe, source: "AG_UI_agente_url_contexto_luma" },
  { id: "campaign_expert", name: "Experto en Campañas", icon: Megaphone, source: "AU_UI_Agente_campana" },
  { id: "resumen_reuniones", name: "Resumen de Reuniones", icon: Users, source: "AG_UI_agente_resumen_reuniones" },
  { id: "projects", name: "Proyectos Zoho", icon: FolderKanban, source: "AG-UI_project" },
  { id: "transcription", name: "Transcripción", icon: FileText, source: "AG_UI_agent_transcripción" },
  { id: "licitaciones", name: "Licitaciones", icon: Gavel, source: "—" },
  { id: "investigacion_fuentes", name: "Investigación de Fuentes", icon: Search, source: "AG-UI_investigacion_fuentes" },
];

function UploadButton() {
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<string | null>(null);
  const { appendMessage } = useCopilotChat();

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setUploaded(file.name);
      appendMessage(
        new TextMessage({
          role: Role.User,
          content: `El usuario ha subido un archivo. Procésalo y genera un resumen completo.\n\nDetalles del archivo:\n- Nombre: ${file.name}\n- Tipo: ${file.type}\n- URI en GCS: ${data.url}\n\nPor favor analiza este archivo usando la URI GCS proporcionada.`,
        })
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      alert("Error al subir: " + message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <button
      type="button"
      disabled={uploading}
      className={`fixed bottom-36 right-6 z-50 p-4 rounded-full shadow-lg transition-all ${
        uploading ? "bg-gray-600 cursor-wait" : "bg-blue-600 hover:bg-blue-700"
      }`}
      title="Subir audio, video, PDF o imagen"
    >
      <label className="cursor-pointer flex items-center justify-center">
        <Paperclip className="text-white" />
        <input
          type="file"
          accept="audio/*,video/*,image/*,.pdf"
          onChange={handleFile}
          disabled={uploading}
          className="hidden"
        />
      </label>
      {uploaded && (
        <span className="absolute -top-8 right-0 text-xs bg-green-900 text-green-200 px-2 py-1 rounded whitespace-nowrap">
          ✓ {uploaded}
        </span>
      )}
    </button>
  );
}

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
      type="button"
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
  const active = AGENTS.find((a) => a.id === selectedAgent);

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Panel de Agentes Unificados
          </h1>
          <p className="text-gray-400 mt-2">
            Un frontend → <code className="text-gray-300">/api/copilotkit</code> → backend{" "}
            <code className="text-gray-300">:8000/&lt;agent_id&gt;</code>
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              type="button"
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
                <p className="text-xs text-gray-600 mt-1">← {agent.source}</p>
              </div>
            </button>
          ))}
        </div>

        <div className="bg-gray-800/30 rounded-2xl p-8 border border-gray-800">
          <h2 className="text-xl font-semibold mb-2">Agente activo: {active?.name}</h2>
          <p className="text-gray-400 text-sm font-mono mb-2">
            Backend: http://localhost:8000/{selectedAgent}
          </p>
          <p className="text-gray-500 text-sm">
            CopilotKit usa el id <strong className="text-gray-300">{selectedAgent}</strong> en el sidebar.
            {selectedAgent === "resumen_reuniones" && " Usa el clip 📎 para subir archivos a GCS."}
          </p>
        </div>
      </div>

      <CopilotSidebar agent={selectedAgent} defaultOpen />
      {selectedAgent === "resumen_reuniones" && <UploadButton />}
      <MicButton />
    </main>
  );
}
