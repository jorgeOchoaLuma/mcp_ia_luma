"use client";

import { useState } from "react";

import {
  CopilotChat,
  useFrontendTool,
} from "@copilotkit/react-core/v2";

import {
  Sparkles,
  TrendingUp,
  Lightbulb,
  FileText,
  Check,
  Copy,
  Download,
} from "lucide-react";

import { z } from "zod";

import {
  AppState,
  TrendSchema,
  ContentIdeaSchema,
  ContentDraftSchema,
} from "./types";

export default function Dashboard() {
  const [appState, setAppState] = useState<AppState>({
    sector: null,
    fecha: null,
    tendencias: [],
    ideas: [],
    drafts: [],
    recomendacion: null,
  });

  const [activeDraftIndex, setActiveDraftIndex] = useState(0);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);

    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  const handleDownloadJSON = () => {
    const dataToExport = {
      sector: appState.sector,
      fecha: appState.fecha,
      tendencias: appState.tendencias,
      ideas: appState.ideas,
      recomendacion: appState.recomendacion,
      drafts: appState.drafts,
    };

    const jsonString = JSON.stringify(dataToExport, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `analisis-${appState.sector?.toLowerCase().replace(/\s+/g, "-") || "contenido"
      }.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // ============================================================
  // MOSTRAR TENDENCIAS
  // ============================================================

  useFrontendTool({
    name: "mostrar_tendencias",

    description:
      "Muestra las tendencias investigadas para el sector",

    parameters: z.object({
      sector: z.string(),
      fecha: z.string(),
      tendencias: z.array(TrendSchema),
    }),

    handler: async (args) => {
      const tendencias = args.tendencias;

      setAppState((prev) => ({
        ...prev,
        sector: args.sector,
        fecha: args.fecha,
        tendencias,
      }));
    },

    render: (props) => (
      <div
        className={`tool-preview ${props.status === "complete" ? "done" : "loading"
          }`}
      >
        <div className="tool-preview-icon">🔍</div>

        <div className="tool-preview-info">
          <strong>
            Analizando tendencias{" "}
            {props.status === "complete" ? "completado" : "..."}
          </strong>

          {props.args?.sector && (
            <span className="tool-preview-meta">
              Sector: {props.args.sector}
            </span>
          )}
        </div>

        {props.status === "complete" && (
          <span className="tool-preview-badge">✓ Listo</span>
        )}
      </div>
    ),
  });

  // ============================================================
  // MOSTRAR IDEAS
  // ============================================================

  useFrontendTool({
    name: "mostrar_ideas",

    description:
      "Muestra las ideas de contenido generadas a partir de las tendencias",

    parameters: z.object({
      ideas: z.array(ContentIdeaSchema),
      recomendacion: z.string(),
    }),

    handler: async (args) => {
      const ideas = args.ideas;

      setAppState((prev) => ({
        ...prev,
        ideas,
        recomendacion: args.recomendacion,
      }));
    },

    render: (props) => (
      <div
        className={`tool-preview ${props.status === "complete" ? "done" : "loading"
          }`}
      >
        <div className="tool-preview-icon">💡</div>

        <div className="tool-preview-info">
          <strong>
            Generando ideas{" "}
            {props.status === "complete" ? "completado" : "..."}
          </strong>
        </div>

        {props.status === "complete" && (
          <span className="tool-preview-badge">✓ Listo</span>
        )}
      </div>
    ),
  });

  // ============================================================
  // MOSTRAR BORRADORES
  // ============================================================

  useFrontendTool({
    name: "mostrar_borradores",

    description:
      "Muestra los borradores completos y listos para publicar",

    parameters: z.object({
      drafts: z.array(ContentDraftSchema),
    }),

    handler: async (args) => {
      const drafts = args.drafts;

      setAppState((prev) => ({
        ...prev,
        drafts,
      }));
    },

    render: (props) => (
      <div
        className={`tool-preview ${props.status === "complete" ? "done" : "loading"
          }`}
      >
        <div className="tool-preview-icon">📝</div>

        <div className="tool-preview-info">
          <strong>
            Escribiendo borradores{" "}
            {props.status === "complete" ? "completado" : "..."}
          </strong>
        </div>

        {props.status === "complete" && (
          <span className="tool-preview-badge">✓ Listo</span>
        )}
      </div>
    ),
  });

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="app-root">
      {/* HEADER */}
      <header className="app-header">
        <div className="app-header-logo">
          <Sparkles size={18} color="white" />
        </div>

        <div>
          <h1 className="app-header-title">Deep Research UI</h1>
          <span className="app-header-subtitle">
            Generative Content Platform
          </span>
        </div>
      </header>

      <div className="app-body">
        {/* ======================================================
            DASHBOARD PANEL
        ====================================================== */}

        <div className="dashboard-panel">
          {appState.tendencias.length === 0 &&
            appState.ideas.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">✨</div>

              <h2 className="empty-state-title">
                ¿Qué sector analizamos hoy?
              </h2>

              <p className="empty-state-desc">
                Pídele al agente que analice tendencias para un sector
                (ej: Gastronomía, Finanzas, Salud). Automáticamente
                extraerá data, creará ideas y redactará los posts
                finales.
              </p>

              <div className="empty-state-chips">
                <span className="chip">
                  Analiza tendencias de moda 2026
                </span>
                <span className="chip">
                  Ideas de contenido para salud mental
                </span>
              </div>
            </div>
          ) : (
            <>
              {/* ==================================================
                  SECTOR
              ================================================== */}

              {appState.sector && (
                <div className="sector-badge">
                  <Sparkles size={14} />
                  Análisis de: {appState.sector} ({appState.fecha})
                </div>
              )}

              {/* ==================================================
                  TENDENCIAS
              ================================================== */}

              {appState.tendencias.length > 0 && (
                <section>
                  <div className="section-header">
                    <div className="section-icon trends">
                      <TrendingUp
                        size={18}
                        color="var(--color-primary-light)"
                      />
                    </div>

                    <div>
                      <h2 className="section-title">
                        Tendencias Detectadas
                      </h2>
                      <span className="section-meta">
                        Top {appState.tendencias.length} temas del
                        momento
                      </span>
                    </div>
                  </div>

                  <div className="trends-grid">
                    {appState.tendencias.map((t, idx) => (
                      <div key={idx} className="card trend-card">
                        <div className="trend-number">
                          Tendencia 0{idx + 1}
                        </div>

                        <h3 className="trend-title">{t.titulo}</h3>
                        <p className="trend-text">{t.contexto}</p>

                        <div className="trend-label">Impacto</div>
                        <p className="trend-text mb-0">{t.impacto}</p>

                        <div className="trend-audience">
                          Target: {t.audiencia_objetivo}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* ==================================================
                  IDEAS
              ================================================== */}

              {appState.ideas.length > 0 && (
                <section>
                  <div className="section-header">
                    <div className="section-icon ideas">
                      <Lightbulb size={18} color="var(--color-cyan)" />
                    </div>

                    <div>
                      <h2 className="section-title">
                        Ideas de Contenido
                      </h2>
                      <span className="section-meta">
                        Basadas en las tendencias detectadas
                      </span>
                    </div>
                  </div>

                  {appState.recomendacion && (
                    <div className="editorial-box">
                      <div className="editorial-label">
                        Consejo Editorial
                      </div>
                      <div className="editorial-text">
                        {appState.recomendacion}
                      </div>
                    </div>
                  )}

                  <div className="ideas-grid mt-2">
                    {appState.ideas.map((idea, idx) => {
                      const platform =
                        idea.plataformas[0]?.toLowerCase() || "default";

                      return (
                        <div
                          key={idx}
                          className={`card idea-card ${idea.destacada ? "destacada" : ""
                            }`}
                        >
                          <span className={`format-badge ${platform}`}>
                            {idea.formato}
                          </span>

                          <h3 className="idea-title">
                            {idea.titulo_sugerido}
                          </h3>
                          <p className="idea-desc">
                            {idea.descripcion_breve}
                          </p>

                          <div className="idea-meta">
                            {idea.plataformas.map((p) => (
                              <span key={p} className="idea-platform">
                                {p}
                              </span>
                            ))}
                          </div>

                          <div className="idea-schedule">
                            🕒 {idea.horario_sugerido}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}

              {/* ==================================================
                  BORRADORES
              ================================================== */}

              {appState.drafts.length > 0 && (
                <section>
                  <div className="section-header">
                    <div className="section-icon drafts">
                      <FileText size={18} color="var(--color-emerald)" />
                    </div>

                    <div>
                      <h2 className="section-title">
                        Borradores Generados
                      </h2>
                      <span className="section-meta">
                        Listos para copiar y publicar
                      </span>
                    </div>

                    <button
                      onClick={handleDownloadJSON}
                      className="download-btn"
                      style={{ marginLeft: "auto" }}
                    >
                      <Download size={14} /> Descargar JSON
                    </button>
                  </div>

                  <div className="mt-2">
                    {appState.drafts.map((draft, draftIdx) => (
                      <div key={draftIdx} className="draft-item">
                        <h3 className="draft-idea-title">
                          {draft.idea_base}
                        </h3>

                        <div className="draft-tendency">
                          Inspirado en: {draft.tendencia_origen}
                        </div>

                        <div className="draft-tabs">
                          {draft.piezas.map((pieza, pIdx) => (
                            <button
                              key={pIdx}
                              onClick={() => setActiveDraftIndex(pIdx)}
                              className={`draft-tab ${activeDraftIndex === pIdx ? "active" : ""
                                }`}
                            >
                              {pieza.formato}
                            </button>
                          ))}
                        </div>

                        {draft.piezas[activeDraftIndex] && (
                          <div className="draft-content-box">
                            <div className="flex justify-between items-center mb-0">
                              <h4 className="draft-hook">
                                {
                                  draft.piezas[activeDraftIndex].borrador
                                    .titulo_o_hook
                                }
                              </h4>

                              <button
                                onClick={() =>
                                  handleCopy(
                                    draft.piezas[activeDraftIndex].borrador
                                      .cuerpo,
                                    `${draftIdx}-${activeDraftIndex}`
                                  )
                                }
                                className={`copy-btn ${copiedId ===
                                    `${draftIdx}-${activeDraftIndex}`
                                    ? "copied"
                                    : ""
                                  }`}
                              >
                                {copiedId ===
                                  `${draftIdx}-${activeDraftIndex}` ? (
                                  <>
                                    <Check size={14} /> Copiado
                                  </>
                                ) : (
                                  <>
                                    <Copy size={14} /> Copiar
                                  </>
                                )}
                              </button>
                            </div>

                            <div className="draft-body">
                              {
                                draft.piezas[activeDraftIndex].borrador
                                  .cuerpo
                              }
                            </div>

                            {draft.piezas[activeDraftIndex].borrador
                              .cta && (
                                <div className="draft-cta">
                                  👉{" "}
                                  {
                                    draft.piezas[activeDraftIndex].borrador
                                      .cta
                                  }
                                </div>
                              )}

                            {draft.piezas[activeDraftIndex].borrador
                              .hashtags &&
                              draft.piezas[activeDraftIndex].borrador
                                .hashtags.length > 0 && (
                                <div className="draft-hashtags">
                                  {draft.piezas[
                                    activeDraftIndex
                                  ].borrador.hashtags.map((tag, i) => (
                                    <span key={i} className="draft-hashtag">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}

                            {draft.piezas[activeDraftIndex].borrador
                              .notas_visuales && (
                                <div className="draft-notes mt-2">
                                  <strong>🎨 Tip Visual:</strong>{" "}
                                  {
                                    draft.piezas[activeDraftIndex].borrador
                                      .notas_visuales
                                  }
                                </div>
                              )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>

        {/* ======================================================
            CHAT
        ====================================================== */}

        <div className="chat-panel">
          <div className="chat-panel-header">Asistente de Contenido</div>

          <CopilotChat
            labels={{
              welcomeMessageText:
                "¿En qué sector quieres que investigue tendencias y cree contenido hoy?",
            }}
          />
        </div>
      </div>
    </div>
  );
}