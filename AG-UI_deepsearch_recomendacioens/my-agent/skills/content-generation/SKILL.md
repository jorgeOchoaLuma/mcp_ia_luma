---
name: content-generation
description: Skill para redactar borradores completos y listos para publicar de las ideas de contenido con mayor potencial. Genera el texto real por formato (post LinkedIn, carrusel, guión de video, artículo de blog, newsletter).
---

# Content Generation Skill

Este skill toma las **2-3 ideas de contenido con mayor potencial** identificadas en el análisis y genera los **borradores completos y listos para publicar**, adaptados al tono y audiencia de cada plataforma.

## Selección de Ideas a Desarrollar

Antes de redactar, selecciona las top 2-3 ideas del análisis basándote en:
- Mayor potencial de engagement para el sector analizado
- Variedad de formatos (no repitas el mismo tipo dos veces)
- Relevancia y urgencia de la tendencia que las origina

## Instrucciones por Formato

### 📱 Post de LinkedIn
- Longitud: 150-300 palabras
- Tono: Profesional, reflexivo, con llamada a la acción
- Estructura: Hook (1-2 líneas impactantes) → Desarrollo (3-5 párrafos cortos) → CTA + pregunta para comentarios
- Incluir sugerencia de emojis estratégicos y hashtags relevantes (5-8 hashtags)

### 🎠 Carrusel de Instagram
- Entre 5 y 8 slides
- Slide 1: Portada con título gancho
- Slides 2-N: Un punto clave por slide (texto corto, máx 30 palabras por slide)
- Último slide: CTA claro ("Guarda este post", "Comparte con alguien que necesita esto")
- Incluir sugerencia de paleta de colores y estilo visual acorde al sector

### 🎬 Script de Reel / TikTok
- Duración objetivo: 30-60 segundos
- Estructura: Hook (0-3s) → Desarrollo rápido (puntos clave en 3-5 oraciones) → Cierre + CTA
- Incluir: texto del caption, hashtags (10-15), sugerencia de música/sonido de tendencia
- Tono: dinámico, directo, coloquial según la audiencia

### 📝 Artículo de Blog
- Longitud: esquema completo con introducción (100 palabras), 3-4 secciones desarrolladas (100-150 palabras c/u) y conclusión + CTA
- Incluir: título SEO optimizado, meta descripción (155 caracteres), palabra clave principal sugerida
- Tono: informativo y accesible, con ejemplos concretos del sector

### 📧 Newsletter
- Asunto principal + asunto alternativo (A/B test)
- Preview text (90 caracteres)
- Cuerpo: saludo personalizado → intro breve → contenido principal (3-4 bloques) → CTA final
- Tono: cercano, de conversación entre expertos

## Guías de Calidad

- **Tono adaptado al sector**: Un post de moda no suena igual que uno de finanzas. Ajusta vocabulario y referencias.
- **Hooks poderosos**: La primera línea debe detener el scroll. Usa datos sorprendentes, preguntas provocadoras o afirmaciones inesperadas.
- **CTAs específicos**: Evita "visita nuestra web". Prefiere "¿Qué opinas? Cuéntanos en los comentarios" o "Guarda esto para tu próxima reunión de equipo".
- **Listo para copiar-pegar**: El texto debe poder usarse directamente sin edición mayor.

## Formato de Salida

```json
{
  "contenido_generado": [
    {
      "idea_base": "Título de la idea que se está desarrollando",
      "tendencia_origen": "Tendencia del sector que inspiró esta idea",
      "piezas": [
        {
          "formato": "Post LinkedIn / Carrusel Instagram / Script Reel / Artículo Blog / Newsletter",
          "borrador": {
            "titulo_o_hook": "Primera línea o título",
            "cuerpo": "Texto completo del contenido",
            "cta": "Llamada a la acción específica",
            "hashtags": ["#hashtag1", "#hashtag2"],
            "notas_visuales": "Sugerencias de diseño, música o estilo visual (si aplica)"
          }
        }
      ]
    }
  ]
}
```
