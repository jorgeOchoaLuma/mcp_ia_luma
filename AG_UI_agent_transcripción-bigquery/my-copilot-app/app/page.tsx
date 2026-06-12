"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotChat } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";

const SAVE_KEYWORDS = ["ya terminé", "guarda", "guardar", "fin", "terminar", "save", "done"];

function isSaveKeyword(text: string): boolean {
  const lower = text.toLowerCase().trim();
  return SAVE_KEYWORDS.some((kw) => lower.includes(kw));
}

function MicButton() {
  const { appendMessage } = useCopilotChat();
  const [isRecording, setIsRecording]     = useState(false);
  const [supported, setSupported]         = useState(true);
  const [liveText, setLiveText]           = useState("");   // ← texto visible en tiempo real
  const recognitionRef                    = useRef<any>(null);
  const accumulatedRef                    = useRef<string[]>([]);

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
    recognition.lang            = "es-ES";
    recognition.interimResults  = true;    // ← resultados parciales para mostrar en tiempo real
    recognition.continuous      = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      let interimTranscript = "";
      let finalTranscript   = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript.trim() + " ";
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      // Mostrar texto en vivo (acumulado + parcial actual)
      const accumulated = accumulatedRef.current.join(" ");
      setLiveText(
        [accumulated, finalTranscript, interimTranscript]
          .filter(Boolean)
          .join(" ")
          .trim()
      );

      if (finalTranscript.trim()) {
        if (isSaveKeyword(finalTranscript)) {
          // Keyword detectada → mandar todo al agente y limpiar
          const full = [...accumulatedRef.current, finalTranscript.trim()].join(" ");
          accumulatedRef.current = [];
          setLiveText("");
          sendToAgent(full);
          recognition.stop();
          setIsRecording(false);
        } else {
          // Fragmento final → acumular
          accumulatedRef.current.push(finalTranscript.trim());
        }
      }
    };

    recognition.onend = () => {
      // Si sigue grabando (continuous), reiniciar
      if (recognitionRef.current?._active) {
        try { recognition.start(); } catch (_) {}
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

    recognitionRef.current = recognition;
  }, [sendToAgent]);

  const toggle = () => {
    const rec = recognitionRef.current;
    if (!rec) return;

    if (isRecording) {
      // Detener — mandar lo acumulado con keyword "guardar"
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
      {/* Burbuja de transcripción en tiempo real */}
      {isRecording && liveText && (
        <div
          style={{
            position:     "fixed",
            bottom:       "152px",
            right:        "24px",
            zIndex:       9998,
            maxWidth:     "320px",
            background:   "rgba(30,30,40,0.92)",
            color:        "#f1f5f9",
            borderRadius: "12px",
            padding:      "10px 14px",
            fontSize:     "13px",
            lineHeight:   "1.5",
            boxShadow:    "0 4px 20px rgba(0,0,0,0.4)",
            backdropFilter: "blur(6px)",
            border:       "1px solid rgba(99,102,241,0.4)",
            wordBreak:    "break-word",
          }}
        >
          <div style={{ color: "#818cf8", fontSize: "11px", marginBottom: "4px", fontWeight: 600 }}>
            🎙️ Transcribiendo...
          </div>
          {liveText}
        </div>
      )}

      {/* Indicador de grabación cuando no hay texto aún */}
      {isRecording && !liveText && (
        <div
          style={{
            position:     "fixed",
            bottom:       "152px",
            right:        "24px",
            zIndex:       9998,
            background:   "rgba(30,30,40,0.92)",
            color:        "#818cf8",
            borderRadius: "12px",
            padding:      "8px 14px",
            fontSize:     "12px",
            boxShadow:    "0 4px 20px rgba(0,0,0,0.4)",
            border:       "1px solid rgba(99,102,241,0.4)",
          }}
        >
          🎙️ Escuchando...
        </div>
      )}

      {/* Botón mic */}
      <button
        onClick={toggle}
        title={isRecording ? "Click para detener y guardar" : "Click para hablar"}
        style={{
          position:     "fixed",
          bottom:       "88px",
          right:        "24px",
          zIndex:       9999,
          width:        "52px",
          height:       "52px",
          borderRadius: "50%",
          background:   isRecording ? "#ef4444" : "#6366f1",
          border:       "none",
          cursor:       "pointer",
          fontSize:     "22px",
          boxShadow:    "0 4px 14px rgba(0,0,0,0.35)",
          transition:   "background 0.2s, transform 0.1s",
          transform:    isRecording ? "scale(1.1)" : "scale(1)",
        }}
      >
        {isRecording ? "⏹️" : "🎤"}
      </button>
    </>
  );
}

export default function Page() {
  return (
    <main>
      <h1>Voice Transcription</h1>
      <CopilotSidebar defaultOpen>
        <MicButton />
      </CopilotSidebar>
    </main>
  );
}
