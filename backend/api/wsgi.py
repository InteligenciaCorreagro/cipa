"""
WSGI Application Factory para CIPA
Configurado para funcionar con subpath en Railway
"""

import os
import sys
from pathlib import Path
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

# Fix PYTHONPATH
CURRENT_FILE = Path(__file__).resolve()
API_DIR = CURRENT_FILE.parent
BACKEND_DIR = API_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(API_DIR))


def create_app():
    """Crear y configurar la aplicación Flask con soporte para subpath"""

    # Importar la app del módulo principal
    from app import app

    # Configurar para trabajar detrás de proxy (Railway)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Obtener base path de variable de entorno
    BASE_PATH = os.getenv('BASE_PATH', '/intranet/cipa').rstrip('/')
    FRONTEND_DIR = BACKEND_DIR.parent / 'frontend' / 'dist'

    print(f"=" * 60)
    print(f"🚀 CIPA WSGI Application")
    print(f"=" * 60)
    print(f"Base Path: {BASE_PATH}")
    print(f"Frontend Dir: {FRONTEND_DIR}")
    print(f"Serving: {BASE_PATH}/api/* -> Flask API")
    print(f"Serving: {BASE_PATH}/* -> React SPA")
    print(f"=" * 60)

    # Servir archivos estáticos del frontend
    @app.route(f'{BASE_PATH}/')
    @app.route(f'{BASE_PATH}/<path:path>')
    def serve_frontend(path=''):
        """Servir el frontend de React"""
        if path and (FRONTEND_DIR / path).exists():
            return send_from_directory(FRONTEND_DIR, path)
        # Para React Router, siempre servir index.html
        return send_from_directory(FRONTEND_DIR, 'index.html')

    # Ruta raíz - redirigir al subpath
    @app.route('/')
    def root():
        """Redirigir a la ruta del subpath"""
        from flask import redirect
        return redirect(BASE_PATH + '/')

    # Health check público
    @app.route(f'{BASE_PATH}/api/health')
    def health_subpath():
        """Health check en el subpath"""
        from datetime import datetime
        from flask import jsonify
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.1",
            "base_path": BASE_PATH
        }), 200

    return app


# Para uso con Gunicorn
application = create_app()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
