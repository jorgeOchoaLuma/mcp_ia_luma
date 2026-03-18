"""
Research Agent con Google ADK
Arquitectura: SequentialAgent

  1. SearchAgent  → google_search (built-in only)
                    output_key="research_report"
  2. SaverAgent   → save_research_to_markdown (FunctionTool only)
                    input_key="research_report"

Gemini no permite mezclar built-in tools con FunctionTool en el mismo agente.
El traspaso entre agentes se hace con output_key / input_key en el estado de sesión.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import google_search
from google.adk.tools.function_tool import FunctionTool
from google.genai.types import Content, Part

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools import url_context
from google.genai import types
from typing import Optional

from url_validator import (
    before_tool_callback,
    after_tool_callback,
    before_model_url_filter,
    after_model_url_scanner,
)


# ═══════════════════════════════════════════════════════════════
#  TOOL: Guardar reporte en Markdown (cross-platform)
# ═══════════════════════════════════════════════════════════════

def save_research_to_markdown(topic: str, report_content: str) -> str:
    """
    Guarda el reporte de investigación en un archivo .md.
    Compatible con Windows, Mac y Linux.

    Args:
        topic: Tema investigado (nombre del archivo).
        report_content: Contenido completo del reporte.

    Returns:
        Mensaje con la ruta guardada o error.
    """

    def clean_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in text.split("\n")]
        cleaned, blank_count = [], 0
        for line in lines:
            if line == "":
                blank_count += 1
                if blank_count <= 1:
                    cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)
        return "\n".join(cleaned).strip()

    def fix_tables(text: str) -> str:
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                if result and result[-1].strip() != "":
                    result.append("")
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                has_sep = any(
                    re.match(r"^\|[\s\-\|:]+\|$", tl.strip())
                    for tl in table_lines
                )
                if not has_sep and len(table_lines) >= 2:
                    cols = len([c for c in table_lines[0].split("|") if c.strip()])
                    table_lines.insert(1, "| " + " | ".join(["---"] * cols) + " |")
                result.extend(table_lines)
                result.append("")
                continue
            else:
                result.append(lines[i])
                i += 1
        return "\n".join(result)

    # Nombre de archivo seguro (cross-platform)
    safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", topic)
    safe_name = safe_name.strip().replace(" ", "_")[:80] or "investigacion"
    fecha = datetime.now().strftime("%Y-%m-%d")
    filename = f"{safe_name}_{fecha}.md"

    # Directorio cross-platform con pathlib
    output_dir = Path.home() / "Documents" / "investigaciones"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = (
        f"# Investigación: {topic}\n\n"
        f"> **Generado el:** {now_str}  \n"
        f"> **Herramienta:** Research Agent (Google ADK)  \n\n"
        f"---\n\n"
        f"{fix_tables(clean_text(report_content))}\n\n"
        f"---\n\n*Fin del reporte — {topic} — {fecha}*\n"
    )

    try:
        file_path.write_text(md_content, encoding="utf-8")
        print(f"[SAVE] ✅ Guardado: {file_path}")
        return (
            f"✅ Reporte guardado exitosamente.\n"
            f"📁 Ruta: {file_path}\n"
            f"📄 Archivo: {filename}"
        )
    except Exception as e:
        print(f"[SAVE] ❌ Error: {e}")
        return f"❌ Error al guardar: {e}"


save_markdown_tool = FunctionTool(func=save_research_to_markdown)


# ═══════════════════════════════════════════════════════════════
#  CALLBACKS (SearchAgent)
# ═══════════════════════════════════════════════════════════════

BLOCKED_TOPICS = ["desinformación", "fake news", "propaganda", "manipulación masiva"]


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    last_user_msg = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == "user":
                for part in content.parts:
                    if hasattr(part, "text") and part.text:
                        last_user_msg = part.text
                        break
                break

    print(f"\n[SEARCH] Tema: {last_user_msg[:120]}...")

    if any(t in last_user_msg.lower() for t in BLOCKED_TOPICS):
        return LlmResponse(
            content=Content(
                role="model",
                parts=[Part(text="Este tema no está permitido.")],
            )
        )
    return before_model_url_filter(callback_context, llm_request)


def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    print(f"[SEARCH] Escaneando URLs en respuesta...")
    return after_model_url_scanner(callback_context, llm_response)


# ═══════════════════════════════════════════════════════════════
#  AGENTE 1 – SearchAgent
#  output_key="research_report" → escribe resultado en session.state
# ═══════════════════════════════════════════════════════════════

search_agent = LlmAgent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    output_key="research_report",          # ← guarda output en session.state
    instruction="""
Eres un agente de investigación periodística. Investiga el tema recibido
y genera un reporte completo con EXACTAMENTE estas secciones:

## Resumen Ejecutivo
(3-5 oraciones con los hallazgos más importantes)

## Hallazgos Principales
(datos, hechos y argumentos clave)

## Fuentes Consultadas
(título, autor, fecha, URL completa, credibilidad 1-5 estrellas, aportación)

## Perspectivas y Debate
(distintos puntos de vista o controversias)

## Datos Estadísticos Relevantes
(cifras y porcentajes con sus fuentes)

## Recomendaciones para el Artículo
(ángulos, titulares o argumentos sugeridos)

Prioriza: PubMed, arXiv, Reuters, AP, BBC, NYT, El País, ONU, OMS, World Bank.
Descarta: blogs sin autoría, redes sociales sin verificar.
Indica siempre si algo es opinión vs. hecho verificado.
""",
    description="Investiga con Google Search y genera reporte estructurado.",
    tools=[google_search],
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)


# ═══════════════════════════════════════════════════════════════
#  AGENTE 2 – SaverAgent
#  Lee {research_report} desde session.state vía instruction template
# ═══════════════════════════════════════════════════════════════

saver_agent = LlmAgent(
    name="SaverAgent",
    model="gemini-2.5-flash",
    instruction="""
El siguiente reporte fue generado por el agente de investigación:

{research_report}

Tu única tarea:
1. Identificar el tema principal del reporte (primera línea o título).
2. Llamar a save_research_to_markdown con:
   - topic: el tema identificado (texto corto, sin caracteres especiales)
   - report_content: el reporte completo tal como aparece arriba
3. Responder al usuario con la ruta donde quedó guardado el archivo.
""",
    description="Guarda el reporte en un archivo .md.",
    tools=[save_markdown_tool],
)


# ═══════════════════════════════════════════════════════════════
#  ROOT AGENT – Pipeline secuencial
# ═══════════════════════════════════════════════════════════════

investigacion = SequentialAgent(
    name="ResearchAgent",
    description=(
        "Investiga fuentes fidedignas con Google Search "
        "y guarda el reporte automáticamente en ~/Documents/investigaciones/"
    ),
    sub_agents=[search_agent, saver_agent],
)

agent = investigacion

adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="app_investigacion_fuentes_luma",
    user_id="investigador_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)





