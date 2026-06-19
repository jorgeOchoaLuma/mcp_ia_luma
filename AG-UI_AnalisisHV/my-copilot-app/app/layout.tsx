import { CopilotKit } from "@copilotkit/react-core/v2"; 
import "@copilotkit/react-core/v2/styles.css";
import './globals.css';

// ...

export default function RootLayout({ children }: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit" agent="my_agent">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}