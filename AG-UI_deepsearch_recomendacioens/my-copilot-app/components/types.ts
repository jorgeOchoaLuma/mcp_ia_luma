import { z } from "zod";

export const TrendSchema = z.object({
  titulo: z.string(),
  contexto: z.string(),
  impacto: z.string(),
  audiencia_objetivo: z.string(),
});
export type Trend = z.infer<typeof TrendSchema>;

export const ContentIdeaSchema = z.object({
  tendencia_base: z.string(),
  formato: z.string(),
  titulo_sugerido: z.string(),
  enfoque: z.string(),
  plataformas: z.array(z.string()),
  descripcion_breve: z.string(),
  justificacion: z.string(),
  horario_sugerido: z.string(),
  destacada: z.boolean().optional(),
});
export type ContentIdea = z.infer<typeof ContentIdeaSchema>;

export const ContentDraftSchema = z.object({
  idea_base: z.string(),
  tendencia_origen: z.string(),
  piezas: z.array(
    z.object({
      formato: z.string(),
      borrador: z.object({
        titulo_o_hook: z.string(),
        cuerpo: z.string(),
        cta: z.string(),
        hashtags: z.array(z.string()),
        notas_visuales: z.string().optional(),
      }),
    })
  ),
});
export type ContentDraft = z.infer<typeof ContentDraftSchema>;

export type AppState = {
  sector: string | null;
  fecha: string | null;
  tendencias: Trend[];
  ideas: ContentIdea[];
  drafts: ContentDraft[];
  recomendacion: string | null;
};
