#!/bin/bash
# ============================================
# Script de inicio para CIPA en Railway
# ============================================

set -e

echo "================================================"
echo "🚀 Iniciando CIPA en Railway"
echo "================================================"
echo "Base Path: $BASE_PATH"
echo "Puerto: $PORT"
echo "================================================"

# Verificar base de datos
if [ ! -f "/app/backend/data/notas_credito.db" ]; then
    echo "⚠️  Base de datos no encontrada. Inicializando..."
    cd /app/backend
    python scripts/inicializar_auth.py || echo "⚠️  No se pudo inicializar la autenticación"
fi

# Verificar JWT Secret
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "⚠️  WARNING: JWT_SECRET_KEY no está configurado. Usando valor por defecto (NO SEGURO)"
fi

# Iniciar aplicación con Gunicorn
echo "🚀 Iniciando servidor con Gunicorn..."
cd /app/backend

exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "api.wsgi:create_app()"
