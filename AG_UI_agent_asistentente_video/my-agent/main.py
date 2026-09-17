"""
Agente de Producción de Contenido Educativo
Gestiona el flujo de creación de videos sobre IA para audiencias no técnicas

Incluye generación real de imágenes para el paso 3 (Ayudas Visuales),
usando el modelo de imagen de Gemini (Nano Banana 2) y el framework de
5 dimensiones (Sujeto | Acción | Ubicación | Estilo | Composición).

Flujo híbrido (Entrada Estructural -> Motor LLM -> Inyección de Estilo -> Render):
el "Motor LLM" que traduce las 5 dimensiones en narrativa se hace en LOTE
(una sola llamada para todas las filas del video), no una llamada por imagen.

Estilo y aspect_ratio se eligen en un solo paso (componente
configurarAyudasVisuales en el frontend). Todas las imágenes se muestran
con UNA sola llamada al componente visualAidGallery, nunca con markdown
ni con múltiples llamadas paralelas por imagen.

Almacenamiento de imágenes: si GCS_BUCKET_NAME está configurado, las
imágenes se suben a un bucket PRIVADO de Cloud Storage y se sirven a
través de nuestro propio endpoint /images/{id}.png (proxy) — el usuario
nunca ve la URL real de GCS. Sin GCS_BUCKET_NAME, cae a un diccionario
en memoria (solo válido para desarrollo local, un único proceso).
"""

import os
import json
import uuid
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset
from google.adk.agents.llm_agent import LlmAgent
from google.adk.apps import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google import genai
from google.genai import types
from google.cloud import storage
from dotenv import load_dotenv
load_dotenv()


# =========================
# BIGQUERY PLUGIN CONFIG
# =========================

PROJECT_ID  = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASET_ID  = os.environ["BQ_DATASET_ID"]
BQ_LOCATION = os.environ.get("BQ_LOCATION", "US")

bq_plugin = BigQueryAgentAnalyticsPlugin(
    project_id=PROJECT_ID,
    dataset_id=DATASET_ID,
    location=BQ_LOCATION,
    config=BigQueryLoggerConfig(
        batch_size=1,
        batch_flush_interval=0.5,
        log_session_metadata=True,
        auto_schema_upgrade=True,
        create_views=True,
    ),
)


# =========================
# CLIENTE DE GENERACIÓN DE IMÁGENES (Vertex AI / Nano Banana 2)
# =========================

VERTEX_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
IMAGE_MODEL_ID = os.environ.get("IMAGE_MODEL_ID", "gemini-3.1-flash-image-preview")
EVAL_MODEL_ID = os.environ.get("EVAL_MODEL_ID", "gemini-3-flash-preview")

IMAGE_QUALITY_THRESHOLD = float(os.environ.get("IMAGE_QUALITY_THRESHOLD", "3.5"))

ALLOWED_ASPECT_RATIOS = {
    "16:9": "Horizontal — YouTube, presentaciones, video para escritorio",
    "9:16": "Vertical — Reels, TikTok, YouTube Shorts",
    "1:1":  "Cuadrado — feed de Instagram, Facebook y LinkedIn",
    "4:3":  "Horizontal clásico — formatos de presentación tradicionales",
    "3:4":  "Vertical clásico — carruseles de redes sociales",
}
DEFAULT_ASPECT_RATIO = "16:9"

BRAND_REFERENCE_IMAGE = os.environ.get("BRAND_REFERENCE_IMAGE")
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")

# =========================
# ALMACENAMIENTO DE IMÁGENES (GCS privado con proxy, o memoria local)
# =========================

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
storage_client = storage.Client(project=PROJECT_ID) if GCS_BUCKET_NAME else None

# Fallback en memoria SOLO si no hay bucket configurado (desarrollo local
# sin GCS). En producción con múltiples instancias, siempre usa GCS.
IMAGE_STORE: dict[str, bytes] = {}


def _guardar_imagen(image_bytes: bytes, image_id: str) -> str:
    """
    Sube la imagen a un bucket PRIVADO de Cloud Storage (si está
    configurado) o la guarda en memoria como fallback local. En ambos
    casos devuelve la URL de NUESTRO backend, no la de GCS — el usuario
    nunca ve la URL real del bucket; el endpoint /images/{id}.png actúa
    de proxy y descarga el archivo del lado del servidor.
    """
    if storage_client:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(f"ayudas-visuales/{image_id}.png")
        blob.upload_from_string(image_bytes, content_type="image/png")
    else:
        IMAGE_STORE[image_id] = image_bytes

    return f"{BACKEND_BASE_URL}/images/{image_id}.png"


genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=VERTEX_LOCATION,
)

EVAL_CRITERIA = [
    "prompt_adherence",
    "visual_quality",
    "claridad_educativa",
    "coherencia_marca",
]

EVAL_PROMPT_TEMPLATE = """
Eres un evaluador experto de imagenes para contenido educativo corporativo.
Evalua esta imagen frente a la descripcion: "{descripcion}"

Contexto: la imagen se usara como ayuda visual en un video educativo sobre
IA para audiencias NO tecnicas de empresas. Debe ser clara, profesional,
sin texto renderizado dentro de la imagen, y coherente con una estetica
de marca minimalista corporativa.

Califica cada criterio de 1 a 5 y explica brevemente:
- prompt_adherence: la imagen refleja el sujeto y la accion descritos.
- visual_quality: nitidez, composicion, iluminacion.
- claridad_educativa: una audiencia no tecnica entenderia el concepto solo con la imagen.
- coherencia_marca: estilo minimalista/corporativo, sin texto renderizado dentro de la imagen.

Devuelve UNICAMENTE JSON valido, sin texto adicional ni markdown:
{{
  "prompt_adherence": {{"score": X, "explicacion": "..."}},
  "visual_quality": {{"score": X, "explicacion": "..."}},
  "claridad_educativa": {{"score": X, "explicacion": "..."}},
  "coherencia_marca": {{"score": X, "explicacion": "..."}},
  "overall_score": X,
  "resumen": "..."
}}
"""


# =========================
# TOOL IMPLEMENTATIONS: RESUMEN / GUION
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


# =========================
# PASO 1: TABLA DE MOMENTOS (Entrada Estructural)
# =========================

TABLA_PROMPT_TEMPLATE = """
Eres un director de arte para contenido educativo corporativo sobre IA.
Analiza esta transcripción y genera una lista de momentos clave del video
(mínimo 5) para crear ayudas visuales.

Transcripción:
{transcripcion}

Para cada momento, define:
- momento: identificador con tiempo aproximado (ej. "Introducción 0:00-0:15")
- elemento_visual: qué se debe mostrar (sujeto de la imagen)
- texto_overlay: texto corto que se superpondrá en edición (NO debe ir dentro de la imagen)
- composicion: el encuadre más adecuado para ESE momento (ej. "Plano general,
  vista establecedora", "Vista cenital tipo diagrama", "Primer plano,
  profundidad de campo baja", "Plano medio, tiro a nivel del ojo"). Varía
  la composición según el tipo de momento, no repitas siempre lo mismo.

Devuelve UNICAMENTE un JSON array valido, sin texto adicional ni markdown:
[
  {{"momento": "...", "elemento_visual": "...", "texto_overlay": "...", "composicion": "..."}}
]
"""


def _generar_tabla_momentos(transcripcion: str) -> list[dict]:
    response = genai_client.models.generate_content(
        model=EVAL_MODEL_ID,
        contents=[TABLA_PROMPT_TEMPLATE.format(transcripcion=transcripcion)],
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


# =========================
# PASO 2: MOTOR LLM EN LOTE (traduce TODAS las filas a narrativa en 1 llamada)
# =========================

ESTILO_PRESETS = {
    "minimalista_corporativo": {
        "etiqueta": "Minimalista corporativo",
        "descripcion": (
            "Ilustración educativa profesional, paleta de marca corporativa, "
            "iluminación blanca uniforme, estética minimalista y moderna"
        ),
    },
    "ilustracion_flat": {
        "etiqueta": "Ilustración flat",
        "descripcion": (
            "Ilustración vectorial flat design, colores planos vibrantes, "
            "formas geométricas simples, sin sombras complejas"
        ),
    },
    "fotorrealista": {
        "etiqueta": "Fotorrealista",
        "descripcion": (
            "Fotografía profesional de estudio, iluminación suave y realista, "
            "alta definición, ambiente corporativo auténtico"
        ),
    },
    "isometrico": {
        "etiqueta": "Isométrico técnico",
        "descripcion": (
            "Ilustración isométrica técnica, paleta de colores fría y "
            "tecnológica, líneas limpias, estilo diagrama de producto"
        ),
    },
}
DEFAULT_ESTILO_ID = "minimalista_corporativo"

UBICACION_BASE = "Fondo limpio, entorno corporativo minimalista, sin distractores"


def _resolver_estilo(estilo_id: str) -> str:
    preset = ESTILO_PRESETS.get(estilo_id, ESTILO_PRESETS[DEFAULT_ESTILO_ID])
    return preset["descripcion"]


ENRIQUECIMIENTO_BATCH_TEMPLATE = """
Eres un director de arte traduciendo especificaciones técnicas en
descripciones narrativas para un generador de imágenes.

Estilo de marca (fijo para todas las imágenes de este video): {estilo}
Ubicación base (fija para todas las imágenes de este video): {ubicacion}

Para cada uno de los siguientes momentos, escribe un párrafo narrativo
cohesivo (NO lista, NO bullets) que combine su Sujeto, Acción, la
Ubicación y el Estilo fijos de arriba, y su Composición específica.
No menciones ni incluyas el texto_overlay dentro de la descripción
visual — ese texto se superpone después en edición, la imagen no debe
contener ningún texto renderizado. No incluyas nombres de marcas,
empresas o logos específicos, aunque la transcripción los mencione —
genera imágenes conceptuales y genéricas.

Momentos:
{momentos_json}

Devuelve UNICAMENTE un JSON array válido, sin texto adicional ni
markdown, con un objeto por momento en el MISMO ORDEN de entrada:
[
  {{"momento": "...", "prompt_narrativo": "..."}}
]
"""


def _enriquecer_prompts_batch(filas: list[dict], estilo_texto: str) -> dict[str, str]:
    momentos_input = [
        {
            "momento": fila.get("momento", ""),
            "sujeto": fila.get("elemento_visual", ""),
            "composicion": fila.get("composicion", "Plano medio, tiro a nivel del ojo"),
        }
        for fila in filas
    ]

    instruccion = ENRIQUECIMIENTO_BATCH_TEMPLATE.format(
        estilo=estilo_texto,
        ubicacion=UBICACION_BASE,
        momentos_json=json.dumps(momentos_input, ensure_ascii=False),
    )

    try:
        response = genai_client.models.generate_content(
            model=EVAL_MODEL_ID,
            contents=[instruccion],
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        resultados = json.loads(text)
        return {r["momento"]: r["prompt_narrativo"] for r in resultados if "momento" in r}
    except Exception:
        return {}


def _construir_prompt_fallback(
    momento: str, elemento_visual: str, texto_overlay: str, composicion: str,
    estilo_texto: str,
) -> str:
    return f"""
Sujeto: {elemento_visual}
Acción: {momento}
Ubicación: {UBICACION_BASE}
Estilo: {estilo_texto}
Composición: {composicion}

Nota importante: NO incluyas ningún texto, letras ni overlays dentro
de la imagen. El texto "{texto_overlay}" se superpondrá después en
edición de video, no debe aparecer renderizado en la imagen. No
incluyas nombres de marcas, empresas o logos específicos.
""".strip()


def _aplicar_correccion_prompt(prompt_narrativo: str, feedback: str) -> str:
    return f"{prompt_narrativo}\n\nCorrección requerida antes de aceptar la imagen: {feedback}"


# =========================
# ORQUESTADOR PRINCIPAL: TABLA + IMÁGENES
# =========================

def generar_ayudas_visuales(
    transcripcion: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    estilo_id: str = DEFAULT_ESTILO_ID,
) -> dict:
    """
    Genera la tabla de momentos del video Y las imágenes reales de apoyo
    para cada momento, EN UNA SOLA LLAMADA.

    aspect_ratio: "16:9", "9:16", "1:1", "4:3" o "3:4". Debe obtenerse del
    componente configurarAyudasVisuales si aún no se ha indicado.

    estilo_id: "minimalista_corporativo", "ilustracion_flat", "fotorrealista"
    o "isometrico". Debe obtenerse del componente configurarAyudasVisuales
    si aún no se ha indicado.
    """
    try:
        filas = _generar_tabla_momentos(transcripcion)
    except Exception as e:
        return {"status": "error", "mensaje": f"No se pudo generar la tabla de momentos: {e}"}

    estilo_texto = _resolver_estilo(estilo_id)
    prompts_narrativos = _enriquecer_prompts_batch(filas, estilo_texto)

    imagenes = []
    for fila in filas:
        resultado = generar_imagen_visual(
            momento=fila.get("momento", ""),
            elemento_visual=fila.get("elemento_visual", ""),
            texto_overlay=fila.get("texto_overlay", ""),
            composicion=fila.get("composicion", "Plano medio, tiro a nivel del ojo"),
            aspect_ratio=aspect_ratio,
            estilo_id=estilo_id,
            prompt_narrativo_precalculado=prompts_narrativos.get(fila.get("momento", "")),
        )
        imagenes.append(resultado)

    return {
        "status": "success",
        "tipo": "ayudas_visuales",
        "formato": "tabla_con_imagenes",
        "filas": filas,
        "imagenes": imagenes,
        "instruccion": (
            "OBLIGATORIO: llama UNA SOLA VEZ al componente visualAidGallery, "
            "pasando el array completo de 'imagenes' tal cual (con sus campos "
            "momento, elemento_visual, texto_overlay, image_url y "
            "requiere_revision). PROHIBIDO llamar a visualAidCard por "
            "separado o llamar a visualAidGallery más de una vez, generar "
            "markdown, o describir las imágenes en prosa. Si alguna imagen "
            "tiene status='error', indícalo brevemente en texto y sigue "
            "con las demás."
        ),
    }


# =========================
# GENERACIÓN + EVALUACIÓN POR IMAGEN
# =========================

def _generar_imagen_bytes(prompt: str, aspect_ratio: str) -> bytes | None:
    contents = [prompt]
    if BRAND_REFERENCE_IMAGE and os.path.exists(BRAND_REFERENCE_IMAGE):
        with open(BRAND_REFERENCE_IMAGE, "rb") as f:
            reference_bytes = f.read()
        contents = [
            types.Part.from_bytes(data=reference_bytes, mime_type="image/png"),
            "Usa la imagen anterior únicamente como guía de estilo y paleta de color. "
            + prompt,
        ]

    response = genai_client.models.generate_content(
        model=IMAGE_MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
            ),
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data
    return None


def _evaluar_imagen(image_bytes: bytes, descripcion: str) -> dict:
    response = genai_client.models.generate_content(
        model=EVAL_MODEL_ID,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            EVAL_PROMPT_TEMPLATE.format(descripcion=descripcion),
        ],
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


def generar_imagen_visual(
    momento: str,
    elemento_visual: str,
    texto_overlay: str,
    composicion: str,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    estilo_id: str = DEFAULT_ESTILO_ID,
    prompt_narrativo_precalculado: str | None = None,
) -> dict:
    """
    Genera la imagen real de apoyo para UNA fila de la tabla de ayudas visuales,
    usando el modelo de imagen de Gemini (Nano Banana 2), y la evalúa
    automáticamente antes de entregarla.
    """
    descripcion = f"{elemento_visual} — {momento}"

    aspect_ratio_aviso = None
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        aspect_ratio_aviso = (
            f"'{aspect_ratio}' no es un aspect_ratio soportado, se usó "
            f"'{DEFAULT_ASPECT_RATIO}' en su lugar."
        )
        aspect_ratio = DEFAULT_ASPECT_RATIO

    try:
        prompt_base = prompt_narrativo_precalculado or _construir_prompt_fallback(
            momento, elemento_visual, texto_overlay, composicion,
            _resolver_estilo(estilo_id),
        )

        image_bytes = _generar_imagen_bytes(prompt_base, aspect_ratio)
        if image_bytes is None:
            return {"status": "error", "momento": momento, "mensaje": "El modelo no devolvió datos de imagen."}

        evaluacion = _evaluar_imagen(image_bytes, descripcion)
        intentos = 1

        if evaluacion.get("overall_score", 0) < IMAGE_QUALITY_THRESHOLD:
            feedback = evaluacion.get("resumen", "Mejora la claridad y coherencia con la descripción.")
            prompt_corregido = _aplicar_correccion_prompt(prompt_base, feedback)
            nuevo_bytes = _generar_imagen_bytes(prompt_corregido, aspect_ratio)
            if nuevo_bytes is not None:
                nueva_evaluacion = _evaluar_imagen(nuevo_bytes, descripcion)
                intentos = 2
                if nueva_evaluacion.get("overall_score", 0) >= evaluacion.get("overall_score", 0):
                    image_bytes, evaluacion = nuevo_bytes, nueva_evaluacion

        image_id = uuid.uuid4().hex[:8]
        image_url = _guardar_imagen(image_bytes, image_id)
        requiere_revision = evaluacion.get("overall_score", 0) < IMAGE_QUALITY_THRESHOLD

        resultado = {
            "status": "success",
            "tipo": "imagen_visual",
            "image_id": image_id,
            "momento": momento,
            "elemento_visual": elemento_visual,
            "texto_overlay": texto_overlay,
            "composicion": composicion,
            "aspect_ratio": aspect_ratio,
            "estilo_id": estilo_id,
            "image_url": image_url,
            "intentos": intentos,
            "evaluacion": evaluacion,
            "requiere_revision": requiere_revision,
        }
        if aspect_ratio_aviso:
            resultado["aviso"] = aspect_ratio_aviso
        return resultado

    except Exception as e:
        return {
            "status": "error",
            "momento": momento,
            "mensaje": str(e),
        }


# =========================
# LLM AGENT
# =========================

agui_toolset = AGUIToolset(
    tool_filter=lambda tool, readonly_context=None: tool.name in [
        "configurarAyudasVisuales", "visualAidGallery",
    ]
)

agent = LlmAgent(
    model="gemini-3.1-flash-lite",
    name="Productor_video",
    description="Asistente de producción de contenido para videos educativos sobre IA. Especializado en crear material accesible para audiencias no técnicas de empresas sobre una transcripción o texto.",
    instruction="""Eres el asistente de producción de contenido para el canal educativo sobre Inteligencia Artificial.

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

9. Responde claro y Profesional.

10. Nunca responda que no esta de animo. siempre este dispuesto a ayudar. y de forma profesional.

11. Cuando el usuario pida "Ayudas Visuales":
    a. Si el usuario NO indicó tanto el formato como el estilo, llama
       UNA SOLA VEZ al componente configurarAyudasVisuales (sin
       argumentos).
    b. Con aspect_ratio y estilo_id resueltos, llama a
       generar_ayudas_visuales pasando ambos parámetros.
    c. Con el resultado, llama UNA SOLA VEZ al componente
       visualAidGallery con el array completo de 'imagenes'. PROHIBIDO
       llamar a visualAidGallery más de una vez o llamar a
       visualAidCard individualmente por cada imagen. PROHIBIDO
       markdown o enlaces de texto para mostrar imágenes.
""",
    tools=[
        generar_resumen,
        generar_guion_avatar,
        generar_ayudas_visuales,
        generar_imagen_visual,
        agui_toolset,
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=4000,
    ),
)


# =========================
# ADK APP con el plugin
# =========================

adk_app = App(
    name="Productor_video",
    root_agent=agent,
    plugins=[bq_plugin],
)


# =========================
# ADK AGENT WRAPPER
# =========================

adk_agent = ADKAgent.from_app(
    adk_app,
    user_id="demo_user",
    plugin_close_timeout=10.0,
)


# =========================
# FASTAPI APPLICATION
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_adk_fastapi_endpoint(app, adk_agent)


# =========================
# ENDPOINT DE IMÁGENES GENERADAS (proxy — nunca expone la URL real de GCS)
# =========================

@app.get("/images/{image_id}.png")
async def get_generated_image(image_id: str):
    if storage_client:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(f"ayudas-visuales/{image_id}.png")
        if not blob.exists():
            return Response(status_code=404)
        data = blob.download_as_bytes()
        return Response(content=data, media_type="image/png")

    data = IMAGE_STORE.get(image_id)
    if data is None:
        return Response(status_code=404)
    return Response(content=data, media_type="image/png")


# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": "Productor_video",
        "tools": [
            "generar_resumen",
            "generar_guion_avatar",
            "generar_ayudas_visuales",
            "generar_imagen_visual",
        ],
        "estilos_disponibles": list(ESTILO_PRESETS.keys()),
        "image_model": IMAGE_MODEL_ID,
        "almacenamiento": "gcs" if storage_client else "memoria_local",
        "bigquery_dataset": DATASET_ID,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)