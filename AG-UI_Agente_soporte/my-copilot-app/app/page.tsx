import { CopilotSidebar } from "@copilotkit/react-ui";

export default function Page() {
  return (
    <main>
      <h1>Your App</h1>
      <CopilotSidebar labels={{ initial: "Hola soy un agente de soporte de Luma Cloud, ¿en qué puedo ayudarte hoy?" }} />
    </main>
  );
}