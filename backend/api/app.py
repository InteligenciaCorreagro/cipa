"""
API REST para consulta de notas de crédito

Endpoints:
- POST /api/auth/login - Autenticación
- POST /api/auth/logout - Cerrar sesión
- POST /api/auth/refresh - Refresh token
- POST /api/auth/change-password - Cambiar contraseña

- GET /api/notas - Listar notas (con filtros)
- GET /api/notas/<id> - Obtener nota específica
- GET /api/notas/estadisticas - Estadísticas generales
- GET /api/notas/por-estado - Notas agrupadas por estado

- GET /api/aplicaciones/<numero_nota> - Aplicaciones de una nota
- GET /api/archivo/estadisticas - Estadísticas del archivo
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_cors import CORS
from dotenv import load_dotenv

# =============================================================================
# PYTHONPATH FIX: aseguramos que 'backend' (padre de 'core') esté en sys.path
# Estructura esperada:
# PROCESO ACTUAL/
#   backend/
#     api/app.py   <-- este archivo
#     api/auth.py
#     core/archivador_notas.py
# =============================================================================
CURRENT_FILE = Path(__file__).resolve()
API_DIR = CURRENT_FILE.parent                 # .../backend/api
BACKEND_DIR = API_DIR.parent                  # .../backend

# Insertamos 'backend' y 'backend/api' al inicio del sys.path
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(API_DIR))

# (Opcional de depuración)
# import pprint; print(">> sys.path head:"); pprint.pprint(sys.path[:5])

# Imports locales (ya con rutas correctas)
from auth import AuthManager
from core.archivador_notas import ArchivadorNotas

# =============================================================================
# Carga de variables de entorno y logging
# =============================================================================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# App Flask y configuración
# =============================================================================
app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# JWT Manager
jwt = JWTManager(app)

# CORS (ajusta origins según sea necesario)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# =============================================================================
# Rate Limiter (compatibilidad v2/v3 de Flask-Limiter)
# =============================================================================
try:
    # Flask-Limiter v3+
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
except Exception:
    # Fallback a v2 (firma antigua)
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

# =============================================================================
# Instancias de managers y DB
# =============================================================================
auth_manager = AuthManager()
archivador = ArchivadorNotas()

DB_PATH = BACKEND_DIR / 'data' / 'notas_credito.db'


def get_db_connection():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# ENDPOINTS DE AUTENTICACIÓN
# =============================================================================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Autenticación de usuario

    Request Body:
        {
            "username": "admin",
            "password": "password123"
        }

    Response:
        {
            "access_token": "...",
            "refresh_token": "...",
            "usuario": {...}
        }
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username y password requeridos"}), 400

    username = data['username']
    password = data['password']
    # IP del cliente (para auditoría)
    try:
        from flask_limiter.util import get_remote_address as _get_ip
        ip_address = _get_ip()
    except Exception:
        ip_address = request.remote_addr or '0.0.0.0'

    # Autenticar
    autenticado, usuario, mensaje = auth_manager.autenticar(username, password, ip_address)

    if not autenticado:
        return jsonify({"error": mensaje}), 401

    # Crear tokens JWT
    access_token = create_access_token(identity=usuario['id'], additional_claims={
        'username': usuario['username'],
        'rol': usuario['rol']
    })
    refresh_token = create_refresh_token(identity=usuario['id'])

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": {
            "id": usuario['id'],
            "username": usuario['username'],
            "email": usuario['email'],
            "rol": usuario['rol']
        }
    }), 200


@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Obtener nuevo access token usando refresh token"""
    identity = get_jwt_identity()
    claims = get_jwt()

    access_token = create_access_token(identity=identity, additional_claims=claims)
    return jsonify({"access_token": access_token}), 200


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión"""
    # Si manejas lista negra, aquí invalidas el jti
    # jti = get_jwt()['jti']
    # auth_manager.invalidar_sesion(jti)
    return jsonify({"mensaje": "Sesión cerrada exitosamente"}), 200


@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Cambiar contraseña del usuario actual"""
    data = request.get_json()

    if not data or 'nueva_contraseña' not in data:
        return jsonify({"error": "Nueva contraseña requerida"}), 400

    claims = get_jwt()
    username = claims.get('username')

    if auth_manager.cambiar_contraseña(username, data['nueva_contraseña']):
        return jsonify({"mensaje": "Contraseña cambiada exitosamente"}), 200
    else:
        return jsonify({"error": "Error al cambiar contraseña"}), 500


# =============================================================================
# ENDPOINTS DE NOTAS
# =============================================================================

@app.route('/api/notas', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def listar_notas():
    """
    Listar notas de crédito con filtros

    Query Parameters:
        - estado: PENDIENTE, PARCIAL, APLICADA
        - nit_cliente: Filtrar por NIT
        - fecha_desde: YYYY-MM-DD
        - fecha_hasta: YYYY-MM-DD
        - limite: Máximo de resultados (default: 100)
        - offset: Paginación (default: 0)
    """
    # Parámetros de filtro
    estado = request.args.get('estado')
    nit_cliente = request.args.get('nit_cliente')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    limite = int(request.args.get('limite', 100))
    offset = int(request.args.get('offset', 0))

    # Construir query
    query = "SELECT * FROM notas_credito WHERE 1=1"
    params = []

    if estado:
        query += " AND estado = ?"
        params.append(estado)

    if nit_cliente:
        query += " AND nit_cliente = ?"
        params.append(nit_cliente)

    if fecha_desde:
        query += " AND fecha_nota >= ?"
        params.append(fecha_desde)

    if fecha_hasta:
        query += " AND fecha_nota <= ?"
        params.append(fecha_hasta)

    query += " ORDER BY fecha_nota DESC LIMIT ? OFFSET ?"
    params.extend([limite, offset])

    # Ejecutar query
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(query, params)
    notas = [dict(row) for row in cursor.fetchall()]

    # Contar total (quitamos ORDER BY y LIMIT/OFFSET)
    query_count = query.split('ORDER BY')[0].replace('SELECT *', 'SELECT COUNT(*)')
    cursor.execute(query_count, params[:-2])
    total = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "notas": notas,
        "total": total,
        "limite": limite,
        "offset": offset,
        "total_paginas": (total + limite - 1) // limite
    }), 200


@app.route('/api/notas/<int:nota_id>', methods=['GET'])
@jwt_required()
def obtener_nota(nota_id):
    """Obtener detalles de una nota específica"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM notas_credito WHERE id = ?', (nota_id,))
    nota = cursor.fetchone()

    if not nota:
        conn.close()
        return jsonify({"error": "Nota no encontrada"}), 404

    # Obtener aplicaciones
    cursor.execute('''
        SELECT * FROM aplicaciones_notas
        WHERE id_nota = ?
        ORDER BY fecha_aplicacion DESC
    ''', (nota_id,))

    aplicaciones = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "nota": dict(nota),
        "aplicaciones": aplicaciones
    }), 200


@app.route('/api/notas/por-estado', methods=['GET'])
@jwt_required()
def notas_por_estado():
    """Obtener resumen de notas agrupadas por estado"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad, SUM(saldo_pendiente) as saldo_total
        FROM notas_credito
        GROUP BY estado
    ''')

    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({"estados": resultados}), 200


@app.route('/api/notas/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas():
    """Obtener estadísticas generales"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    # Total notas
    cursor.execute('SELECT COUNT(*) FROM notas_credito')
    stats['total_notas'] = cursor.fetchone()[0]

    # Por estado
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad, SUM(saldo_pendiente) as saldo
        FROM notas_credito
        GROUP BY estado
    ''')

    stats['por_estado'] = {row['estado']: {
        'cantidad': row['cantidad'],
        'saldo': row['saldo'] or 0
    } for row in cursor.fetchall()}

    # Total aplicaciones
    cursor.execute('SELECT COUNT(*) FROM aplicaciones_notas')
    stats['total_aplicaciones'] = cursor.fetchone()[0]

    # Valor total pendiente
    cursor.execute('SELECT SUM(saldo_pendiente) FROM notas_credito WHERE estado != "APLICADA"')
    stats['valor_total_pendiente'] = cursor.fetchone()[0] or 0

    conn.close()

    return jsonify(stats), 200


@app.route('/api/aplicaciones/<numero_nota>', methods=['GET'])
@jwt_required()
def obtener_aplicaciones(numero_nota):
    """Obtener aplicaciones de una nota específica"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM aplicaciones_notas
        WHERE numero_nota = ?
        ORDER BY fecha_aplicacion DESC
    ''', (numero_nota,))

    aplicaciones = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({"aplicaciones": aplicaciones}), 200


# =============================================================================
# ENDPOINTS DE ARCHIVO
# =============================================================================

@app.route('/api/archivo/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas_archivo():
    """Obtener estadísticas del archivo"""
    stats = archivador.obtener_estadisticas_archivo()
    return jsonify(stats), 200


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token expirado"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Token inválido"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "Token no proporcionado"}), 401


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Configurar puerto
    port = int(os.getenv('API_PORT', 5000))

    logger.info(f"Iniciando API en puerto {port}")
    logger.info(f"JWT Secret configurado: {'Sí' if app.config['JWT_SECRET_KEY'] != 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION' else 'NO - USAR .env!'}")

    # Ejecutar app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )
