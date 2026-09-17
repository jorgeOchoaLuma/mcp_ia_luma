"use client";
import { CopilotKit } from "@copilotkit/react-core/v2";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function CopilotProviderInner({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();
  const userEmail = searchParams.get("userEmail") || undefined;

  // Pasamos el email del usuario como property al backend de CopilotKit
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="agent_projects"
      properties={{ userEmail }}
    >
      {children}
    </CopilotKit>
  );
}

export function CopilotProvider({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CopilotProviderInner>
        {children}
      </CopilotProviderInner>
    </Suspense>
  );
}
