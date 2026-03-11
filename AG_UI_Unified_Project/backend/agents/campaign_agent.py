"""
Marketing Campaign Agent
Pipeline: PLANEA > ESCRIBE > EJECUTA > GUARDA en .md
"""

import re
from datetime import datetime
from pathlib import Path
from google.adk.tools import FunctionTool
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.llm_agent import LlmAgent
from google.genai import types

GEMINI_MODEL = "gemini-2.0-flash"

def save_to_markdown(
    product_name: str,
    buyer_persona: str,
    keywords_and_competition: str,
    ad_content: str,
    measurement_plan: str
) -> str:
    """Guarda el contenido completo de la campaña en un archivo .md."""
    def clean_text(text: str) -> str:
        if not text: return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in text.split("\n")]
        cleaned = []
        blank_count = 0
        for line in lines:
            if line == "":
                blank_count += 1
                if blank_count <= 1: cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)
        return "\n".join(cleaned).strip()

    safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", product_name)
    safe_name = safe_name.strip().replace(" ", "_") or "campaña"
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    filename = f"{safe_name}_{fecha_actual}.md"
    output_dir = Path.home() / "Documents" / "resultados_campanas"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"# 📊 Campaña de Marketing: {product_name}\n\n> **Generado el:** {now_str}\n\n"
    md_content += f"## 👤 Buyer Persona\n\n{clean_text(buyer_persona)}\n\n---\n"
    md_content += f"## 🔍 Keywords\n\n{clean_text(keywords_and_competition)}\n\n---\n"
    md_content += f"## 📝 Anuncios\n\n{clean_text(ad_content)}\n\n---\n"
    md_content += f"## 📈 Plan de Medición\n\n{clean_text(measurement_plan)}\n\n---\n"

    try:
        file_path.write_text(md_content, encoding="utf-8")
        return f"✅ Archivo guardado: {filename}"
    except Exception as e:
        return f"❌ Error: {e}"

save_markdown_tool = FunctionTool(func=save_to_markdown)

buyer_persona_agent = LlmAgent(
    name="BuyerPersonaAgent",
    model=GEMINI_MODEL,
    instruction="Crea un Buyer Persona detallado para el producto/servicio.",
    output_key="buyer_persona"
)

keywords_agent = LlmAgent(
    name="KeywordsAndCompetitionAgent",
    model=GEMINI_MODEL,
    instruction="Genera keywords long tail y análisis de competencia basado en {buyer_persona}.",
    output_key="keywords_and_competition"
)

ad_writer_agent = LlmAgent(
    name="AdWriterAgent",
    model=GEMINI_MODEL,
    instruction="Redacta anuncios y scripts basados en {buyer_persona} y {keywords_and_competition}.",
    output_key="ad_content"
)

measurement_plan_agent = LlmAgent(
    name="MeasurementPlanAgent",
    model=GEMINI_MODEL,
    instruction="Crea el plan de medición digital basado en {buyer_persona} y {ad_content}.",
    output_key="measurement_plan"
)

save_agent = LlmAgent(
    name="SaveMarkdownAgent",
    model=GEMINI_MODEL,
    tools=[save_markdown_tool],
    instruction="Llama a `save_to_markdown` con el contenido generado. Argumentos: product_name, buyer_persona={buyer_persona}, keywords_and_competition={keywords_and_competition}, ad_content={ad_content}, measurement_plan={measurement_plan}.",
)

agent = SequentialAgent(
    name="campaign_expert",
    sub_agents=[buyer_persona_agent, keywords_agent, ad_writer_agent, measurement_plan_agent, save_agent],
    description="Pipeline completo de creación de campañas de marketing.",
)
