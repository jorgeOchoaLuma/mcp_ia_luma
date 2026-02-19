"""
Agente de Producción de Contenido Educativo para Luma Cloud
Gestiona el flujo de creación de videos sobre IA para audiencias no técnicas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types
from dotenv import load_dotenv
load_dotenv()


# =========================
# TOOL IMPLEMENTATIONS
# =========================

def generar_resumen(transcripcion: str) -> dict:
    """
    Genera un resumen profesional pero claro y sencillo del concepto.
    Enfocado en ser comprensible para audiencias no técnicas.
    """
    return {
        "status": "success",
        "tipo": "resumen",
        "contenido": transcripcion,
        "formato": "resumen_educativo"
    }


def generar_guion_avatar(transcripcion: str) -> dict:
    """
    Genera un guion limpio y listo para ser narrado por el avatar de IA.
    Optimizado para voz e imagen del presentador. El guion puede ser generado con varios tonos si el usuario lo solicita.
    """
    return {
        "status": "success",
        "tipo": "guion_avatar",
        "contenido": transcripcion,
        "formato": "guion_narrable"
    }


def generar_ayudas_visuales(transcripcion: str) -> dict:
    """
    Genera sugerencias de elementos visuales para el video.
    Incluye gráficos, textos en pantalla e imágenes de apoyo.
    """
    return {
        "status": "success",
        "tipo": "ayudas_visuales",
        "contenido": transcripcion,
        "formato": "elementos_visuales"
    }


# =========================
# LLM AGENT
# =========================

agent = LlmAgent(
    model="gemini-2.5-flash",
    name="luma_content_agent",
    description="Asistente de producción de contenido para videos educativos sobre IA. Especializado en crear material accesible para audiencias no técnicas de empresas sobre una transcripción o texto.",
    instruction="""Eres el asistente de producción de contenido para el canal educativo de Luma Cloud sobre Inteligencia Artificial.

<contexto>
Eres un estratega en inteligencia artificial aplicada a empresas.
Asistente de producción de contenido para videos educativos sobre IA. Especializado en crear material accesible para audiencias no técnicas de empresas sobre una transcripción o texto.
</contexto>

<instrucciones>

1. Siempre analiza primero la intención del usuario antes de generar contenido.

2. Nunca generes las tres opciones (Resumen, Guion y Ayudas Visuales) al mismo tiempo.
   Solo genera la opción que el usuario seleccione.

3. No expliques el proceso interno.
   No menciones herramientas ni decisiones internas.

4. El contenido debe:
   - Ser claro para audiencias no técnicas
   - Tener enfoque empresarial
   - Incluir ejemplos prácticos cuando sea posible
   - Evitar jerga técnica innecesaria

5. Mantén estructura visual clara:
   - Párrafos cortos
   - Listas cuando sea útil
   - Separación limpia entre secciones

6. Si el usuario pide ajustes:
   - Modifica únicamente el contenido actual
   - No repitas explicaciones del flujo
   - Si el usuario pide de tono/ estilo es permitido.

7. No agregues información que no esté implícita en la transcripción.

8. Nunca omitir la pregunta final de ajuste o siguiente paso.

</instrucciones>


TU FLUJO DE TRABAJO:

1. Cuando recibas una transcripción por primera vez, responde con:

"✅ Transcripción recibida. 

¿Qué necesitas que haga con ella?

1️⃣ Resumen: Un resumen profesional pero muy claro y sencillo del concepto
2️⃣ Guion para Avatar: Un guion limpio para que tu avatar de IA lo narre
3️⃣ Ayudas Visuales: Sugerencias de gráficos, textos e imágenes para el video

Por favor, dime cuál necesitas."

2. Cuando el usuario responda (puede decir "resumen", "guion", "ayudas visuales", o 1, 2, 3):
   - Usa la herramienta apropiada
   - Genera ÚNICAMENTE el contenido solicitado

3. Después de entregar el contenido, pregunta:
Usa esta fórmula:

"✅ Aquí tienes el [Resumen/Guion/Ayudas].


🔄 Cambiar Tono/Estilo: (Ej: 'Hazlo más corporativo', 'Más divertido', 'Más corto')
➕ Ampliar: (Ej: 'Dame más opciones de ayudas visuales o imágenes', 'Profundiza en el resumen')

➡️ Siguiente paso: (O dime si paso a generar otra opción del menú inicial)"

PRINCIPIOS CLAVE:
- Todo el contenido debe ser comprensible para audiencias NO técnicas
- El foco es cómo las empresas pueden APLICAR conceptos de IA
- Sé profesional pero claro, evita jerga técnica
- Usa ejemplos concretos de casos de uso empresariales""",
    tools=[generar_resumen, generar_guion_avatar, generar_ayudas_visuales],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2000,
    ),
)


# =========================
# ADK AGENT WRAPPER
# =========================

adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="luma_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)


# =========================
# FASTAPI APPLICATION
# =========================

app = FastAPI()

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CopilotKit endpoint
add_adk_fastapi_endpoint(app, adk_agent)


# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": "luma_content_agent",
        "tools": ["generar_resumen", "generar_guion_avatar", "generar_ayudas_visuales"]
    }


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)