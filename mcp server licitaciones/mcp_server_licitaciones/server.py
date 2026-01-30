"""
Servidor HTTP para exponer el servidor MCP de licitaciones en Coolify.
El puerto se configura mediante la variable de entorno PORT (Coolify lo maneja automáticamente).
"""
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from licitaciones import (
    listar_licitaciones,
    obtener_licitacion_completa,
    ver_correo_licitacion,
    obtener_detalles_licitacion,
    obtener_documentos_requeridos,
    cambiar_estado_licitacion,
    obtener_requisitos_experiencia,
    obtener_requisitos_financieros,
    obtener_requisitos_hv,
    obtener_resumen_ia,
    obtener_requisitos_tecnicos,
    obtener_criterios_puntaje,
)

app = FastAPI(
    title="MCP Server - Licitaciones",
    description="Servidor MCP para gestión de licitaciones",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para requests
class CambioEstadoRequest(BaseModel):
    nuevo_estado: str

@app.get("/")
async def root():
    """Endpoint raíz del servidor."""
    port = os.getenv("PORT", "8004")
    return {
        "name": "MCP Server - Licitaciones",
        "version": "1.0.0",
        "status": "running",
        "port": port,
        "endpoints": {
            "health": "/health",
            "tools": "/api/tools",
            "listar_licitaciones": "/api/licitaciones",
            "obtener_licitacion": "/api/licitaciones/{licitacion_id}",
        }
    }

@app.get("/health")
async def health():
    """Endpoint de health check para Coolify."""
    return {"status": "healthy", "service": "mcp-licitaciones"}

@app.get("/api/tools")
async def list_tools():
    """Lista todas las herramientas disponibles."""
    return {
        "tools": [
            "listar_licitaciones",
            "obtener_licitacion_completa",
            "ver_correo_licitacion",
            "obtener_detalles_licitacion",
            "obtener_documentos_requeridos",
            "cambiar_estado_licitacion",
            "obtener_requisitos_experiencia",
            "obtener_requisitos_financieros",
            "obtener_requisitos_hv",
            "obtener_resumen_ia",
            "obtener_requisitos_tecnicos",
            "obtener_criterios_puntaje",
        ]
    }

# Endpoints HTTP para las herramientas MCP
def parse_mcp_result(result_str: str):
    """Parsea el resultado de una función MCP que devuelve JSON string."""
    try:
        return json.loads(result_str)
    except json.JSONDecodeError:
        return result_str

@app.get("/api/licitaciones")
async def api_listar_licitaciones():
    """Lista todas las licitaciones disponibles."""
    try:
        result_str = await listar_licitaciones()
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}")
async def api_obtener_licitacion_completa(licitacion_id: str):
    """Obtiene información completa de una licitación."""
    try:
        result_str = await obtener_licitacion_completa(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/correo")
async def api_ver_correo(licitacion_id: str):
    """Obtiene el correo original de una licitación."""
    try:
        result_str = await ver_correo_licitacion(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/detalles")
async def api_obtener_detalles(licitacion_id: str):
    """Obtiene detalles específicos de una licitación."""
    try:
        result_str = await obtener_detalles_licitacion(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/documentos")
async def api_obtener_documentos(licitacion_id: str):
    """Obtiene los documentos requeridos para una licitación."""
    try:
        result_str = await obtener_documentos_requeridos(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/licitaciones/{licitacion_id}/estado")
async def api_cambiar_estado(licitacion_id: str, request: CambioEstadoRequest):
    """Cambia el estado de una licitación."""
    try:
        result_str = await cambiar_estado_licitacion(licitacion_id, request.nuevo_estado)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/experiencia")
async def api_obtener_experiencia(licitacion_id: str):
    """Obtiene los requisitos de experiencia."""
    try:
        result_str = await obtener_requisitos_experiencia(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/financiero")
async def api_obtener_financiero(licitacion_id: str):
    """Obtiene los requisitos financieros."""
    try:
        result_str = await obtener_requisitos_financieros(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/hv")
async def api_obtener_hv(licitacion_id: str):
    """Obtiene los requisitos de hojas de vida."""
    try:
        result_str = await obtener_requisitos_hv(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/resumen-ia")
async def api_obtener_resumen_ia(licitacion_id: str):
    """Obtiene el resumen generado por IA."""
    try:
        result_str = await obtener_resumen_ia(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/tecnicos")
async def api_obtener_tecnicos(licitacion_id: str):
    """Obtiene los requisitos técnicos."""
    try:
        result_str = await obtener_requisitos_tecnicos(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licitaciones/{licitacion_id}/puntaje")
async def api_obtener_puntaje(licitacion_id: str):
    """Obtiene los criterios de evaluación y puntaje."""
    try:
        result_str = await obtener_criterios_puntaje(licitacion_id)
        return {"success": True, "data": parse_mcp_result(result_str)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Leer el puerto de la variable de entorno PORT (Coolify lo configura automáticamente)
    port = int(os.getenv("PORT", 8004))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
