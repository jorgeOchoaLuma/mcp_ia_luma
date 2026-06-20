import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

export const metadata = {
  title: "Zoho Desk — Ticket Operations",
  description: "Asistente MCP para operaciones de tickets Zoho Desk",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit" agent="zoho_desk">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
