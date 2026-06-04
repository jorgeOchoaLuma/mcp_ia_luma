"use client";

import { useState } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotChat } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";

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

      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.error) throw new Error(data.error);

      setUploaded(file.name);

      // Inyectar como mensaje de texto al agente
      appendMessage(
        new TextMessage({
          role: Role.User,
          content: `El usuario ha subido un archivo. Procésalo y genera un resumen completo.\n\nDetalles del archivo:\n- Nombre: ${file.name}\n- Tipo: ${file.type}\n- URI en GCS: ${data.url}\n\nPor favor analiza este archivo usando la URI GCS proporcionada.`,
        })
      );
    } catch (err: any) {
      alert("Error al subir: " + err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div style={{
      position: "fixed",
      bottom: "80px",
      right: "20px",
      zIndex: 1000,
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-end",
      gap: "8px",
    }}>
      {uploaded && (
        <div style={{
          background: "#e8f5e9",
          border: "1px solid #4caf50",
          borderRadius: "8px",
          padding: "6px 12px",
          fontSize: "12px",
          color: "#2e7d32",
          maxWidth: "200px",
          wordBreak: "break-word",
        }}>
          ✓ {uploaded}
        </div>
      )}
      <label style={{
        background: "#1976d2",
        color: "white",
        borderRadius: "50%",
        width: "48px",
        height: "48px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: uploading ? "not-allowed" : "pointer",
        opacity: uploading ? 0.7 : 1,
        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        fontSize: "20px",
      }}>
        {uploading ? "⏳" : "📎"}
        <input
          type="file"
          accept="audio/*,video/*,image/*,.pdf"
          onChange={handleFile}
          disabled={uploading}
          style={{ display: "none" }}
        />
      </label>
    </div>
  );
}

export default function Page() {
  return (
    <main>
      <h1>Resumen de Reuniones</h1>
      <UploadButton />
      <CopilotSidebar />
    </main>
  );
}
