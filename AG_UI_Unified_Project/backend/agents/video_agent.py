"""
Video Producer Agent for Luma Cloud.
Portado desde AG_UI_agent_asistentente_video.
"""

import os

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.genai import types
from ag_ui_adk import ADKAgent

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
BQ_DATASET_ID = os.environ.get("BQ_DATASET_ID", "")
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")


def generar_resumen(transcripcion: str) -> dict:
    return {
        "status": "success",
        "tipo": "resumen",
        "contenido": transcripcion,
        "formato": "resumen_educativo",
    }


def generar_guion_avatar(transcripcion: str) -> dict:
    return {
        "status": "success",
        "tipo": "guion_avatar",
        "contenido": transcripcion,
        "formato": "guion_narrable",
    }


def generar_ayudas_visuales(transcripcion: str) -> dict:
    return {
        "status": "success",
        "tipo": "ayudas_visuales",
        "contenido": transcripcion,
        "formato": "tabla_visual",
        "columnas": ["Momento del Video", "Elemento Visual Sugerido", "Texto en Pantalla (Overlay)"],
        "instruccion": (
            "Presenta el resultado como tabla markdown con columnas: "
            "Momento del Video | Elemento Visual Sugerido | Texto en Pantalla (Overlay)"
        ),
    }


root_agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="video_producer",
    description=(
        "Asistente de producción de contenido para videos educativos sobre IA. "
        "Especializado en material accesible para audiencias no técnicas."
    ),
    instruction="""Eres el asistente de producción de contenido para el canal educativo de Luma Cloud sobre Inteligencia Artificial.

<contexto>
Eres un estratega en inteligencia artificial aplicada a empresas.
Asistente de producción de contenido para videos educativos sobre IA.
</contexto>

<instrucciones>
1. Analiza primero la intención del usuario.
2. Nunca generes las tres opciones al mismo tiempo; solo la seleccionada.
3. No expliques el proceso interno ni menciones herramientas.
4. Contenido claro, enfoque empresarial, ejemplos prácticos, sin jerga innecesaria.
5. Estructura visual clara: párrafos cortos y listas.
6. Si piden ajustes, modifica solo el contenido actual.
7. No agregues información que no esté en la transcripción.
8. Siempre pregunta por ajustes o siguiente paso al final.
9. Cuando uses generar_ayudas_visuales, presenta tabla markdown:
   | Momento del Video | Elemento Visual Sugerido | Texto en Pantalla (Overlay) |
   Mínimo 5 filas.
</instrucciones>

TU FLUJO:
1. Texto >20 palabras → ofrece menú: 1) Resumen 2) Guion Avatar 3) Ayudas Visuales.
2. Usa la herramienta correspondiente.
3. Pregunta por ajustes o siguiente paso.
""",
    tools=[generar_resumen, generar_guion_avatar, generar_ayudas_visuales],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2000,
    ),
)

plugins = []
if PROJECT_ID and BQ_DATASET_ID:
    plugins.append(
        BigQueryAgentAnalyticsPlugin(
            project_id=PROJECT_ID,
            dataset_id=BQ_DATASET_ID,
            location=BQ_LOCATION,
            config=BigQueryLoggerConfig(
                batch_size=1,
                batch_flush_interval=0.5,
                log_session_metadata=True,
                auto_schema_upgrade=True,
                create_views=True,
            ),
        )
    )

adk_app = App(
    name="video_producer_app",
    root_agent=root_agent,
    plugins=plugins,
)

adk_agent = ADKAgent.from_app(
    adk_app,
    user_id="demo_user",
    plugin_close_timeout=10.0,
)

# Compatibilidad con imports legacy
agent = root_agent
