import { AgentProvider } from "./agent-provider";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AgentProvider>{children}</AgentProvider>
      </body>
    </html>
  );
}
