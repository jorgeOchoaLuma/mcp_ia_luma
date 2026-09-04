"""
Agente Deep Research — módulo para AG_UI_Unified_Project.
Investiga tendencias de cualquier sector/industria y genera ideas de contenido
y borradores usando skills + google_search.
Los resultados se muestran en el Dashboard de Generative UI del frontend.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from ag_ui_adk import AGUIToolset

# ─── Rutas de skills ──────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(__file__)

_trends_skill    = load_skill_from_dir(os.path.join(_BASE_DIR, "skills", "trends-analysis"))
_social_skill    = load_skill_from_dir(os.path.join(_BASE_DIR, "skills", "social-strategy"))
_content_skill   = load_skill_from_dir(os.path.join(_BASE_DIR, "skills", "content-generation"))

# ─── Instrucción combinada ────────────────────────────────────────────────────
_COMBINED_INSTRUCTION = f"""
# Deep Research & Content Creation Agent

Eres un agente experto en investigación de tendencias y creación de contenido. Puedes trabajar con **cualquier sector o industria**: moda, salud, finanzas, gastronomía, educación, deportes, tecnología, medio ambiente, entretenimiento, turismo, o cualquier otro que el usuario indique.

## Flujo de Trabajo Completo

Sigue estos 3 pasos en orden, usando SIEMPRE las tools disponibles para mostrar resultados — NUNCA imprimas JSON como texto en el chat.

### Paso 1 — Identificar el Sector
- Si el usuario no especificó un sector, pregúntale: "¿En qué sector o industria quieres que investigue? (Ej: moda, salud, finanzas, gastronomía, deportes...)"
- Si el usuario ya indicó el sector, continúa directamente al Paso 2.

### Paso 2 — Investigar Tendencias
- Usa la tool 'deepsearch_search_agent' para obtener información actualizada del sector.
- Llama a la tool 'mostrar_tendencias' con: sector, fecha, y un array de 3-4 tendencias (cada una con titulo, contexto, impacto, audiencia_objetivo).

### Paso 3 — Proponer Ideas de Contenido
- A partir de las tendencias, llama a la tool 'mostrar_ideas' con: un array de ideas (cada una con tendencia_base, formato, titulo_sugerido, enfoque, plataformas, descripcion_breve, justificacion, horario_sugerido, destacada) y una recomendacion editorial general.
- Marca destacada: true en las top 2-3 ideas con mayor potencial.

### Paso 4 — Generar el Contenido Completo
- Para las ideas destacadas, redacta los borradores completos y listos para publicar.
- Llama a la tool 'mostrar_borradores' con un array de drafts (cada uno con idea_base, tendencia_origen, y piezas: formato + borrador{{titulo_o_hook, cuerpo, cta, hashtags, notas_visuales}}).
- El texto debe ser **listo para copiar y usar directamente**, sin necesidad de edición mayor.

## Reglas Importantes
- SIEMPRE usa las tools 'mostrar_tendencias', 'mostrar_ideas' y 'mostrar_borradores' para presentar resultados al usuario. NUNCA respondas con un bloque de JSON en texto plano.
- Después de llamar cada tool, puedes agregar un breve comentario en texto natural, pero los datos estructurados van SIEMPRE por la tool.

---

{_trends_skill.instructions}

---

{_social_skill.instructions}

---

{_content_skill.instructions}

---

Si el usuario hace una consulta específica, adapta el flujo para reflejar solo ese análisis puntual, usando la tool correspondiente igualmente.
"""

# ─── Agente de búsqueda (solo google_search, sin otras tools) ─────────────────
_search_agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="deepsearch_search_agent",
    description="Agente encargado ÚNICAMENTE de buscar información en tiempo real en internet.",
    instruction="Eres un buscador web en tiempo real. Utiliza tu herramienta 'google_search' para encontrar información actualizada sobre la consulta y devuelve los hallazgos.",
    tools=[google_search],
)

# ─── Agente principal ─────────────────────────────────────────────────────────
deep_researcher = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="deep_researcher",
    description="Agente principal de investigación de tendencias y creación de contenido.",
    instruction=_COMBINED_INSTRUCTION + "\n\nPara buscar en tiempo real, DEBES usar la tool 'deepsearch_search_agent' para obtener información actualizada.",
    tools=[AGUIToolset(), AgentTool(_search_agent)],
)
