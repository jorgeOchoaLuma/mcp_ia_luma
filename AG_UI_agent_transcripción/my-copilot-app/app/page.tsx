"use client";

import { useState, useEffect, useRef } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotChat } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";

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
      setIsRecording(false);
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  if (!supported) return null;

  return (
    <button
      onClick={toggle}
      title={isRecording ? "Click para detener" : "Click para hablar"}
      style={{
        position: "fixed",
        bottom: "88px",       // encima del input del sidebar
        right: "24px",
        zIndex: 9999,
        width: "52px",
        height: "52px",
        borderRadius: "50%",
        background: isRecording ? "#ef4444" : "#6366f1",
        border: "none",
        cursor: "pointer",
        fontSize: "22px",
        boxShadow: "0 4px 14px rgba(0,0,0,0.35)",
        transition: "background 0.2s, transform 0.1s",
        transform: isRecording ? "scale(1.1)" : "scale(1)",
      }}
    >
      {isRecording ? "⏹️" : "🎤"}
    </button>
  );
}

export default function Page() {
  return (
    <main>
      <h1>Your App</h1>
      <CopilotSidebar defaultOpen />
      <MicButton />
    </main>
  );
}
