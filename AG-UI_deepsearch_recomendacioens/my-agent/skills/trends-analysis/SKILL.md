---
name: trends-analysis
description: Skill para realizar búsquedas profundas y análisis de tendencias actuales en CUALQUIER sector o industria indicado por el usuario (moda, salud, finanzas, gastronomía, deportes, tecnología, educación, etc.).
---

# Trends Analysis Skill

Este skill permite al agente investigar y resumir las tendencias más importantes del momento en el sector que el usuario indique. **No está limitado a ninguna industria específica.**

## Identificación del Sector

- Si el usuario **especificó un sector o industria**, úsalo directamente para guiar toda la investigación.
- Si el usuario **no especificó un sector**, pregúntale antes de continuar: *"¿En qué sector o industria quieres que analice las tendencias? (Ej: moda, salud, finanzas, gastronomía, educación, deportes, tecnología, medio ambiente, etc.)"*

## Instrucciones de Investigación

1. Utiliza `google_search` con el nombre del sector + términos como: "tendencias 2026", "noticias recientes", "reportes de la industria", "qué está cambiando en [sector]".
2. Busca en fuentes relevantes: noticias, blogs especializados, reportes de analistas, publicaciones de industria.
3. Identifica entre **3 y 5 tendencias** que están dominando la conversación en ese sector en los últimos 30-60 días.
4. Para cada tendencia, extrae:
   - **Título**: Nombre corto y descriptivo de la tendencia.
   - **Contexto**: ¿Por qué está ganando fuerza ahora? ¿Qué la originó?
   - **Impacto**: ¿Cómo afecta a las empresas, consumidores o profesionales del sector?
   - **Audiencia objetivo**: ¿A quién le interesa más esta tendencia? (Ej: emprendedores, consumidores finales, profesionales del sector, inversores, etc.)

## Guías de Calidad

- **Nunca dejes listas vacías**: Si la información directa es escasa, infiere a partir de señales del mercado, comportamiento del consumidor o noticias relacionadas.
- **Sé específico**: Evita tendencias genéricas como "la digitalización sigue creciendo". Prefiere tendencias concretas con nombre y contexto real.
- **Sé actual**: Prioriza noticias y reportes de los últimos 1-2 meses.

## Formato de Salida

Genera la información en formato JSON siguiendo esta estructura:

```json
{
  "sector": "Nombre del Sector analizado",
  "fecha_analisis": "Mes y año del análisis",
  "tendencias": [
    {
      "titulo": "Título corto de la tendencia",
      "contexto": "¿Por qué es relevante ahora?",
      "impacto": "¿Cómo afecta a empresas o personas del sector?",
      "audiencia_objetivo": "A quién le interesa más"
    }
  ]
}
```
