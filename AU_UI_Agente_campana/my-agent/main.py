# ./adk_agent_samples/mcp_agent/agent.py
from google.adk.tools import FunctionTool
from google.adk.agents.sequential_agent import SequentialAgent
from dotenv import load_dotenv
import os
import re
from datetime import datetime
from pathlib import Path


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types





load_dotenv()
GEMINI_MODEL = "gemini-2.5-flash"


# =============================================================================
# TOOL: Guardar en Markdown (Cross-platform + Formato limpio)
# =============================================================================
def save_to_markdown(
    product_name: str,
    buyer_persona: str,
    keywords_and_competition: str,
    ad_content: str,
    measurement_plan: str
) -> str:
    """
    Guarda el contenido completo de la campaña en un archivo .md bien formateado.
    Compatible con Windows, Mac y Linux.

    Args:
        product_name: Nombre del producto/servicio.
        buyer_persona: Contenido del buyer persona generado.
        keywords_and_competition: Keywords y análisis de competencia.
        ad_content: Anuncios y scripts generados.
        measurement_plan: Plan de medición y resumen ejecutivo.

    Returns:
        Ruta del archivo guardado o mensaje de error.
    """

    def clean_text(text: str) -> str:
        """Limpia y normaliza el texto para un MD bien formateado."""
        if not text:
            return ""
        # Normalizar saltos de línea (Windows \r\n → \n)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Eliminar espacios al inicio/fin de cada línea
        lines = [line.rstrip() for line in text.split("\n")]
        # Colapsar más de 2 líneas vacías consecutivas → máximo 1
        cleaned = []
        blank_count = 0
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
        """
        Asegura que las tablas Markdown tengan el separador de encabezado correcto
        y estén rodeadas de líneas en blanco para renderizarse bien.
        """
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Detectar línea de tabla (empieza y termina con |)
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                # Asegurar línea en blanco antes de la tabla
                if result and result[-1].strip() != "":
                    result.append("")

                # Recolectar todas las líneas de la tabla
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                    i += 1

                # Verificar si tiene separador (fila con ---)
                has_separator = any(
                    re.match(r"^\|[\s\-\|:]+\|$", tl.strip())
                    for tl in table_lines
                )

                if not has_separator and len(table_lines) >= 2:
                    # Insertar separador después del encabezado (fila 0)
                    header = table_lines[0]
                    cols = len([c for c in header.split("|") if c.strip()]) 
                    separator = "| " + " | ".join(["---"] * cols) + " |"
                    table_lines.insert(1, separator)

                result.extend(table_lines)
                # Asegurar línea en blanco después de la tabla
                result.append("")
                continue
            else:
                result.append(line)
                i += 1
        return "\n".join(result)

    def format_section(title: str, content: str, level: int = 2) -> str:
        """Formatea una sección con encabezado y contenido limpio."""
        prefix = "#" * level
        clean = fix_tables(clean_text(content))
        return f"{prefix} {title}\n\n{clean}\n\n---\n"

    # --- Nombre de archivo seguro (cross-platform) ---
    # Eliminar caracteres inválidos en cualquier OS
    safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", product_name)
    safe_name = safe_name.strip().replace(" ", "_") or "campaña"
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    filename = f"{safe_name}_{fecha_actual}.md"

    # --- Directorio de salida (cross-platform con pathlib) ---
    output_dir = Path.home() / "Documents" / "resultados_campanas"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    

    # --- Construcción del Markdown ---
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md_content = f"""# 📊 Campaña de Marketing: {product_name}

> **Generado el:** {now_str}  
> **Herramienta:** Telethor Marketing Agent  

---

"""
    md_content += format_section("👤 Buyer Persona", buyer_persona)
    md_content += "\n"
    md_content += format_section("🔍 Keywords y Análisis de Competencia", keywords_and_competition)
    md_content += "\n"
    md_content += format_section("📝 Anuncios y Contenido Publicitario", ad_content)
    md_content += "\n"
    md_content += format_section("📈 Plan de Medición Digital", measurement_plan)
    md_content += f"\n---\n\n*Fin del reporte — {product_name} — {fecha_actual}*\n"

    # --- Guardar archivo ---
    try:
        file_path.write_text(md_content, encoding="utf-8")
        print(f"✅ Archivo guardado: {file_path}")
        return (
            f"✅ Archivo guardado exitosamente.\n"
            f"📁 Ruta: {file_path}\n"
            f"📄 Nombre: {filename}"
        )
    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        return f"❌ Error al guardar el archivo: {e}"


save_markdown_tool = FunctionTool(func=save_to_markdown)


# =============================================================================
# AGENTES - Etapa 1: PLANEA
# =============================================================================
buyer_persona_agent = LlmAgent(
    name="BuyerPersonaAgent",
    model=GEMINI_MODEL,
    instruction="""
    Eres un experto en marketing digital especializado en crear Buyer Personas.
    
    El usuario te indicará el producto/servicio y la empresa. Basándote en esa información,
    crea un Buyer Persona detallado con la siguiente estructura:

    - **Nombre ficticio del Buyer Persona**
    - **Género**
    - **Edad**
    - **Ubicación**
    - **Estado civil**
    - **Trabajo/Industria**
    - **Intereses**
    - **Comportamientos digitales**
    - **Historial web típico**
    - **10 Términos de búsqueda (long tail keywords)**
    - **7 Puntos de dolor (pain points) profesionales y personales**
    - **7 Objetivos profesionales**
    - **¿Cómo puede ayudarlo el producto/servicio?**

    IMPORTANTE: Usa formato Markdown limpio. Para listas usa guiones (-).
    Separa cada sección con una línea en blanco. No uses caracteres especiales innecesarios.
    """,
    description="Crea el Buyer Persona para el producto/servicio.",
    output_key="buyer_persona"
)

keywords_agent = LlmAgent(
    name="KeywordsAndCompetitionAgent",
    model=GEMINI_MODEL,
    instruction="""
    Eres un experto en SEM y análisis competitivo de marketing digital.

    Buyer Persona de referencia:
    {buyer_persona}

    ## 1. KEYWORDS (Long Tail)
    Presenta una tabla Markdown con EXACTAMENTE este formato (respeta los | y ---):

    | Palabra Clave Sugerida | Intención de Búsqueda | Relevancia |
    |---|---|---|
    | ejemplo keyword long tail | Informacional | Alta |

    Incluye 10 filas de datos reales.

    ## 2. ANÁLISIS DE COMPETENCIA
    Para cada uno de 3 competidores usa este formato:

    ### Competidor 1: [Nombre]
    - **Puntos fuertes:** ...
    - **Puntos débiles:** ...
    - **Sesgos de marketing:** ...
    - **Técnicas de redacción:** ...

    IMPORTANTE: Las tablas deben tener siempre encabezado + fila separadora (---) + datos.
    """,
    description="Genera keywords long tail y análisis de competencia.",
    output_key="keywords_and_competition"
)


# =============================================================================
# AGENTE - Etapa 2: ESCRIBE
# =============================================================================
ad_writer_agent = LlmAgent(
    name="AdWriterAgent",
    model=GEMINI_MODEL,
    instruction="""
    Eres un experto copywriter especializado en Google Ads y scripts de video.

    **BUYER PERSONA:**
    {buyer_persona}

    **KEYWORDS Y COMPETENCIA:**
    {keywords_and_competition}

    ## 1. SCRIPT DEL ANUNCIO (30 segundos)

    **Hook (0-5 seg):** ...  
    **Problema:** ...  
    **Solución:** ...  
    **Beneficios:**
    - Beneficio 1
    - Beneficio 2
    - Beneficio 3

    **CTA:** ...

    ## 2. ANUNCIOS GOOGLE ADS

    Presenta los 3 anuncios con este formato de tabla:

    | Campo | Anuncio 1 | Anuncio 2 | Anuncio 3 |
    |---|---|---|---|
    | Título 1 (máx 30 car) | ... | ... | ... |
    | Título 2 (máx 30 car) | ... | ... | ... |
    | Descripción 1 (máx 90 car) | ... | ... | ... |
    | Descripción 2 (máx 90 car) | ... | ... | ... |
    | Propuesta de valor | ... | ... | ... |

    ## 3. REDES SOCIALES

    ### LinkedIn
    [texto formal, máx 150 palabras]

    ### Instagram
    [texto dinámico con emojis, máx 80 palabras + hashtags]

    IMPORTANTE: Tablas con encabezado + separador (---) + datos. Sin líneas vacías dentro de tablas.
    """,
    description="Redacta anuncios, scripts y contenido de redes sociales.",
    output_key="ad_content"
)


# =============================================================================
# AGENTE - Etapa 3: EJECUTA
# =============================================================================
measurement_plan_agent = LlmAgent(
    name="MeasurementPlanAgent",
    model=GEMINI_MODEL,
    instruction="""
    Eres un experto en analítica digital (metodología Avinash Kaushik).

    **BUYER PERSONA:** {buyer_persona}
    **CONTENIDO CREADO:** {ad_content}

    ## PLAN DE MEDICIÓN

    Presenta la tabla con EXACTAMENTE este formato:

    | Objetivo de Negocio | Meta SMART | KPI Principal | KPI Secundario | Herramienta | Segmento |
    |---|---|---|---|---|---|
    | Awareness | ... | ... | ... | ... | ... |
    | Generación de Leads | ... | ... | ... | ... | ... |
    | Conversión | ... | ... | ... | ... | ... |
    | Retención | ... | ... | ... | ... | ... |

    ## DASHBOARD RECOMENDADO
    - **Métricas en tiempo real:** ...
    - **Frecuencia de reportes:** Diario / Semanal / Mensual
    - **Alertas recomendadas:** ...

    ## RESUMEN EJECUTIVO
    [Máx. 200 palabras integrando: perfil del cliente, propuesta de valor, KPIs clave y próximo paso]

    IMPORTANTE: Tablas con encabezado + separador (---) + datos. Sin líneas vacías dentro de tablas.
    """,
    description="Crea el plan de medición digital y resumen ejecutivo.",
    output_key="measurement_plan"
)


# =============================================================================
# AGENTE - Etapa Final: GUARDAR
# =============================================================================
save_agent = LlmAgent(
    name="SaveMarkdownAgent",
    model=GEMINI_MODEL,
    tools=[save_markdown_tool],
    instruction="""
    Tu única tarea es llamar a la herramienta `save_to_markdown` con estos argumentos:

    - product_name: extrae el nombre del producto/servicio del contexto del buyer persona
    - buyer_persona: {buyer_persona}
    - keywords_and_competition: {keywords_and_competition}
    - ad_content: {ad_content}
    - measurement_plan: {measurement_plan}

    Llama a la herramienta UNA SOLA VEZ y confirma al usuario el resultado con la ruta del archivo.
    No generes contenido adicional.
    """,
    description="Guarda todos los resultados de la campaña en un archivo .md.",
)


# =============================================================================
# AGENTE SECUENCIAL PRINCIPAL
# =============================================================================
marketing_pipeline_agent = SequentialAgent(
    name="MarketingPipelineAgent",
    sub_agents=[
        buyer_persona_agent,
        keywords_agent,
        ad_writer_agent,
        measurement_plan_agent,
        save_agent,
    ],
    description="Pipeline: PLANEA > ESCRIBE > EJECUTA > GUARDA en .md",
)

agent = marketing_pipeline_agent

adk_agent = ADKAgent(
    adk_agent=agent,
    app_name="app_campana",
    user_id="campana_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)


app = FastAPI()
add_adk_fastapi_endpoint(app, adk_agent, path="/")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)




