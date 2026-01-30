# Configuración para Coolify

## Valores Recomendados para Coolify

### Información Básica
- **Name**: `MCP Server Licitaciones`
- **Description**: `Servidor MCP para gestión de licitaciones - Conexión de Agentes conversacionales`
- **Build Pack**: `Dockerfile`

### Dominios
- **Domains**: `ws.dev.lumacloud.co` (o tu dominio preferido)
- **Direction**: `Allow www & non-www` (o según tu preferencia)

### Docker Configuration
- **Docker Registry**: (vacío - no se hará push a registry)
- **Docker Image**: (vacío)
- **Docker Image Tag**: (vacío)

### Build Configuration
- **Base Directory**: `.` (raíz del repositorio)
- **Dockerfile Location**: `Dockerfile`
- **Docker Build Stage Target**: (vacío)
- **Watch Paths**: (vacío - no necesario para este proyecto)
- **Custom Docker Options**: (vacío - NO usar los flags del otro proyecto)

### Network & Ports
- **Ports Exposes**: `8004`
- **Port Mappings**: (dejar que Coolify lo maneje automáticamente, o `8004:8004`)
- **Network Aliases**: (vacío)

## Variables de Entorno Necesarias

Asegúrate de configurar estas variables de entorno en Coolify:

```
PORT=8004
PYTHONUNBUFFERED=1
PYTHONIOENCODING=utf-8
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=tu_api_key_aqui
```

## Notas Importantes

1. El Dockerfile ya está configurado para usar la variable de entorno `PORT` que Coolify proporciona automáticamente.

2. El servidor tiene un endpoint de health check en `/health` que Coolify puede usar.

3. No necesitas los Custom Docker Options del otro proyecto (`--cap-add SYS_ADMIN`, etc.) ya que este proyecto no los requiere.

4. El Base Directory debe apuntar a la raíz donde está el Dockerfile (directorio "mcp server licitaciones").

5. El servidor escuchará en el puerto que Coolify le asigne a través de la variable `PORT`.

## Verificación Post-Deploy

Una vez desplegado, puedes verificar que funciona accediendo a:
- `https://ws.dev.lumacloud.co/health` - Debe retornar `{"status": "healthy", "service": "mcp-licitaciones"}`
- `https://ws.dev.lumacloud.co/` - Debe mostrar información del servidor
