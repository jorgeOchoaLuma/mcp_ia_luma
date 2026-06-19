"""
Vertex AI Search (Discovery Engine) con manejo de errores IAM.
Evita que un 403 PERMISSION_DENIED tumbe todo el agente.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import google.auth
import google.auth.transport.requests
import httpx
from google.adk.tools.function_tool import FunctionTool

log = logging.getLogger(__name__)

# Discovery Engine datastores suelen estar en `global`, no en us-central1.
VERTEX_SEARCH_LOCATION = os.getenv("VERTEX_SEARCH_LOCATION", "global")


def build_datastore_path(project_id: str, datastore_id: str) -> str:
    return (
        f"projects/{project_id}/locations/{VERTEX_SEARCH_LOCATION}"
        f"/collections/default_collection/dataStores/{datastore_id}"
    )


def _access_token() -> str:
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def _format_results(payload: dict[str, Any]) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for item in payload.get("results", []):
        doc = item.get("document", {})
        derived = doc.get("derivedStructData", {})
        snippets = derived.get("snippets") or []
        snippet_text = snippets[0].get("snippet", "") if snippets else ""
        formatted.append(
            {
                "title": str(derived.get("title", "")),
                "link": str(derived.get("link", "")),
                "snippet": snippet_text,
            }
        )
    return formatted


def make_search_tool(project_id: str, datastore_id: str) -> FunctionTool:
    """Crea FunctionTool de búsqueda segura para un datastore."""

    datastore_path = build_datastore_path(project_id, datastore_id)
    serving_config = f"{datastore_path}/servingConfigs/default_search"
    search_url = f"https://discoveryengine.googleapis.com/v1/{serving_config}:search"

    log.info("[vertex_search] datastore=%s location=%s", datastore_id, VERTEX_SEARCH_LOCATION)

    def search_internal_documents(query: str) -> dict[str, Any]:
        """
        Busca en documentos internos de Luma Cloud (Vertex AI Search).

        Args:
            query: Pregunta o términos de búsqueda del usuario.

        Returns:
            Resultados con snippets o mensaje de no encontrado / error de permisos.
        """
        if not query or not query.strip():
            return {
                "status": "empty_query",
                "results": [],
                "message": "No encontré información sobre esto en los documentos.",
            }

        try:
            token = _access_token()
            response = httpx.post(
                search_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"query": query.strip(), "pageSize": 8},
                timeout=30.0,
            )

            if response.status_code == 403:
                log.error(
                    "[vertex_search] 403 PERMISSION_DENIED — falta roles/discoveryengine.user "
                    "en la service account para %s",
                    serving_config,
                )
                return {
                    "status": "permission_denied",
                    "results": [],
                    "message": "No encontré información sobre esto en los documentos.",
                    "hint": (
                        "Asignar roles/discoveryengine.user a la service account en GCP "
                        f"para {datastore_path}"
                    ),
                }

            response.raise_for_status()
            results = _format_results(response.json())
            if not results:
                return {
                    "status": "no_results",
                    "results": [],
                    "message": "No encontré información sobre esto en los documentos.",
                }

            return {"status": "ok", "results": results, "count": len(results)}

        except httpx.HTTPStatusError as exc:
            log.error("[vertex_search] HTTP %s: %s", exc.response.status_code, exc)
            return {
                "status": "error",
                "results": [],
                "message": "No encontré información sobre esto en los documentos.",
            }
        except Exception as exc:
            log.error("[vertex_search] error: %s", exc)
            return {
                "status": "error",
                "results": [],
                "message": "No encontré información sobre esto en los documentos.",
            }

    return FunctionTool(func=search_internal_documents)
