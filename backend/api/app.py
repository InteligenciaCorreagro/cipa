"""
API REST para consulta de notas de crédito - VERSIÓN CON DEBUG JWT

CAMBIOS:
- Logging detallado de JWT
- Validación explícita de tokens
- Mensajes de error más descriptivos
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
    jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
)
from flask_cors import CORS
from dotenv import load_dotenv

# =============================================================================
# PYTHONPATH FIX
# =============================================================================
CURRENT_FILE = Path(__file__).resolve()
API_DIR = CURRENT_FILE.parent
BACKEND_DIR = API_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(API_DIR))

# Imports locales
try:
    from auth import AuthManager
    from core.archivador_notas import ArchivadorNotas
except ImportError as e:
    print(f"Error en imports: {e}")
    # Fallback
    try:
        from api.auth import AuthManager
        from core.archivador_notas import ArchivadorNotas
    except ImportError as e2:
        print(f"Error en imports (fallback): {e2}")
        sys.exit(1)

# =============================================================================
# Configuración
# =============================================================================
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG para ver todo
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# App Flask
# =============================================================================
app = Flask(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION')
app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

logger.info(f"="*60)
logger.info(f"JWT_SECRET_KEY configurado:")
logger.info(f"  Primeros 40 chars: {JWT_SECRET[:40]}...")
logger.info(f"  Longitud: {len(JWT_SECRET)} caracteres")
logger.info(f"="*60)

# JWT Manager
jwt = JWTManager(app)

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Rate Limiter (opcional)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
except Exception as e:
    logger.warning(f"Flask-Limiter no disponible: {e}")
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    limiter = DummyLimiter()

# =============================================================================
# Managers
# =============================================================================
auth_manager = AuthManager()
archivador = ArchivadorNotas()

# Usar la misma base de datos que main.py y GitHub Actions
# Apunta al directorio raíz del proyecto, no al subdirectorio backend
PROJECT_ROOT = BACKEND_DIR.parent
DB_PATH = Path(os.getenv('DB_PATH', str(PROJECT_ROOT / 'data' / 'notas_credito.db')))


def get_db_connection():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# MIDDLEWARE DE DEBUG
# =============================================================================

@app.before_request
def log_request():
    """Log detallado de cada request"""
    logger.debug(f"=" * 60)
    logger.debug(f"REQUEST: {request.method} {request.path}")
    
    # Log headers (sin datos sensibles completos)
    auth_header = request.headers.get('Authorization', '')
    if auth_header:
        if auth_header.startswith('Bearer '):
            token_preview = auth_header[7:27] + '...'
            logger.debug(f"Authorization header presente: Bearer {token_preview}")
        else:
            logger.warning(f"Authorization header malformado: {auth_header[:50]}")
    else:
        logger.debug("No Authorization header")
    
    logger.debug(f"=" * 60)


# =============================================================================
# JWT ERROR HANDLERS
# =============================================================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.warning(f"Token expirado - Usuario ID: {jwt_payload.get('sub')}")
    return jsonify({
        "error": "Token expirado",
        "message": "Tu sesión ha expirado. Por favor, inicia sesión nuevamente."
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.error(f"Token inválido: {error}")
    return jsonify({
        "error": "Token inválido",
        "message": "El token proporcionado no es válido.",
        "detail": str(error)
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    logger.warning(f"Token faltante: {error}")
    return jsonify({
        "error": "Token no proporcionado",
        "message": "Se requiere autenticación para acceder a este recurso."
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    logger.warning(f"Token revocado - Usuario ID: {jwt_payload.get('sub')}")
    return jsonify({
        "error": "Token revocado",
        "message": "Tu sesión ha sido cerrada."
    }), 401


# =============================================================================
# ENDPOINTS DE AUTENTICACIÓN
# =============================================================================


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Autenticación de usuario"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username y password requeridos"}), 400

    username = data['username']
    password = data['password']
    
    try:
        ip_address = request.remote_addr or '0.0.0.0'
    except:
        ip_address = '0.0.0.0'

    logger.info(f"Intento de login: {username} desde {ip_address}")

    # Autenticar
    autenticado, usuario, mensaje = auth_manager.autenticar(username, password, ip_address)

    if not autenticado:
        logger.warning(f"Login fallido para {username}: {mensaje}")
        return jsonify({"error": mensaje}), 401

    # ✅ CRÍTICO: Convertir ID a string
    user_id_str = str(usuario['id'])

    # Crear tokens JWT con identity como string
    access_token = create_access_token(
        identity=user_id_str,
        additional_claims={
            'username': usuario['username'],
            'rol': usuario['rol'],
            'user_id': usuario['id']  # Opcional: mantener el int en claims
        }
    )
    
    refresh_token = create_refresh_token(
        identity=user_id_str,
        additional_claims={
            'username': usuario['username']
        }
    )

    logger.info(f"✅ Login exitoso: {username} (ID: {user_id_str})")
    logger.debug(f"Access token: {access_token[:50]}...")
    logger.debug(f"Refresh token: {refresh_token[:50]}...")

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
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
    # ✅ get_jwt_identity() puede retornar string o int dependiendo del token
    identity = get_jwt_identity()
    
    # ✅ CRÍTICO: Asegurar que sea string
    identity_str = str(identity)
    
    logger.info(f"Refresh token para usuario ID: {identity_str}")

    # Obtener datos del usuario (SQLite acepta string o int)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, rol
        FROM usuarios
        WHERE id = ? AND activo = 1
    ''', (identity_str,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        logger.warning(f"Usuario no encontrado o inactivo: {identity_str}")
        return jsonify({"error": "Usuario no encontrado o inactivo"}), 401

    # ✅ Generar nuevo access token con identity como string
    access_token = create_access_token(
        identity=identity_str,  # String obligatorio
        additional_claims={
            'username': row['username'],
            'rol': row['rol'],
            'user_id': row['id']
        }
    )
    
    logger.info(f"✅ Nuevo access token generado para: {row['username']}")
    logger.debug(f"Nuevo token: {access_token[:50]}...")
    
    return jsonify({"access_token": access_token}), 200


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión"""
    identity = get_jwt_identity()
    logger.info(f"Logout: Usuario ID {identity}")
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
        logger.info(f"Contraseña cambiada para: {username}")
        return jsonify({"mensaje": "Contraseña cambiada exitosamente"}), 200
    else:
        return jsonify({"error": "Error al cambiar contraseña"}), 500


@app.route('/api/auth/register', methods=['POST'])
@jwt_required()
def register_user():
    """
    Crear nuevo usuario - Solo para administradores
    Este es el 'backdoor' para creación de usuarios con autenticación
    """
    # Verificar que el usuario actual sea admin
    claims = get_jwt()
    rol_actual = claims.get('rol')

    if rol_actual != 'admin':
        logger.warning(f"Intento de crear usuario sin permisos de admin: {claims.get('username')}")
        return jsonify({"error": "No tiene permisos para crear usuarios"}), 403

    data = request.get_json()

    # Validar datos requeridos
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username y password son requeridos"}), 400

    username = data['username']
    password = data['password']
    email = data.get('email')
    rol = data.get('rol', 'viewer')

    # Validar rol
    if rol not in ['admin', 'editor', 'viewer']:
        return jsonify({"error": "Rol inválido. Debe ser: admin, editor o viewer"}), 400

    # Validar longitud de contraseña
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    # Crear usuario
    if auth_manager.crear_usuario(username, password, email, rol):
        logger.info(f"Usuario creado por admin {claims.get('username')}: {username} ({rol})")
        return jsonify({
            "mensaje": "Usuario creado exitosamente",
            "usuario": {
                "username": username,
                "email": email,
                "rol": rol
            }
        }), 201
    else:
        return jsonify({"error": "Error al crear usuario. Puede que ya exista."}), 400


@app.route('/api/auth/users', methods=['GET'])
@jwt_required()
def list_users():
    """Listar usuarios - Solo para administradores"""
    # Verificar que el usuario actual sea admin
    claims = get_jwt()
    rol_actual = claims.get('rol')

    if rol_actual != 'admin':
        return jsonify({"error": "No tiene permisos para ver usuarios"}), 403

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, username, email, rol, activo, ultimo_acceso, fecha_creacion
            FROM usuarios
            ORDER BY fecha_creacion DESC
        ''')

        usuarios = []
        for row in cursor.fetchall():
            usuarios.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'rol': row[3],
                'activo': bool(row[4]),
                'ultimo_acceso': row[5],
                'fecha_creacion': row[6]
            })

        conn.close()

        return jsonify({
            "total": len(usuarios),
            "usuarios": usuarios
        }), 200

    except Exception as e:
        logger.error(f"Error al listar usuarios: {e}")
        return jsonify({"error": "Error al obtener usuarios"}), 500


@app.route('/api/reporte/operativo', methods=['GET'])
@jwt_required()
def reporte_operativo():
    """
    Obtener datos del reporte operativo diario
    Equivalente a lo que se envía por correo a operativa
    """
    try:
        fecha = request.args.get('fecha')

        # Si no se especifica fecha, usar ayer
        if not fecha:
            fecha_obj = datetime.now() - timedelta(days=1)
            fecha = fecha_obj.strftime('%Y-%m-%d')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Obtener notas de la fecha
        cursor.execute('''
            SELECT numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                   codigo_producto, nombre_producto, valor_total, cantidad,
                   saldo_pendiente, cantidad_pendiente, estado
            FROM notas_credito
            WHERE DATE(fecha_nota) = ? OR DATE(fecha_registro) = ?
            ORDER BY fecha_nota DESC
        ''', (fecha, fecha))

        notas = []
        for row in cursor.fetchall():
            notas.append({
                'numero_nota': row[0],
                'fecha_nota': row[1],
                'nit_cliente': row[2],
                'nombre_cliente': row[3],
                'codigo_producto': row[4],
                'nombre_producto': row[5],
                'valor_total': row[6],
                'cantidad': row[7],
                'saldo_pendiente': row[8],
                'cantidad_pendiente': row[9],
                'estado': row[10]
            })

        # Obtener aplicaciones de la fecha
        cursor.execute('''
            SELECT numero_nota, numero_factura, fecha_factura, nit_cliente,
                   codigo_producto, valor_aplicado, cantidad_aplicada, fecha_aplicacion
            FROM aplicaciones_notas
            WHERE DATE(fecha_aplicacion) = ?
            ORDER BY fecha_aplicacion DESC
        ''', (fecha,))

        aplicaciones = []
        for row in cursor.fetchall():
            aplicaciones.append({
                'numero_nota': row[0],
                'numero_factura': row[1],
                'fecha_factura': row[2],
                'nit_cliente': row[3],
                'codigo_producto': row[4],
                'valor_aplicado': row[5],
                'cantidad_aplicada': row[6],
                'fecha_aplicacion': row[7]
            })

        # Obtener facturas rechazadas de la fecha
        cursor.execute('''
            SELECT numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                   codigo_producto, nombre_producto, tipo_inventario,
                   valor_total, razon_rechazo
            FROM facturas_rechazadas
            WHERE DATE(fecha_factura) = ?
            ORDER BY fecha_factura DESC
        ''', (fecha,))

        facturas_rechazadas = []
        for row in cursor.fetchall():
            facturas_rechazadas.append({
                'numero_factura': row[0],
                'fecha_factura': row[1],
                'nit_cliente': row[2],
                'nombre_cliente': row[3],
                'codigo_producto': row[4],
                'nombre_producto': row[5],
                'tipo_inventario': row[6],
                'valor_total': row[7],
                'razon_rechazo': row[8]
            })

        # Resumen de notas
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'APLICADA' THEN 1 ELSE 0 END) as aplicadas,
                SUM(CASE WHEN estado = 'PENDIENTE' THEN saldo_pendiente ELSE 0 END) as saldo_pendiente
            FROM notas_credito
        ''')

        resumen_row = cursor.fetchone()
        resumen_notas = {
            'total': resumen_row[0] or 0,
            'pendientes': resumen_row[1] or 0,
            'aplicadas': resumen_row[2] or 0,
            'saldo_pendiente': resumen_row[3] or 0
        }

        conn.close()

        return jsonify({
            "fecha": fecha,
            "notas_credito": notas,
            "aplicaciones": aplicaciones,
            "facturas_rechazadas": facturas_rechazadas,
            "resumen": {
                "total_notas": len(notas),
                "total_aplicaciones": len(aplicaciones),
                "total_rechazadas": len(facturas_rechazadas),
                "resumen_notas": resumen_notas
            }
        }), 200

    except Exception as e:
        logger.error(f"Error en reporte operativo: {e}", exc_info=True)
        return jsonify({"error": "Error al generar reporte"}), 500


# =============================================================================
# ENDPOINTS DE NOTAS
# =============================================================================

@app.route('/api/notas', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def listar_notas():
    """Listar notas de crédito con filtros"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando listado de notas")
        
        estado = request.args.get('estado')
        nit_cliente = request.args.get('nit_cliente')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        limite = int(request.args.get('limite', 100))
        offset = int(request.args.get('offset', 0))

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

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query, params)
        notas = [dict(row) for row in cursor.fetchall()]

        query_count = query.split('ORDER BY')[0].replace('SELECT *', 'SELECT COUNT(*)')
        cursor.execute(query_count, params[:-2])
        total = cursor.fetchone()[0]

        conn.close()

        logger.debug(f"Retornando {len(notas)} notas de {total} totales")

        return jsonify({
            "items": notas,
            "total": total,
            "limite": limite,
            "offset": offset,
            "total_paginas": (total + limite - 1) // limite
        }), 200

    except Exception as e:
        logger.error(f"Error en listar_notas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener notas"}), 500


@app.route('/api/notas/<int:nota_id>', methods=['GET'])
@jwt_required()
def obtener_nota(nota_id):
    """Obtener detalles de una nota específica"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando nota {nota_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM notas_credito WHERE id = ?', (nota_id,))
        nota = cursor.fetchone()

        if not nota:
            conn.close()
            return jsonify({"error": "Nota no encontrada"}), 404

        cursor.execute('''
            SELECT * FROM aplicaciones_notas
            WHERE id_nota = ?
            ORDER BY fecha_aplicacion DESC
        ''', (nota_id,))

        aplicaciones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(dict(nota)), 200

    except Exception as e:
        logger.error(f"Error en obtener_nota: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener nota"}), 500


@app.route('/api/notas/por-estado', methods=['GET'])
@jwt_required()
def notas_por_estado():
    """Obtener resumen de notas agrupadas por estado"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                estado, 
                COUNT(*) as cantidad, 
                SUM(valor_total) as valor_total,
                SUM(saldo_pendiente) as saldo_pendiente
            FROM notas_credito
            GROUP BY estado
        ''')

        resultados = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(resultados), 200

    except Exception as e:
        logger.error(f"Error en notas_por_estado: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener datos"}), 500


@app.route('/api/notas/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas():
    """Obtener estadísticas generales"""
    try:
        identity = get_jwt_identity()
        logger.info(f"Usuario ID {identity} solicitando estadísticas")
        
        conn = get_db_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*) FROM notas_credito')
        stats['total_notas'] = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(valor_total) FROM notas_credito')
        stats['total_valor'] = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT estado, COUNT(*) as cantidad, SUM(saldo_pendiente) as saldo
            FROM notas_credito
            GROUP BY estado
        ''')

        for row in cursor.fetchall():
            estado_lower = row['estado'].lower().replace(' ', '_')
            stats[f'notas_{estado_lower}'] = row['cantidad']

        cursor.execute('SELECT SUM(saldo_pendiente) FROM notas_credito WHERE estado != "APLICADA"')
        stats['saldo_pendiente_total'] = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM aplicaciones_notas')
        stats['total_aplicaciones'] = cursor.fetchone()[0]

        conn.close()

        logger.info(f"✅ Estadísticas retornadas exitosamente")
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error en estadisticas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener estadísticas"}), 500


@app.route('/api/aplicaciones/<numero_nota>', methods=['GET'])
@jwt_required()
def obtener_aplicaciones(numero_nota):
    """Obtener aplicaciones de una nota específica"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM aplicaciones_notas
            WHERE numero_nota = ?
            ORDER BY fecha_aplicacion DESC
        ''', (numero_nota,))

        aplicaciones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(aplicaciones), 200

    except Exception as e:
        logger.error(f"Error en obtener_aplicaciones: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener aplicaciones"}), 500


# =============================================================================
# ENDPOINTS DE FACTURAS
# =============================================================================

@app.route('/api/facturas', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def listar_facturas():
    """Listar facturas con filtros"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando listado de facturas")

        estado = request.args.get('estado')
        nit_cliente = request.args.get('nit_cliente')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        es_valida = request.args.get('es_valida')
        limite = int(request.args.get('limite', 100))
        offset = int(request.args.get('offset', 0))

        # Usar tabla facturas para facturas válidas
        query = "SELECT * FROM facturas WHERE 1=1"
        params = []

        if estado:
            query += " AND estado = ?"
            params.append(estado)

        if nit_cliente:
            query += " AND nit_cliente = ?"
            params.append(nit_cliente)

        if fecha_desde:
            query += " AND fecha_factura >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha_factura <= ?"
            params.append(fecha_hasta)

        # Filtrar por tiene_nota_credito si es_valida viene como parámetro
        # (reutilizamos este parámetro para filtrar facturas con/sin notas)
        if es_valida is not None:
            if es_valida.lower() == 'con_nota':
                query += " AND tiene_nota_credito = 1"
            elif es_valida.lower() == 'sin_nota':
                query += " AND tiene_nota_credito = 0"

        query += " ORDER BY fecha_factura DESC LIMIT ? OFFSET ?"
        params.extend([limite, offset])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query, params)
        facturas = [dict(row) for row in cursor.fetchall()]

        query_count = query.split('ORDER BY')[0].replace('SELECT *', 'SELECT COUNT(*)')
        cursor.execute(query_count, params[:-2])
        total = cursor.fetchone()[0]

        conn.close()

        logger.debug(f"Retornando {len(facturas)} facturas de {total} totales")

        return jsonify({
            "items": facturas,
            "total": total,
            "limite": limite,
            "offset": offset,
            "total_paginas": (total + limite - 1) // limite
        }), 200

    except Exception as e:
        logger.error(f"Error en listar_facturas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener facturas"}), 500


@app.route('/api/facturas/<int:factura_id>', methods=['GET'])
@jwt_required()
def obtener_factura(factura_id):
    """Obtener detalles de una factura específica"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando factura {factura_id}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Usar tabla facturas
        cursor.execute('SELECT * FROM facturas WHERE id = ?', (factura_id,))
        factura = cursor.fetchone()

        if not factura:
            conn.close()
            return jsonify({"error": "Factura no encontrada"}), 404

        # Obtener notas de crédito asociadas si las hay
        numero_factura = factura['numero_factura']
        codigo_producto = factura['codigo_producto']
        cursor.execute('''
            SELECT * FROM aplicaciones_notas
            WHERE numero_factura = ?
            ORDER BY fecha_aplicacion DESC
        ''', (numero_factura,))

        aplicaciones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        factura_dict = dict(factura)
        factura_dict['aplicaciones'] = aplicaciones

        return jsonify(factura_dict), 200

    except Exception as e:
        logger.error(f"Error en obtener_factura: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener factura"}), 500


@app.route('/api/facturas/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas_facturas():
    """Obtener estadísticas generales de facturas válidas y rechazadas"""
    try:
        identity = get_jwt_identity()
        logger.info(f"Usuario ID {identity} solicitando estadísticas de facturas")

        conn = get_db_connection()
        cursor = conn.cursor()

        stats = {}

        # Total de facturas válidas
        cursor.execute('SELECT COUNT(*) FROM facturas')
        stats['facturas_validas'] = cursor.fetchone()[0]

        # Total de facturas rechazadas
        cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas')
        stats['facturas_invalidas'] = cursor.fetchone()[0]

        # Total general
        stats['total_facturas'] = stats['facturas_validas'] + stats['facturas_invalidas']

        # Valor total facturado (solo válidas)
        cursor.execute('SELECT SUM(valor_total) FROM facturas')
        stats['valor_total_facturado'] = cursor.fetchone()[0] or 0

        # Facturas con notas de crédito aplicadas
        cursor.execute('SELECT COUNT(*) FROM facturas WHERE tiene_nota_credito = 1')
        stats['facturas_con_notas'] = cursor.fetchone()[0]

        # Valor total de notas aplicadas
        cursor.execute('SELECT SUM(valor_nota_aplicada) FROM facturas')
        stats['valor_total_transado'] = cursor.fetchone()[0] or 0

        # Facturas últimos 30 días
        cursor.execute('''
            SELECT COUNT(*) FROM facturas
            WHERE fecha_factura >= date('now', '-30 days')
        ''')
        stats['facturas_ultimos_30_dias'] = cursor.fetchone()[0]

        # Estadísticas por estado de facturas válidas
        cursor.execute('''
            SELECT estado, COUNT(*) as cantidad, SUM(valor_total) as valor_total
            FROM facturas
            GROUP BY estado
        ''')

        stats['por_estado'] = []
        for row in cursor.fetchall():
            stats['por_estado'].append({
                'estado': row[0],
                'cantidad': row[1],
                'valor_total': row[2] or 0
            })

        conn.close()

        logger.info(f"✅ Estadísticas de facturas retornadas exitosamente")
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error en estadisticas_facturas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener estadísticas"}), 500


@app.route('/api/facturas/transacciones', methods=['GET'])
@jwt_required()
def obtener_transacciones():
    """Obtener grilla de transacciones (facturas con valores transados)"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando transacciones")

        limite = int(request.args.get('limite', 50))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener aplicaciones de notas (transacciones reales)
        cursor.execute('''
            SELECT
                id,
                numero_nota,
                numero_factura,
                fecha_factura,
                nit_cliente,
                codigo_producto,
                valor_aplicado,
                cantidad_aplicada,
                fecha_aplicacion
            FROM aplicaciones_notas
            ORDER BY fecha_aplicacion DESC
            LIMIT ? OFFSET ?
        ''', (limite, offset))

        transacciones = [dict(row) for row in cursor.fetchall()]

        # Contar total
        cursor.execute('SELECT COUNT(*) FROM aplicaciones_notas')
        total = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            "items": transacciones,
            "total": total,
            "limite": limite,
            "offset": offset
        }), 200

    except Exception as e:
        logger.error(f"Error en obtener_transacciones: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener transacciones"}), 500


@app.route('/api/facturas/rechazadas', methods=['GET'])
@jwt_required()
def obtener_facturas_rechazadas():
    """Obtener grilla de facturas rechazadas"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando facturas rechazadas")

        limite = int(request.args.get('limite', 50))
        offset = int(request.args.get('offset', 0))
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query base
        query = '''
            SELECT
                id,
                numero_factura,
                fecha_factura,
                nit_cliente,
                nombre_cliente,
                codigo_producto,
                nombre_producto,
                tipo_inventario,
                valor_total,
                razon_rechazo,
                fecha_registro
            FROM facturas_rechazadas
            WHERE 1=1
        '''
        params = []

        if fecha_desde:
            query += " AND fecha_factura >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha_factura <= ?"
            params.append(fecha_hasta)

        query += " ORDER BY fecha_factura DESC LIMIT ? OFFSET ?"
        params.extend([limite, offset])

        cursor.execute(query, params)
        rechazadas = [dict(row) for row in cursor.fetchall()]

        # Contar total
        query_count = query.split('ORDER BY')[0].replace('SELECT\n                id,\n                numero_factura,\n                fecha_factura,\n                nit_cliente,\n                nombre_cliente,\n                codigo_producto,\n                nombre_producto,\n                tipo_inventario,\n                valor_total,\n                razon_rechazo,\n                fecha_registro', 'SELECT COUNT(*)')
        cursor.execute(query_count, params[:-2])
        total = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            "items": rechazadas,
            "total": total,
            "limite": limite,
            "offset": offset
        }), 200

    except Exception as e:
        logger.error(f"Error en obtener_facturas_rechazadas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener facturas rechazadas"}), 500


@app.route('/api/facturas/con-notas', methods=['GET'])
@jwt_required()
def obtener_facturas_con_notas():
    """Obtener grilla de facturas que tienen notas de crédito aplicadas"""
    try:
        identity = get_jwt_identity()
        logger.debug(f"Usuario ID {identity} solicitando facturas con notas")

        limite = int(request.args.get('limite', 50))
        offset = int(request.args.get('offset', 0))
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Usar aplicaciones_notas para obtener facturas con notas aplicadas
        query = '''
            SELECT
                id,
                numero_nota,
                numero_factura,
                fecha_factura,
                nit_cliente,
                codigo_producto,
                valor_aplicado,
                cantidad_aplicada,
                fecha_aplicacion
            FROM aplicaciones_notas
            WHERE 1=1
        '''
        params = []

        if fecha_desde:
            query += " AND fecha_factura >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha_factura <= ?"
            params.append(fecha_hasta)

        query += " ORDER BY fecha_factura DESC LIMIT ? OFFSET ?"
        params.extend([limite, offset])

        cursor.execute(query, params)
        facturas = [dict(row) for row in cursor.fetchall()]

        # Contar total
        query_count = query.split('ORDER BY')[0].replace('SELECT\n                id,\n                numero_nota,\n                numero_factura,\n                fecha_factura,\n                nit_cliente,\n                codigo_producto,\n                valor_aplicado,\n                cantidad_aplicada,\n                fecha_aplicacion', 'SELECT COUNT(*)')
        cursor.execute(query_count, params[:-2])
        total = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            "items": facturas,
            "total": total,
            "limite": limite,
            "offset": offset
        }), 200

    except Exception as e:
        logger.error(f"Error en obtener_facturas_con_notas: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener facturas con notas"}), 500


# =============================================================================
# ENDPOINTS DE ARCHIVO
# =============================================================================

@app.route('/api/archivo/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas_archivo():
    """Obtener estadísticas del archivo"""
    try:
        stats = archivador.obtener_estadisticas_archivo()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error en estadisticas_archivo: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener estadísticas"}), 500


# =============================================================================
# ENDPOINTS DE ADMIN - PROCESAMIENTO DE RANGO DE FECHAS
# =============================================================================

@app.route('/api/admin/procesar-rango', methods=['POST'])
@jwt_required()
def procesar_rango():
    """
    Procesar un rango de fechas y generar Excel consolidado
    Requiere rol de admin

    Body:
    {
        "fecha_desde": "2025-01-01",
        "fecha_hasta": "2025-01-31"
    }
    """
    try:
        # Obtener usuario actual y verificar que sea admin
        current_user = get_jwt_identity()
        user_data = auth_manager.get_user(current_user)

        if not user_data or user_data.get('role') != 'admin':
            return jsonify({"error": "No autorizado. Se requiere rol de administrador"}), 403

        # Obtener datos del request
        data = request.get_json()
        fecha_desde_str = data.get('fecha_desde')
        fecha_hasta_str = data.get('fecha_hasta')

        if not fecha_desde_str or not fecha_hasta_str:
            return jsonify({"error": "Se requieren fecha_desde y fecha_hasta"}), 400

        # Parsear fechas
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400

        # Validar rango
        if fecha_desde > fecha_hasta:
            return jsonify({"error": "fecha_desde debe ser anterior a fecha_hasta"}), 400

        # Validar que el rango no sea muy grande (máximo 90 días)
        dias_diff = (fecha_hasta - fecha_desde).days
        if dias_diff > 90:
            return jsonify({"error": "El rango máximo permitido es de 90 días"}), 400

        # Importar funciones de procesamiento
        try:
            import sys
            sys.path.insert(0, str(BACKEND_DIR))
            from main import procesar_rango_fechas
        except ImportError as e:
            logger.error(f"Error importando funciones de procesamiento: {e}")
            return jsonify({"error": "Error en configuración del servidor"}), 500

        # Preparar configuración
        config = {
            'CONNI_KEY': os.getenv('CONNI_KEY'),
            'CONNI_TOKEN': os.getenv('CONNI_TOKEN'),
            'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
            'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
            'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
            'DESTINATARIOS': os.getenv('DESTINATARIOS', '').split(',') if os.getenv('DESTINATARIOS') else [],
            'TEMPLATE_PATH': os.getenv('TEMPLATE_PATH', str(BACKEND_DIR / 'templates' / 'plantilla.xlsx')),
            'DB_PATH': str(DB_PATH)
        }

        # Validar configuración
        if not config['CONNI_KEY'] or not config['CONNI_TOKEN']:
            return jsonify({"error": "Configuración del servidor incompleta"}), 500

        # Procesar rango de fechas
        logger.info(f"Iniciando procesamiento de rango: {fecha_desde_str} a {fecha_hasta_str} por usuario {current_user}")
        resultado = procesar_rango_fechas(fecha_desde, fecha_hasta, config)

        return jsonify(resultado), 200

    except Exception as e:
        logger.error(f"Error en procesar_rango: {e}", exc_info=True)
        return jsonify({"error": "Error al procesar rango de fechas"}), 500


@app.route('/api/admin/descargar-archivo/<filename>', methods=['GET'])
@jwt_required()
def descargar_archivo(filename):
    """
    Descargar archivo generado por el procesamiento
    Requiere rol de admin
    """
    try:
        # Obtener usuario actual y verificar que sea admin
        current_user = get_jwt_identity()
        user_data = auth_manager.get_user(current_user)

        if not user_data or user_data.get('role') != 'admin':
            return jsonify({"error": "No autorizado"}), 403

        # Validar filename para evitar path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Nombre de archivo inválido"}), 400

        # Buscar archivo en directorio output
        output_dir = BACKEND_DIR / 'output'
        file_path = output_dir / filename

        if not file_path.exists():
            return jsonify({"error": "Archivo no encontrado"}), 404

        # Enviar archivo
        from flask import send_file
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"Error en descargar_archivo: {e}", exc_info=True)
        return jsonify({"error": "Error al descargar archivo"}), 500


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint - NO requiere autenticación"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.1",
        "jwt_configured": bool(app.config.get('JWT_SECRET_KEY'))
    }), 200


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno: {error}", exc_info=True)
    return jsonify({"error": "Error interno del servidor"}), 500


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 2500))

    logger.info(f"=" * 60)
    logger.info(f"🚀 INICIANDO API REST - CIPA")
    logger.info(f"=" * 60)
    logger.info(f"Puerto: {port}")
    logger.info(f"JWT Secret configurado: {'Sí' if JWT_SECRET != 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION' else 'NO - CAMBIAR!'}")
    logger.info(f"Base de datos: {DB_PATH}")
    logger.info(f"=" * 60)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True  # DEBUG activado para ver logs
    )