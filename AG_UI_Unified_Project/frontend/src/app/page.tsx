"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useSelectedAgent } from "./agent-provider";
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
  LifeBuoy,
  Briefcase,
  Calendar,
  Sparkles,
  Layers,
} from "lucide-react";
import { useAgentGenerativeUI } from "@/hooks/useAgentGenerativeUI";
import Dashboard from "@/components/deepsearch/Dashboard";

const SAVE_KEYWORDS = ["ya terminé", "guarda", "guardar", "fin", "terminar", "save", "done"];

function isSaveKeyword(text: string): boolean {
  const lower = text.toLowerCase().trim();
  return SAVE_KEYWORDS.some((kw) => lower.includes(kw));
}

const AGENTS = [
  { id: "video_producer", name: "Productor de Video", icon: Video, category: "Creativo", source: "AG_UI_agent_asistentente_video" },
  { id: "projects", name: "Proyectos Zoho", icon: FolderKanban, category: "Gestión", source: "AG-UI_project" },
  { id: "efemerides", name: "Efemérides", icon: Calendar, category: "Contenido", source: "AG_UI_efemerides" },
  { id: "deepsearch", name: "Deep Research & Content", icon: Sparkles, category: "Investigación", source: "AG-UI_deepsearch_recomendacioens" },
  { id: "analisis_hv", name: "Análisis HV / Reclutamiento", icon: Briefcase, category: "RRHH", source: "AG-UI_AnalisisHV" },
  { id: "resumen_reuniones", name: "Resumen de Reuniones", icon: Users, category: "Productividad", source: "AG_UI_agente_resumen_reuniones" },
  { id: "transcription", name: "Transcripción", icon: FileText, category: "Voz", source: "AG_UI_agent_transcripción / bigquery" },
  { id: "url_expert", name: "Experto Luma (Web)", icon: Globe, category: "Contexto", source: "AG_UI_agente_url_contexto_luma" },
  { id: "soporte", name: "Soporte Luma", icon: LifeBuoy, category: "Atención", source: "AG-UI_Agente_soporte" },
  { id: "campaign_expert", name: "Experto en Campañas", icon: Megaphone, category: "Marketing", source: "AU_UI_Agente_campana" },
  { id: "investigacion_fuentes", name: "Investigación de Fuentes", icon: Search, category: "Investigación", source: "AG-UI_investigacion_fuentes" },
  { id: "licitaciones", name: "Licitaciones", icon: Gavel, category: "Legal", source: "—" },
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
          content: `Genera un resumen completo de la reunión del archivo "${file.name}".\n\n[METADATA:uri=${data.url},mime=${data.mimeType || file.type}]`,
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
  const [liveText, setLiveText] = useState("");
  const recognitionRef = useRef<any>(null);
  const accumulatedRef = useRef<string[]>([]);

  const sendToAgent = useCallback(
    (text: string) => {
      appendMessage(new TextMessage({ content: text, role: Role.User }));
    },
    [appendMessage]
  );

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
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript.trim() + " ";
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      const accumulated = accumulatedRef.current.join(" ");
      setLiveText(
        [accumulated, finalTranscript, interimTranscript].filter(Boolean).join(" ").trim()
      );

      if (finalTranscript.trim()) {
        if (isSaveKeyword(finalTranscript)) {
          const full = [...accumulatedRef.current, finalTranscript.trim()].join(" ");
          accumulatedRef.current = [];
          setLiveText("");
          sendToAgent(full);
          recognition.stop();
          setIsRecording(false);
        } else {
          accumulatedRef.current.push(finalTranscript.trim());
        }
      }
    };

    recognition.onend = () => {
      if (recognitionRef.current?._active) {
        try {
          recognition.start();
        } catch {
          /* ignore */
        }
      } else {
        setIsRecording(false);
      }
    };

    recognition.onerror = (e: any) => {
      if (e.error !== "no-speech") {
        setIsRecording(false);
        recognitionRef.current._active = false;
      }
    };

    recognition.recognition = recognition;
  }, [sendToAgent]);

  const toggle = () => {
    const rec = recognitionRef.current;
    if (!rec) return;

    if (isRecording) {
      rec._active = false;
      rec.stop();
      setIsRecording(false);
      if (accumulatedRef.current.length > 0) {
        const full = accumulatedRef.current.join(" ") + " guardar";
        accumulatedRef.current = [];
        setLiveText("");
        sendToAgent(full);
      }
    } else {
      accumulatedRef.current = [];
      setLiveText("");
      rec._active = true;
      rec.start();
      setIsRecording(true);
    }
  };

  if (!supported) return null;

  return (
    <>
      {isRecording && liveText && (
        <div className="fixed bottom-40 right-6 z-50 max-w-xs bg-gray-900/95 text-gray-100 rounded-xl p-3 text-sm border border-indigo-500/40 shadow-lg">
          <div className="text-indigo-400 text-xs font-semibold mb-1">🎙️ Transcribiendo...</div>
          {liveText}
        </div>
      )}
      {isRecording && !liveText && (
        <div className="fixed bottom-40 right-6 z-50 bg-gray-900/95 text-indigo-400 rounded-xl px-3 py-2 text-xs border border-indigo-500/40">
          🎙️ Escuchando...
        </div>
      )}
      <button
        type="button"
        onClick={toggle}
        title={isRecording ? "Detener y guardar" : "Hablar"}
        className={`fixed bottom-24 right-6 z-50 p-4 rounded-full shadow-lg transition-all ${
          isRecording ? "bg-red-500 scale-110" : "bg-indigo-600 hover:bg-indigo-700"
        }`}
      >
        {isRecording ? <MicOff className="text-white" /> : <Mic className="text-white" />}
      </button>
    </>
  );
}

export default function Page() {
  const { agent: selectedAgent, setAgent: setSelectedAgent } = useSelectedAgent();
  const active = AGENTS.find((a) => a.id === selectedAgent);

  // Activación de hooks Generative UI para todos los agentes
  useAgentGenerativeUI(selectedAgent);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Barra de Navegación de Agentes Superior */}
      <header className="sticky top-0 z-40 bg-gray-900/90 backdrop-blur-md border-b border-gray-800 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-md">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                Panel Unificado de Agentes Luma
                <span className="text-[10px] bg-blue-500/20 text-blue-300 font-semibold px-2 py-0.5 rounded-full border border-blue-500/30">
                  Gen UI
                </span>
              </h1>
              <p className="text-xs text-gray-400">
                Agente actual: <strong className="text-blue-400">{active?.name}</strong> ({selectedAgent})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-2xl no-scrollbar">
            {AGENTS.map((agent) => {
              const isSelected = selectedAgent === agent.id;
              const Icon = agent.icon;
              return (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => setSelectedAgent(agent.id)}
                  title={`${agent.name} — ${agent.source}`}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                    isSelected
                      ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                      : "bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 hover:text-white"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{agent.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Contenido Principal */}
      <div className="flex-1">
        {selectedAgent === "deepsearch" ? (
          /* Vista Dashboard Completo para Deep Research */
          <div className="h-[calc(100vh-65px)]">
            <Dashboard />
          </div>
        ) : (
          /* Vista General para los demás agentes */
          <main className="max-w-6xl mx-auto p-6 md:p-8">
            <div className="mb-8">
              <h2 className="text-3xl font-extrabold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                {active?.name}
              </h2>
              <p className="text-gray-400 text-sm mt-1">
                Servicio backend conectado: <code className="text-indigo-300 bg-gray-800 px-1.5 py-0.5 rounded font-mono text-xs">/api/copilotkit → :{selectedAgent}</code>
              </p>
            </div>

            {/* Grid de selección de agentes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {AGENTS.map((agent) => {
                const isSelected = selectedAgent === agent.id;
                const Icon = agent.icon;
                return (
                  <button
                    key={agent.id}
                    type="button"
                    onClick={() => setSelectedAgent(agent.id)}
                    className={`p-5 rounded-xl border text-left transition-all relative overflow-hidden group ${
                      isSelected
                        ? "border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/10"
                        : "border-gray-800 bg-gray-900/50 hover:border-gray-700 hover:bg-gray-800/50"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className={`p-2.5 rounded-lg ${isSelected ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 group-hover:text-white"}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-gray-800/70 text-gray-400 border border-gray-700/50">
                        {agent.category}
                      </span>
                    </div>
                    <p className="font-semibold text-sm text-gray-100 mb-1">{agent.name}</p>
                    <p className="text-xs text-gray-400 font-mono">{agent.id}</p>
                    <p className="text-[11px] text-gray-400 mt-2 truncate">← {agent.source}</p>
                  </button>
                );
              })}
            </div>

            {/* Card de información del agente activo */}
            <div className="bg-gray-900/70 rounded-2xl p-6 border border-gray-800 shadow-xl">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <h3 className="text-lg font-bold text-gray-200">Capacidades del Agente</h3>
              </div>
              <div className="text-gray-400 text-sm leading-relaxed space-y-2">
                {selectedAgent === "video_producer" && (
                  <p>Genera guiones y ayudas visuales interactivas. Incluye selector de relación de aspecto, estilo visual y renderizado de galería de imágenes mediante Gen UI.</p>
                )}
                {selectedAgent === "projects" && (
                  <p>Conexión directa con Zoho Projects mediante MCP. Permite crear proyectos, listas y tareas con Human-in-the-Loop para seleccionar grupos y plantillas dinámicamente.</p>
                )}
                {selectedAgent === "efemerides" && (
                  <p>Búsqueda inteligente de fechas y conmemoraciones nacionales, internacionales e industriales, presentadas en tarjetas temáticas clasificadas por categoría.</p>
                )}
                {selectedAgent === "analisis_hv" && (
                  <p>Conecta con Zoho Recruit para listar vacantes abiertas, descargar currículums y generar el ranking interactivo de candidatos con evidencia documental detallada.</p>
                )}
                {selectedAgent === "resumen_reuniones" && (
                  <p>Genera minutas estructuradas a partir de audios o videos. Utiliza el botón 📎 flotante para subir archivos a Google Cloud Storage.</p>
                )}
                {selectedAgent === "transcription" && (
                  <p>Transcripción de voz en tiempo real. Usa el micrófono flotante y di <em>"guardar"</em> al finalizar para persistir en BigQuery.</p>
                )}
                {selectedAgent === "url_expert" && (
                  <p>Consulta y contextualización en vivo sobre el sitio web y servicios de Luma Cloud.</p>
                )}
                {selectedAgent === "soporte" && (
                  <p>Asistencia técnica y resolución de incidencias de primer nivel para usuarios de Luma.</p>
                )}
                {selectedAgent === "campaign_expert" && (
                  <p>Planificación, estrategia y generación de copys para campañas comerciales y publicitarias.</p>
                )}
                {selectedAgent === "investigacion_fuentes" && (
                  <p>Búsqueda y contrastación de datos a través de múltiples fuentes de información confiables.</p>
                )}
                {selectedAgent === "licitaciones" && (
                  <p>Análisis de pliegos y requerimientos para procesos licitatorios y compras públicas.</p>
                )}
              </div>
            </div>
          </main>
        )}
      </div>

      {/* Sidebar de CopilotKit para los agentes regulares */}
      {selectedAgent !== "deepsearch" && (
        <CopilotSidebar defaultOpen />
      )}

      {selectedAgent === "resumen_reuniones" && <UploadButton />}
      {selectedAgent === "transcription" && <MicButton />}
    </div>
  );
}
