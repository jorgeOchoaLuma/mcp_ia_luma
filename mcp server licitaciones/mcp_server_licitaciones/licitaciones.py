from typing import Any
import httpx
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("licitaciones")

# Constants
LICITACIONES_API_BASE = "https://dev.lumacloud.co/apilic"
USER_AGENT = "licitaciones-app/1.0"


async def make_licitaciones_request(url: str, method: str = "GET", data: dict = None) -> dict[str, Any] | None:
    """Make a request to the Licitaciones API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, timeout=30.0)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
            else:
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


@mcp.tool()
async def listar_licitaciones() -> str:
    """Listar todas las licitaciones disponibles.
    
    Returns:
        Lista de todas las licitaciones en el sistema
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones"
    data = await make_licitaciones_request(url)
    
    if not data:
        return "No se pudieron obtener las licitaciones."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_licitacion_completa(licitacion_id: str) -> str:
    """Obtener información completa de una licitación específica.
    
    Args:
        licitacion_id: ID de la licitación a consultar
        
    Returns:
        Información completa de la licitación
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/completo"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudo obtener la licitación con ID {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def ver_correo_licitacion(licitacion_id: str) -> str:
    """Ver el correo original de una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Contenido del correo original de la licitación
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/correo"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudo obtener el correo de la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_detalles_licitacion(licitacion_id: str) -> str:
    """Obtener detalles específicos de una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Detalles de la licitación
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/detalles"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los detalles de la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_documentos_requeridos(licitacion_id: str) -> str:
    """Obtener la lista de documentos requeridos para una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Lista de documentos requeridos
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/documentos_requeridos"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los documentos requeridos para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def cambiar_estado_licitacion(licitacion_id: str, nuevo_estado: str) -> str:
    """Cambiar el estado de una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        nuevo_estado: Nuevo estado para la licitación (ej: "abierta", "cerrada", "en_evaluacion", "adjudicada")
        
    Returns:
        Confirmación del cambio de estado
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/estado"
    payload = {"estado": nuevo_estado}
    data = await make_licitaciones_request(url, method="POST", data=payload)
    
    if not data:
        return f"No se pudo cambiar el estado de la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_requisitos_experiencia(licitacion_id: str) -> str:
    """Obtener los requisitos de experiencia para una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Requisitos de experiencia solicitados
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/experiencia"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los requisitos de experiencia para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_requisitos_financieros(licitacion_id: str) -> str:
    """Obtener los requisitos financieros para una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Requisitos financieros solicitados
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/financiero"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los requisitos financieros para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_requisitos_hv(licitacion_id: str) -> str:
    """Obtener los requisitos de hojas de vida para una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Requisitos de hojas de vida del equipo de trabajo
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/hv"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los requisitos de HV para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_resumen_ia(licitacion_id: str) -> str:
    """Obtener un resumen generado por IA de una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Resumen inteligente de la licitación
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/resumen_ia"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudo obtener el resumen IA para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_requisitos_tecnicos(licitacion_id: str) -> str:
    """Obtener los requisitos técnicos de una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Especificaciones y requisitos técnicos
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/tecnicos"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los requisitos técnicos para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
async def obtener_criterios_puntaje(licitacion_id: str) -> str:
    """Obtener los criterios de evaluación y puntaje de una licitación.
    
    Args:
        licitacion_id: ID de la licitación
        
    Returns:
        Criterios de evaluación y distribución de puntaje
    """
    url = f"{LICITACIONES_API_BASE}/api/licitaciones/{licitacion_id}/puntaje"
    data = await make_licitaciones_request(url)
    
    if not data:
        return f"No se pudieron obtener los criterios de evaluación para la licitación {licitacion_id}."
    
    if "error" in data:
        return f"Error: {data['error']}"
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    """Initialize and run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()