import { CopilotProvider } from "./CopilotProvider";
import "@copilotkit/react-core/v2/styles.css";
import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={cn("font-sans", geist.variable)}>
      <body>
        <CopilotProvider>
          {children}
        </CopilotProvider>
      </body>
    </html>
  );
}