# ============================================
# Multi-stage Dockerfile para CIPA
# Frontend (React + Vite) + Backend (Flask)
# Optimizado para Render.com deployment
# ============================================

FROM node:20-alpine AS frontend-builder

# Instalar dependencias de build
WORKDIR /app/frontend

# Copiar archivos de dependencias
COPY frontend/package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar código fuente del frontend
COPY frontend/ ./

# Build del frontend con base path configurado
ENV VITE_BASE_PATH=/intranet/cipa
RUN npm run build

# ============================================
# Stage 2: Python Backend + Servir Frontend
# ============================================

FROM python:3.11-slim

# Metadatos
LABEL maintainer="Correagro <info@correagro.com>"
LABEL description="CIPA - Sistema de Gestión de Notas de Crédito"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    BASE_PATH=/intranet/cipa

# Crear usuario no-root para seguridad
RUN groupadd -r cipa && useradd -r -g cipa cipa

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements del backend
COPY backend/requirements.txt ./backend/
COPY backend/api/requirements.txt ./backend/api/

# Instalar dependencias Python
RUN pip install --no-cache-dir -r backend/requirements.txt && \
    pip install --no-cache-dir -r backend/api/requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar código del backend
COPY backend/ ./backend/

# Copiar frontend compilado
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copiar script de inicio
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Crear directorios necesarios
RUN mkdir -p /app/backend/data && \
    mkdir -p /app/backend/logs && \
    chown -R cipa:cipa /app

# Cambiar a usuario no-root
USER cipa

# Exponer puerto
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/intranet/cipa/api/health')" || exit 1

# Comando de inicio
ENTRYPOINT ["./docker-entrypoint.sh"]
