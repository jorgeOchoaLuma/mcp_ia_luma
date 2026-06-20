"""
url_validator.py
─────────────────────────────────────────────────────────────────
Validación de URLs en dos capas:
  1. Lista negra  → dominios conocidos de desinformación/spam
  2. Lista blanca → dominios de alta credibilidad (marcados con ✅)

NO se hacen requests HTTP — el agente puede correr en Vertex AI / Cloud Run
donde no hay salida libre a internet. Google Search ya garantiza que las URLs
existen y son accesibles.
"""

import re
import urllib.parse
from typing import Any, Dict, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


# ═══════════════════════════════════════════════════════════════
#  LISTAS DE DOMINIOS
# ═══════════════════════════════════════════════════════════════

# Bloqueados siempre — fake news, propaganda, spam SEO
BLOCKED_DOMAINS: set[str] = {
    "infowars.com", "naturalnews.com", "beforeitsnews.com",
    "thegatewaypundit.com", "zerohedge.com", "breitbart.com",
    "worldnewsdailyreport.com", "empirenews.net",
    "rt.com", "sputniknews.com",
    "articlesfactory.com", "ezinearticles.com", "hubpages.com",
    "viralnova.com", "distractify.com",
}

# Patrones sospechosos en la URL (regex)
SUSPICIOUS_URL_PATTERNS: list[str] = [
    r"\.tk$", r"\.ml$", r"\.ga$", r"\.cf$",          # TLDs gratis / spam
    r"bit\.ly", r"tinyurl\.com", r"t\.co",             # acortadores
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",            # IPs directas
    r"(hack|crack|keygen)",                             # software ilegal
    r"(adult|xxx|porn|casino|bet|poker)",               # contenido no apto
]

# Dominio de redirección de Google Search grounding (built-in google_search tool).
# No es un dominio "de confianza" en el sentido normal de TRUSTED_DOMAINS —
# es un link de Google que redirige a la fuente real. Google NO expone esa
# URL real en este punto, es intencional (ver
# https://ai.google.dev/gemini-api/docs/google-search), así que se etiqueta
# aparte en vez de quedar sin marca, como pasaba antes.
GOOGLE_GROUNDING_DOMAIN = "vertexaisearch.cloud.google.com"

# Alta confianza — instituciones y medios de referencia
TRUSTED_DOMAINS: set[str] = {
    # Organismos internacionales
    "who.int", "un.org", "worldbank.org", "imf.org", "unicef.org",
    "oecd.org", "fao.org", "unesco.org", "cepal.org",
    # Ciencia y academia
    "nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov",
    "arxiv.org", "scholar.google.com", "jstor.org", "springer.com",
    "sciencedirect.com", "researchgate.net","sciencedirect.com", "incibe.es",
    "asuncion.intedya.com","letslaw.es",
    # Medios de referencia
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "nytimes.com", "theguardian.com", "elpais.com", "lemonde.fr",
    "economist.com", "ft.com", "wsj.com", "bloomberg.com",
    "dw.com", "france24.com", "euronews.com",
    # Datos y estadísticas
    "statista.com", "ourworldindata.org", "data.worldbank.org",
    "ine.es", "inegi.org.mx", "dane.gov.co",
    # TLDs de confianza (gobiernos y educación)
    ".gov", ".gob.mx", ".gob.es", ".gob.ar", ".gob.cl",
    ".gouv.fr", ".gov.uk", ".gov.br",
    ".edu", ".ac.uk", ".edu.mx", ".edu.ar",
}


# ═══════════════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════════════

def _extract_domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def _is_trusted(url: str) -> bool:
    domain = _extract_domain(url)
    return any(domain.endswith(t) for t in TRUSTED_DOMAINS)


def _is_blocked(url: str) -> tuple[bool, str]:
    domain = _extract_domain(url)
    if domain in BLOCKED_DOMAINS:
        return True, f"dominio en lista negra: {domain}"
    for pattern in SUSPICIOUS_URL_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return True, f"patrón sospechoso: {pattern}"
    return False, ""


def _label_url(url: str) -> str:
    """Retorna la etiqueta que se agrega junto a la URL en la respuesta final."""
    blocked, reason = _is_blocked(url)
    if blocked:
        return f"**[⛔ BLOQUEADA: {reason}]**"
    domain = _extract_domain(url)
    if domain == GOOGLE_GROUNDING_DOMAIN:
        # Link de redirección de Google Search grounding. No podemos validar
        # el dominio real de la fuente porque Google no lo expone aquí —
        # es el comportamiento esperado, no un error del agente.
        return "**[🔗 Google Search grounding — redirige a la fuente]**"
    if _is_trusted(url):
        return f"**[✅ Fuente verificada]**"
    return ""  # Sin etiqueta — no está en ninguna lista


# ═══════════════════════════════════════════════════════════════
#  CAPA 1 — before_tool_callback
#  Firma ADK: (BaseTool, dict, ToolContext) -> Optional[dict]
# ═══════════════════════════════════════════════════════════════

def before_tool_callback(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
) -> Optional[Dict]:
    """Limpia URLs bloqueadas del query antes de ejecutar google_search."""
    query: str = args.get("query", "")
    print(f"\n[TOOL↑] query: {query[:80]}")

    for url in re.findall(r"https?://[^\s\"'>]+", query):
        blocked, reason = _is_blocked(url)
        if blocked:
            args["query"] = args["query"].replace(url, "[URL_BLOQUEADA]")
            print(f"[TOOL↑] ⛔ Bloqueada en query: {_extract_domain(url)} — {reason}")

    return None


# ═══════════════════════════════════════════════════════════════
#  CAPA 2 — after_tool_callback
#  Firma ADK: (BaseTool, dict, ToolContext, dict) -> Optional[dict]
# ═══════════════════════════════════════════════════════════════

def after_tool_callback(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict,
) -> Optional[Dict]:
    """Filtra resultados de google_search con dominios bloqueados."""
    tool_name = getattr(tool, "name", str(tool))
    if tool_name != "google_search" or not isinstance(tool_response, dict):
        return None

    results: list = tool_response.get("results", [])
    if not results:
        return None

    filtered, rejected = [], []
    for result in results:
        url = result.get("url", "")
        blocked, reason = _is_blocked(url)
        if blocked:
            rejected.append(url)
            print(f"[TOOL↓] ⛔ Descartado: {_extract_domain(url)} — {reason}")
            continue
        result["_trusted"] = _is_trusted(url)
        result["_domain"] = _extract_domain(url)
        filtered.append(result)

    print(f"[TOOL↓] ✅ {len(filtered)}/{len(results)} resultados válidos | {len(rejected)} descartados")

    return {**tool_response, "results": filtered, "_rejected": rejected}


# ═══════════════════════════════════════════════════════════════
#  CAPA 3 — before_model_url_filter
#  Firma ADK: (CallbackContext, LlmRequest) -> Optional[LlmResponse]
# ═══════════════════════════════════════════════════════════════

def before_model_url_filter(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Elimina URLs bloqueadas del prompt antes de enviarlo al LLM."""
    if not llm_request.contents:
        return None

    count = 0
    for content in llm_request.contents:
        for part in (content.parts or []):
            if not (hasattr(part, "text") and part.text):
                continue
            for url in re.findall(r"https?://[^\s\"'>]+", part.text):
                blocked, _ = _is_blocked(url)
                if blocked:
                    part.text = part.text.replace(url, f"[FUENTE_NO_VALIDA:{_extract_domain(url)}]")
                    count += 1

    if count:
        print(f"[MODEL↑] 🧹 {count} URLs bloqueadas eliminadas del prompt")

    return None


# ═══════════════════════════════════════════════════════════════
#  CAPA 4 — after_model_url_scanner
#  Firma ADK: (CallbackContext, LlmResponse) -> Optional[LlmResponse]
# ═══════════════════════════════════════════════════════════════

def after_model_url_scanner(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """Etiqueta URLs en la respuesta final. Sin requests HTTP."""

    # ── DIAGNÓSTICO TEMPORAL ─────────────────────────────────────────
    # Descomenta estas 3 líneas una vez para confirmar si tu versión de
    # ADK sí está poblando grounding_chunks/grounding_supports con la tool
    # nativa google_search (hay un bug conocido donde quedan en None:
    # https://github.com/google/adk-python/issues/3287).
    # gm = getattr(llm_response, "grounding_metadata", None)
    # if gm:
    #     print(f"[DEBUG grounding_metadata] chunks={gm.grounding_chunks!r} supports={gm.grounding_supports!r}")

    if not (llm_response.content and llm_response.content.parts):
        return llm_response

    stats = {"trusted": 0, "blocked": 0, "grounding": 0}

    for part in llm_response.content.parts:
        if not (hasattr(part, "text") and part.text):
            continue

        urls = list(dict.fromkeys(re.findall(r"https?://[^\s\)\]\"'>]+", part.text)))
        for url in urls:
            label = _label_url(url)
            if label:  # solo reemplazar si tiene etiqueta
                part.text = part.text.replace(url, f"{url} {label}")
            if "⛔" in label:
                stats["blocked"] += 1
            elif "✅" in label:
                stats["trusted"] += 1
            elif "🔗" in label:
                stats["grounding"] += 1

        # Resumen al final
        total = sum(stats.values())
        if total > 0:
            part.text += (
                f"\n\n---\n"
                f"**Validación de fuentes:** "
                f"✅ {stats['trusted']} verificadas · "
                f"🔗 {stats['grounding']} vía Google Search grounding · "
                f"⛔ {stats['blocked']} bloqueadas"
            )
        break

    return llm_response