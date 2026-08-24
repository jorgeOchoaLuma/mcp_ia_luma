// app/hooks/use-example-suggestions.ts
"use client";

// No usamos useCopilotChatSuggestions (es premium, no está en tu paquete).
// En su lugar, exponemos una lista fija de sugerencias que App.tsx puede
// renderizar como botones simples antes del primer mensaje.

export const EXAMPLE_SUGGESTIONS = [
    { title: "Generar ayudas visuales", message: "Genera las ayudas visuales para esta transcripción" },
    { title: "Elegir formato", message: "Necesito las ayudas visuales para Reels de Instagram" },
    { title: "Elegir estilo", message: "Quiero las ayudas visuales en estilo fotorrealista" },
    { title: "Resumen del contenido", message: "Dame un resumen de esta transcripción" },
];