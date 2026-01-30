# MCP Server - Gestión de Licitaciones

Servidor MCP (Model Context Protocol) para la gestión del estado comercial de licitaciones.

## 🚀 Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Agregar la siguiente configuración:

```en google adk
 tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="python",
                args=[str(MCP_SERVER_PATH)],
                env={
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONIOENCODING": "utf-8",
                },
            )
        )
    ],
```

El servidor implementa los siguientes tools basados en la API de licitaciones:

### Consulta de Información

1. **listar_licitaciones()**
   - Lista todas las licitaciones disponibles
   - Endpoint: `GET /api/licitaciones`

2. **obtener_licitacion_completa(licitacion_id)**
   - Obtiene información completa de una licitación
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/completo`

3. **ver_correo_licitacion(licitacion_id)**
   - Ver el correo original de la licitación
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/correo`

4. **obtener_detalles_licitacion(licitacion_id)**
   - Obtiene detalles específicos de una licitación
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/detalles`

5. **obtener_documentos_requeridos(licitacion_id)**
   - Lista los documentos requeridos
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/documentos_requeridos`

### Requisitos Específicos

6. **obtener_requisitos_experiencia(licitacion_id)**
   - Requisitos de experiencia
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/experiencia`

7. **obtener_requisitos_financieros(licitacion_id)**
   - Requisitos financieros
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/financiero`

8. **obtener_requisitos_hv(licitacion_id)**
   - Requisitos de hojas de vida
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/hv`

9. **obtener_requisitos_tecnicos(licitacion_id)**
   - Requisitos técnicos
   - Endpoint: `GET /api/licitaciones/{licitacion_id}/tecnicos`

### Análisis y Gestión

10. **obtener_resumen_ia(licitacion_id)**
    - Resumen generado por IA
    - Endpoint: `GET /api/licitaciones/{licitacion_id}/resumen_ia`

11. **cambiar_estado_licitacion(licitacion_id, nuevo_estado)**
    - Cambia el estado de una licitación
    - Endpoint: `POST /api/licitaciones/{licitacion_id}/estado`
    - Estados posibles: "abierta", "cerrada", "en_evaluacion", "adjudicada"

## 💡 Ejemplos de Uso

Una vez configurado en Claude Desktop, puedes usar los tools así:

```
Usuario: "Muéstrame todas las licitaciones disponibles"
IA: [Usa listar_licitaciones()]

Usuario: "Dame los detalles completos de la licitación 12345"
IA: [Usa obtener_licitacion_completa("12345")]

Usuario: "¿Qué documentos necesito para la licitación 12345?"
IA: [Usa obtener_documentos_requeridos("12345")]

Usuario: "Cambia el estado de la licitación 12345 a cerrada"
IA: [Usa cambiar_estado_licitacion("12345", "cerrada")]
```

## 🔧 Configuración de la API

El servidor está configurado para conectarse a:
- **Base URL**: `https://dev.lumacloud.co/apilic`
- **User Agent**: `licitaciones-app/1.0`

Para cambiar la URL base, edita la constante `LICITACIONES_API_BASE` en el archivo `licitaciones_mcp_server.py`.

## 📝 Notas

- Todos los endpoints incluyen manejo de errores robusto
- Las respuestas están formateadas de manera legible
- El servidor usa transporte STDIO para comunicación con GOOGLE ADK
- Requiere autenticación adecuada según la configuración de tu API

## 🐛 Solución de Problemas

Si el servidor no funciona:

1. Verifica que la ruta en el archivo de configuración sea absoluta y correcta
2. Asegúrate de tener Python 3.12
3. Confirma que las dependencias estén instaladas
4. Revisa los logs para errores específicos
5. Verifica que la URL base de la API sea accesible

## 📄 Licencia

Este servidor MCP es de uso interno para gestión de licitaciones.