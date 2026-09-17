import os
from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from ag_ui_adk import AGUIToolset

# Resolver rutas de los skills
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("CURRENT DIR:", current_dir)

trends_skill_path = os.path.join(current_dir, 'skills', 'trends-analysis')
social_skill_path = os.path.join(current_dir, 'skills', 'social-strategy')
content_gen_skill_path = os.path.join(current_dir, 'skills', 'content-generation')

# Cargar skills
trends_skill = load_skill_from_dir(trends_skill_path)
social_skill = load_skill_from_dir(social_skill_path)
content_gen_skill = load_skill_from_dir(content_gen_skill_path)

# Combinar instrucciones
combined_instructions = f"""
# Deep Research & Content Creation Agent

Eres un agente experto en investigación de tendencias y creación de contenido. Puedes trabajar con **cualquier sector o industria**: moda, salud, finanzas, gastronomía, educación, deportes, tecnología, medio ambiente, entretenimiento, turismo, o cualquier otro que el usuario indique.

## Flujo de Trabajo Completo

Sigue estos 3 pasos en orden, usando SIEMPRE las tools disponibles para mostrar resultados — NUNCA imprimas JSON como texto en el chat.

### Paso 1 — Identificar el Sector
- Si el usuario no especificó un sector, pregúntale: "¿En qué sector o industria quieres que investigue? (Ej: moda, salud, finanzas, gastronomía, deportes...)"
- Si el usuario ya indicó el sector, continúa directamente al Paso 2.

### Paso 2 — Investigar Tendencias
- Usa la tool 'search_agent' para obtener información actualizada del sector.
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
- Después de llamar cada tool, puedes agregar un breve comentario en texto natural (ej. "Aquí tienes las tendencias del sector"), pero los datos estructurados van SIEMPRE por la tool, no en el mensaje.

---

{trends_skill.instructions}

---

{social_skill.instructions}

---

{content_gen_skill.instructions}

---

Si el usuario hace una consulta específica (ej. "Escríbeme el post de LinkedIn sobre sostenibilidad en moda"), adapta el flujo para reflejar solo ese análisis puntual, usando la tool correspondiente igualmente.
"""

# Agente de búsqueda: SOLO puede tener google_search como tool.
# No lleva sub_agents, ni disallow_transfer_*, ni ninguna otra tool,
# porque Gemini no permite mezclar google_search con otras tools.
search_agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="search_agent",
    description="Agente encargado ÚNICAMENTE de buscar información en tiempo real en internet.",
    instruction="Eres un buscador web en tiempo real. Utiliza tu herramienta 'google_search' para encontrar información actualizada sobre la consulta y devuelve los hallazgos.",
    tools=[google_search],
)

# Envolvemos search_agent como AgentTool en lugar de sub_agent.
# Así corre en un contexto aislado (solo con google_search) y
# deep_researcher lo invoca como una tool más, sin transferencia de control.
search_agent_tool = AgentTool(search_agent)

# Agente principal
deep_researcher = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="deep_researcher",
    description="Agente principal de investigación de tendencias y creación de contenido.",
    instruction=combined_instructions + "\n\nPara buscar en tiempo real, DEBES usar la tool 'search_agent' para obtener información actualizada.",
    tools=[AGUIToolset(), search_agent_tool],
)