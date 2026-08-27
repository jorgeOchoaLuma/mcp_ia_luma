---
name: social-strategy
description: Skill para convertir tendencias de cualquier sector en ideas creativas y accionables de contenido para múltiples formatos y plataformas (redes sociales, blogs, newsletters, podcasts, videos, etc.).
---

# Content Ideas Skill

Este skill convierte las tendencias investigadas en **ideas concretas de contenido** adaptadas a diferentes formatos y plataformas. Funciona para cualquier sector o industria.

## Análisis de Potencial de Contenido

1. Para cada tendencia identificada, evalúa:
   - ¿Genera debate o controversia? → Ideal para opinión y LinkedIn.
   - ¿Es visualmente atractiva? → Ideal para Instagram, TikTok, infografías.
   - ¿Necesita explicación profunda? → Ideal para artículos, newsletters, podcasts.
   - ¿Tiene urgencia o novedad? → Ideal para noticias rápidas, Reels, stories.
2. Usa `google_search` para identificar qué tipo de contenido sobre este sector está generando más interacción en redes sociales y medios digitales.

## Formatos de Contenido a Considerar

Propón ideas en los siguientes formatos (selecciona los más adecuados para cada tendencia):

- **Redes Sociales**: Instagram (carrusel, Reel, story), LinkedIn (artículo, post), TikTok (video corto), Facebook (post, video)
- **Blog / Website**: Artículo informativo, guía práctica, opinión, listicle
- **Newsletter / Email**: Resumen semanal, análisis profundo, curación de noticias
- **Video**: YouTube (tutorial, entrevista, documental corto), Reel/TikTok (tendencia rápida)
- **Podcast / Audio**: Episodio de debate, entrevista a experto, resumen de noticias
- **Infografía / Visual**: Datos visualizados, paso a paso, comparativa

## Guías de Calidad para las Ideas

- **Títulos persuasivos y específicos**: En lugar de "Tendencias de moda", usa "Las 5 tendencias de moda sostenible que dominarán el otoño 2026".
- **Enfoque claro por formato**: Educativo, Opinión, Noticia, Entretenimiento, Inspiración, Tutorial.
- **Justificación basada en datos**: Explica por qué esa idea funcionará ahora (ej: "tendencia en crecimiento del 40% en búsquedas").
- **No dejar listas vacías**: Si no hay datos directos de engagement, usa razonamiento lógico basado en el comportamiento del sector.

## Ejemplos de Referencia (Genéricos por Formato)

> **Formato**: Carrusel Instagram
> **Ejemplo de título**: "5 cosas que nadie te dice sobre [tendencia del sector]"
> **Enfoque**: Educativo + visual. Ideal para audiencias que descubren el tema.

> **Formato**: Artículo de Blog / LinkedIn
> **Ejemplo de título**: "¿Por qué [tendencia] está cambiando las reglas en [sector]?"
> **Enfoque**: Análisis profundo + liderazgo de pensamiento.

> **Formato**: Video corto (Reel / TikTok)
> **Ejemplo de título**: "Lo que está pasando en [sector] que nadie está hablando"
> **Enfoque**: Novedad + gancho emocional. Máximo 60 segundos.

> **Formato**: Newsletter
> **Ejemplo de título**: "Esta semana en [sector]: [tendencia] y lo que significa para ti"
> **Enfoque**: Curación + análisis accesible para suscriptores.

## Horarios Óptimos de Publicación (Guía General)

- **LinkedIn**: Martes a jueves, 8-10am o 12-2pm (horario local). Ideal para contenido B2B y profesional.
- **Instagram**: Lunes, miércoles y viernes, 10am-12pm o 6-8pm. Ideal para contenido visual y lifestyle.
- **TikTok**: Martes, jueves y viernes, 7-9pm. Ideal para tendencias y contenido de entretenimiento.
- **Facebook**: Miércoles y jueves, 1-4pm. Ideal para comunidades y noticias.
- **Newsletter/Blog**: Martes o miércoles por la mañana. Alta tasa de apertura en días laborales.

## Formato de Salida

```json
{
  "ideas_de_contenido": [
    {
      "tendencia_base": "Título de la tendencia que origina esta idea",
      "formato": "Tipo de contenido (Carrusel, Artículo, Reel, Newsletter, Podcast, Infografía, etc.)",
      "titulo_sugerido": "Título persuasivo y específico listo para usar",
      "enfoque": "Educativo / Opinión / Noticia / Tutorial / Inspiración / Debate",
      "plataformas": ["Plataforma1", "Plataforma2"],
      "descripcion_breve": "Qué cubriría este contenido en 2-3 líneas",
      "justificacion": "Por qué este contenido funcionará ahora",
      "horario_sugerido": "Mejor momento para publicar"
    }
  ],
  "recomendacion_editorial": "Consejo general de estrategia de contenido para este sector este mes"
}
```
