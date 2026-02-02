# Dockerfile para MCP Server - Licitaciones
# El puerto se configura mediante la variable de entorno PORT (Coolify lo maneja automáticamente)

FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8004

# Instalar dependencias del sistema si son necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias adicionales necesarias para el servidor HTTP
RUN pip install --no-cache-dir fastapi uvicorn

# Copiar el código de la aplicación
COPY mcp_server_licitaciones/ ./mcp_server_licitaciones/

# Establecer el directorio de trabajo dentro del módulo
WORKDIR /app/mcp_server_licitaciones

# Exponer el puerto (Coolify lo manejará automáticamente)
# El puerto se lee de la variable de entorno PORT en runtime
# Nota: EXPOSE solo es informativo, Coolify manejará el puerto real
EXPOSE 8004

# Healthcheck para Coolify
# Coolify puede configurar su propio healthcheck, pero este es un fallback
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8004}/health || exit 1

# Comando para ejecutar el servidor
CMD ["python", "server.py"]
