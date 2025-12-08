"""
API REST para consulta de notas de crédito - VERSIÓN REESTRUCTURADA

Endpoints para:
- Autenticación de usuarios
- Consulta de facturas, notas crédito y facturas rechazadas
- Dashboard y reportes
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

# PYTHONPATH FIX
CURRENT_FILE = Path(__file__).resolve()
API_DIR = CURRENT_FILE.parent
BACKEND_DIR = API_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(API_DIR))

# Imports locales
try:
    from auth import AuthManager
except ImportError:
    from api.auth import AuthManager

# Configuración
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# App Flask
app = Flask(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION')
app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Rate Limiter
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
except Exception:
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
    limiter = DummyLimiter()

# Managers
auth_manager = AuthManager()

PROJECT_ROOT = BACKEND_DIR.parent
DB_PATH = Path(os.getenv('DB_PATH', str(PROJECT_ROOT / 'data' / 'notas_credito.db')))


def get_db_connection():
    """Obtiene conexión a la base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# JWT ERROR HANDLERS
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "error": "Token expirado",
        "message": "Tu sesión ha expirado. Por favor, inicia sesión nuevamente."
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "error": "Token inválido",
        "message": "El token proporcionado no es válido."
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "error": "Token no proporcionado",
        "message": "Se requiere autenticación para acceder a este recurso."
    }), 401


# ENDPOINTS DE AUTENTICACIÓN
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Autenticación de usuario"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username y password requeridos"}), 400

    username = data['username']
    password = data['password']
    ip_address = request.remote_addr or '0.0.0.0'

    autenticado, usuario, mensaje = auth_manager.autenticar(username, password, ip_address)

    if not autenticado:
        return jsonify({"error": mensaje}), 401

    user_id_str = str(usuario['id'])

    access_token = create_access_token(
        identity=user_id_str,
        additional_claims={
            'username': usuario['username'],
            'rol': usuario['rol'],
            'user_id': usuario['id']
        }
    )

    refresh_token = create_refresh_token(
        identity=user_id_str,
        additional_claims={'username': usuario['username']}
    )

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
    """Obtener nuevo access token"""
    identity = str(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, rol FROM usuarios WHERE id = ? AND activo = 1', (identity,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Usuario no encontrado o inactivo"}), 401

    access_token = create_access_token(
        identity=identity,
        additional_claims={
            'username': row['username'],
            'rol': row['rol'],
            'user_id': row['id']
        }
    )

    return jsonify({"access_token": access_token}), 200


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cerrar sesión"""
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
    return jsonify({"error": "Error al cambiar contraseña"}), 500


@app.route('/api/auth/register', methods=['POST'])
@jwt_required()
def register_user():
    """Crear nuevo usuario - Solo admins"""
    claims = get_jwt()
    if claims.get('rol') != 'admin':
        return jsonify({"error": "No tiene permisos para crear usuarios"}), 403

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username y password son requeridos"}), 400

    username = data['username']
    password = data['password']
    email = data.get('email')
    rol = data.get('rol', 'viewer')

    if rol not in ['admin', 'editor', 'viewer']:
        return jsonify({"error": "Rol inválido"}), 400

    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    if auth_manager.crear_usuario(username, password, email, rol):
        return jsonify({
            "mensaje": "Usuario creado exitosamente",
            "usuario": {"username": username, "email": email, "rol": rol}
        }), 201
    return jsonify({"error": "Error al crear usuario. Puede que ya exista."}), 400


@app.route('/api/auth/users', methods=['GET'])
@jwt_required()
def list_users():
    """Listar usuarios - Solo admins"""
    claims = get_jwt()
    if claims.get('rol') != 'admin':
        return jsonify({"error": "No tiene permisos para ver usuarios"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, username, email, rol, activo, ultimo_acceso, fecha_creacion
        FROM usuarios ORDER BY fecha_creacion DESC
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
    return jsonify({"total": len(usuarios), "usuarios": usuarios}), 200


# ENDPOINTS DE FACTURAS
@app.route('/api/facturas', methods=['GET'])
@jwt_required()
def listar_facturas():
    """Listar facturas válidas con filtros"""
    try:
        nit_cliente = request.args.get('nit_cliente')
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        con_nota = request.args.get('con_nota')
        limite = int(request.args.get('limite', 100))
        offset = int(request.args.get('offset', 0))

        query = "SELECT * FROM facturas WHERE 1=1"
        params = []

        if nit_cliente:
            query += " AND nit_cliente = ?"
            params.append(nit_cliente)

        if fecha_desde:
            query += " AND fecha_factura >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha_factura <= ?"
            params.append(fecha_hasta)

        if con_nota is not None:
            if con_nota.lower() == 'true' or con_nota == '1':
                query += " AND nota_aplicada = 1"
            elif con_nota.lower() == 'false' or con_nota == '0':
                query += " AND nota_aplicada = 0"

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

        return jsonify({
            "items": facturas,
            "total": total,
            "limite": limite,
            "offset": offset,
            "total_paginas": (total + limite - 1) // limite
        }), 200

    except Exception as e:
        logger.error(f"Error en listar_facturas: {e}")
        return jsonify({"error": "Error al obtener facturas"}), 500


@app.route('/api/facturas/<int:factura_id>', methods=['GET'])
@jwt_required()
def obtener_factura(factura_id):
    """Obtener detalles de una factura"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM facturas WHERE id = ?', (factura_id,))
        factura = cursor.fetchone()

        if not factura:
            conn.close()
            return jsonify({"error": "Factura no encontrada"}), 404

        factura_dict = dict(factura)

        # Obtener aplicaciones de notas
        cursor.execute('''
            SELECT * FROM aplicaciones_notas
            WHERE numero_factura = ?
            ORDER BY fecha_aplicacion DESC
        ''', (factura['numero_factura'],))

        factura_dict['aplicaciones'] = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(factura_dict), 200

    except Exception as e:
        logger.error(f"Error en obtener_factura: {e}")
        return jsonify({"error": "Error al obtener factura"}), 500


@app.route('/api/facturas/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas_facturas():
    """Estadísticas de facturas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM facturas')
        row = cursor.fetchone()
        stats['facturas_validas'] = row[0] or 0
        stats['valor_total_facturado'] = row[1] or 0

        cursor.execute('SELECT COUNT(*) FROM facturas WHERE nota_aplicada = 1')
        stats['facturas_con_notas'] = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(descuento_valor) FROM facturas WHERE nota_aplicada = 1')
        stats['total_descontado'] = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas')
        stats['facturas_rechazadas'] = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(valor_total) FROM facturas_rechazadas')
        stats['valor_rechazado'] = cursor.fetchone()[0] or 0

        conn.close()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error en estadisticas_facturas: {e}")
        return jsonify({"error": "Error al obtener estadísticas"}), 500


@app.route('/api/facturas/rechazadas', methods=['GET'])
@jwt_required()
def listar_facturas_rechazadas():
    """Listar facturas rechazadas"""
    try:
        limite = int(request.args.get('limite', 50))
        offset = int(request.args.get('offset', 0))
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')

        query = "SELECT * FROM facturas_rechazadas WHERE 1=1"
        params = []

        if fecha_desde:
            query += " AND fecha_factura >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha_factura <= ?"
            params.append(fecha_hasta)

        query += " ORDER BY fecha_registro DESC LIMIT ? OFFSET ?"
        params.extend([limite, offset])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query, params)
        rechazadas = [dict(row) for row in cursor.fetchall()]

        query_count = query.split('ORDER BY')[0].replace('SELECT *', 'SELECT COUNT(*)')
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
        logger.error(f"Error en listar_facturas_rechazadas: {e}")
        return jsonify({"error": "Error al obtener facturas rechazadas"}), 500


# ENDPOINTS DE NOTAS CRÉDITO
@app.route('/api/notas', methods=['GET'])
@jwt_required()
def listar_notas():
    """Listar notas de crédito"""
    try:
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

        return jsonify({
            "items": notas,
            "total": total,
            "limite": limite,
            "offset": offset,
            "total_paginas": (total + limite - 1) // limite
        }), 200

    except Exception as e:
        logger.error(f"Error en listar_notas: {e}")
        return jsonify({"error": "Error al obtener notas"}), 500


@app.route('/api/notas/<int:nota_id>', methods=['GET'])
@jwt_required()
def obtener_nota(nota_id):
    """Obtener detalles de una nota"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM notas_credito WHERE id = ?', (nota_id,))
        nota = cursor.fetchone()

        if not nota:
            conn.close()
            return jsonify({"error": "Nota no encontrada"}), 404

        nota_dict = dict(nota)

        # Obtener historial de aplicaciones
        cursor.execute('''
            SELECT * FROM aplicaciones_notas
            WHERE id_nota = ?
            ORDER BY fecha_aplicacion DESC
        ''', (nota_id,))

        nota_dict['aplicaciones'] = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(nota_dict), 200

    except Exception as e:
        logger.error(f"Error en obtener_nota: {e}")
        return jsonify({"error": "Error al obtener nota"}), 500


@app.route('/api/notas/estadisticas', methods=['GET'])
@jwt_required()
def estadisticas_notas():
    """Estadísticas de notas de crédito"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM notas_credito')
        row = cursor.fetchone()
        stats['total_notas'] = row[0] or 0
        stats['valor_total'] = row[1] or 0

        cursor.execute('''
            SELECT estado, COUNT(*), SUM(saldo_pendiente)
            FROM notas_credito GROUP BY estado
        ''')
        for row in cursor.fetchall():
            estado_lower = row[0].lower()
            stats[f'notas_{estado_lower}'] = row[1]
            stats[f'saldo_{estado_lower}'] = row[2] or 0

        cursor.execute('SELECT SUM(saldo_pendiente) FROM notas_credito WHERE estado != "APLICADA"')
        stats['saldo_pendiente_total'] = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*), SUM(valor_aplicado) FROM aplicaciones_notas')
        row = cursor.fetchone()
        stats['total_aplicaciones'] = row[0] or 0
        stats['monto_total_aplicado'] = row[1] or 0

        conn.close()
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error en estadisticas_notas: {e}")
        return jsonify({"error": "Error al obtener estadísticas"}), 500


@app.route('/api/aplicaciones/<numero_nota>', methods=['GET'])
@jwt_required()
def obtener_aplicaciones(numero_nota):
    """Obtener aplicaciones de una nota"""
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
        logger.error(f"Error en obtener_aplicaciones: {e}")
        return jsonify({"error": "Error al obtener aplicaciones"}), 500


# REPORTE OPERATIVO
@app.route('/api/reporte/operativo', methods=['GET'])
@jwt_required()
def reporte_operativo():
    """Reporte operativo diario"""
    try:
        fecha = request.args.get('fecha')
        if not fecha:
            fecha_obj = datetime.now() - timedelta(days=1)
            fecha = fecha_obj.strftime('%Y-%m-%d')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Notas de la fecha
        cursor.execute('''
            SELECT * FROM notas_credito
            WHERE DATE(fecha_nota) = ? OR DATE(fecha_registro) = ?
            ORDER BY fecha_nota DESC
        ''', (fecha, fecha))
        notas = [dict(row) for row in cursor.fetchall()]

        # Aplicaciones de la fecha
        cursor.execute('''
            SELECT * FROM aplicaciones_notas
            WHERE DATE(fecha_aplicacion) = ?
            ORDER BY fecha_aplicacion DESC
        ''', (fecha,))
        aplicaciones = [dict(row) for row in cursor.fetchall()]

        # Facturas rechazadas de la fecha
        cursor.execute('''
            SELECT * FROM facturas_rechazadas
            WHERE DATE(fecha_factura) = ?
            ORDER BY fecha_factura DESC
        ''', (fecha,))
        rechazadas = [dict(row) for row in cursor.fetchall()]

        # Resumen general
        cursor.execute('''
            SELECT COUNT(*), SUM(saldo_pendiente)
            FROM notas_credito WHERE estado = 'PENDIENTE'
        ''')
        row = cursor.fetchone()
        resumen = {
            'notas_pendientes': row[0] or 0,
            'saldo_pendiente': row[1] or 0
        }

        cursor.execute('SELECT COUNT(*) FROM notas_credito WHERE estado = "APLICADA"')
        resumen['notas_aplicadas'] = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            "fecha": fecha,
            "notas_credito": notas,
            "aplicaciones": aplicaciones,
            "facturas_rechazadas": rechazadas,
            "resumen": resumen
        }), 200

    except Exception as e:
        logger.error(f"Error en reporte_operativo: {e}")
        return jsonify({"error": "Error al generar reporte"}), 500


# DASHBOARD
@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Datos del dashboard principal"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        data = {}

        # Facturas
        cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM facturas')
        row = cursor.fetchone()
        data['facturas_validas'] = row[0] or 0
        data['valor_total_facturado'] = row[1] or 0

        cursor.execute('SELECT COUNT(*) FROM facturas WHERE nota_aplicada = 1')
        data['facturas_con_notas'] = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(descuento_cantidad), SUM(descuento_valor) FROM facturas')
        row = cursor.fetchone()
        data['total_descuento_cantidad'] = row[0] or 0
        data['total_descuento_valor'] = row[1] or 0

        # Rechazadas
        cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM facturas_rechazadas')
        row = cursor.fetchone()
        data['facturas_rechazadas'] = row[0] or 0
        data['valor_rechazado'] = row[1] or 0

        # Notas
        cursor.execute('SELECT COUNT(*), SUM(saldo_pendiente) FROM notas_credito WHERE estado = "PENDIENTE"')
        row = cursor.fetchone()
        data['notas_pendientes'] = row[0] or 0
        data['saldo_pendiente'] = row[1] or 0

        cursor.execute('SELECT COUNT(*) FROM notas_credito WHERE estado = "APLICADA"')
        data['notas_aplicadas'] = cursor.fetchone()[0]

        # Últimas aplicaciones
        cursor.execute('''
            SELECT numero_nota, numero_factura, numero_linea, cantidad_aplicada, valor_aplicado, fecha_aplicacion
            FROM aplicaciones_notas ORDER BY fecha_aplicacion DESC LIMIT 10
        ''')
        data['ultimas_aplicaciones'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return jsonify(data), 200

    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        return jsonify({"error": "Error al obtener datos del dashboard"}), 500


# =========================================================================
# ENDPOINTS DE ADMIN - EXPORTACIÓN Y PROCESAMIENTO
# =========================================================================

@app.route('/api/admin/exportar-excel', methods=['POST'])
@jwt_required()
def exportar_excel_bd():
    """
    Exporta datos de la BD a Excel por rango de fechas
    Solo para admins
    """
    try:
        claims = get_jwt()
        if claims.get('rol') != 'admin':
            return jsonify({"error": "No tiene permisos para exportar"}), 403

        data = request.get_json()
        fecha_desde = data.get('fecha_desde')
        fecha_hasta = data.get('fecha_hasta')
        tipo = data.get('tipo', 'facturas')  # facturas, notas, rechazadas

        if not fecha_desde or not fecha_hasta:
            return jsonify({"error": "Fechas requeridas"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Determinar query según tipo
        if tipo == 'facturas':
            cursor.execute('''
                SELECT numero_linea, numero_factura, producto, codigo_producto,
                       nombre_cliente, nit_cliente, cantidad_original, precio_unitario,
                       valor_total, nota_aplicada, numero_nota_aplicada,
                       descuento_cantidad, descuento_valor, cantidad_restante,
                       valor_restante, fecha_factura
                FROM facturas
                WHERE fecha_factura >= ? AND fecha_factura <= ?
                ORDER BY fecha_factura DESC, numero_factura
            ''', (fecha_desde, fecha_hasta))
            columns = ['Linea', 'Factura', 'Producto', 'Codigo', 'Cliente', 'NIT',
                      'Cantidad', 'Precio Unit', 'Valor Total', 'Nota Aplicada',
                      'Num Nota', 'Desc Cantidad', 'Desc Valor', 'Cant Rest',
                      'Valor Rest', 'Fecha']

        elif tipo == 'notas':
            cursor.execute('''
                SELECT numero_nota, fecha_nota, nombre_cliente, nit_cliente,
                       nombre_producto, codigo_producto, cantidad, valor_total,
                       cantidad_pendiente, saldo_pendiente, estado, causal_devolucion
                FROM notas_credito
                WHERE fecha_nota >= ? AND fecha_nota <= ?
                ORDER BY fecha_nota DESC
            ''', (fecha_desde, fecha_hasta))
            columns = ['Nota', 'Fecha', 'Cliente', 'NIT', 'Producto', 'Codigo',
                      'Cantidad', 'Valor Total', 'Cant Pend', 'Saldo Pend',
                      'Estado', 'Causal']

        elif tipo == 'rechazadas':
            cursor.execute('''
                SELECT numero_factura, numero_linea, producto, codigo_producto,
                       nombre_cliente, nit_cliente, cantidad, valor_total,
                       tipo_inventario, razon_rechazo, fecha_factura
                FROM facturas_rechazadas
                WHERE fecha_factura >= ? AND fecha_factura <= ?
                ORDER BY fecha_factura DESC
            ''', (fecha_desde, fecha_hasta))
            columns = ['Factura', 'Linea', 'Producto', 'Codigo', 'Cliente', 'NIT',
                      'Cantidad', 'Valor', 'Tipo Inv', 'Razon Rechazo', 'Fecha']

        elif tipo == 'aplicaciones':
            cursor.execute('''
                SELECT numero_nota, numero_factura, numero_linea, nit_cliente,
                       codigo_producto, cantidad_aplicada, valor_aplicado, fecha_aplicacion
                FROM aplicaciones_notas
                WHERE DATE(fecha_aplicacion) >= ? AND DATE(fecha_aplicacion) <= ?
                ORDER BY fecha_aplicacion DESC
            ''', (fecha_desde, fecha_hasta))
            columns = ['Nota', 'Factura', 'Linea', 'NIT', 'Codigo',
                      'Cantidad Aplicada', 'Valor Aplicado', 'Fecha']
        else:
            return jsonify({"error": "Tipo inválido"}), 400

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return jsonify({"error": "No hay datos para el rango seleccionado"}), 404

        # Generar Excel
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
        except ImportError:
            return jsonify({"error": "openpyxl no instalado"}), 500

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = tipo.capitalize()

        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Headers
        for col, header in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = thin_border

        # Datos
        for row_idx, row in enumerate(rows, 2):
            for col_idx, value in enumerate(row, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border

        # Ajustar anchos
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        # Guardar
        output_dir = PROJECT_ROOT / 'output'
        output_dir.mkdir(exist_ok=True)

        filename = f"export_{tipo}_{fecha_desde}_{fecha_hasta}.xlsx"
        output_path = output_dir / filename

        wb.save(str(output_path))

        return jsonify({
            "exito": True,
            "mensaje": f"Excel generado con {len(rows)} registros",
            "archivo": filename,
            "total_registros": len(rows)
        }), 200

    except Exception as e:
        logger.error(f"Error en exportar_excel_bd: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al exportar: {str(e)}"}), 500


@app.route('/api/admin/descargar/<filename>', methods=['GET'])
@jwt_required()
def descargar_archivo(filename):
    """Descarga un archivo generado"""
    try:
        from flask import send_file

        # Validar nombre de archivo (seguridad)
        if '..' in filename or '/' in filename:
            return jsonify({"error": "Nombre de archivo inválido"}), 400

        output_dir = PROJECT_ROOT / 'output'
        file_path = output_dir / filename

        if not file_path.exists():
            return jsonify({"error": "Archivo no encontrado"}), 404

        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error al descargar archivo: {e}")
        return jsonify({"error": "Error al descargar archivo"}), 500


@app.route('/api/admin/procesar-rango', methods=['POST'])
@jwt_required()
def procesar_rango():
    """
    Procesa un rango de fechas desde la API externa y guarda en BD
    Solo para admins - Proceso largo
    """
    try:
        claims = get_jwt()
        if claims.get('rol') != 'admin':
            return jsonify({"error": "No tiene permisos"}), 403

        data = request.get_json()
        fecha_desde_str = data.get('fecha_desde')
        fecha_hasta_str = data.get('fecha_hasta')

        if not fecha_desde_str or not fecha_hasta_str:
            return jsonify({"error": "Fechas requeridas"}), 400

        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d')

        # Validar rango máximo 90 días
        diff_days = (fecha_hasta - fecha_desde).days
        if diff_days > 90:
            return jsonify({"error": "Rango máximo permitido: 90 días"}), 400

        if fecha_desde > fecha_hasta:
            return jsonify({"error": "Fecha desde debe ser anterior a fecha hasta"}), 400

        # Importar función de procesamiento
        sys.path.insert(0, str(BACKEND_DIR))
        from main import procesar_rango_fechas

        # Configuración
        config = {
            'CONNI_KEY': os.getenv('CONNI_KEY'),
            'CONNI_TOKEN': os.getenv('CONNI_TOKEN'),
            'DB_PATH': str(DB_PATH),
            'TEMPLATE_PATH': os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')
        }

        if not config['CONNI_KEY'] or not config['CONNI_TOKEN']:
            return jsonify({"error": "Credenciales API no configuradas"}), 500

        # Ejecutar procesamiento
        resultado = procesar_rango_fechas(fecha_desde, fecha_hasta, config)

        return jsonify(resultado), 200

    except Exception as e:
        logger.error(f"Error en procesar_rango: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error al procesar: {str(e)}"}), 500


@app.route('/api/admin/archivos', methods=['GET'])
@jwt_required()
def listar_archivos():
    """Lista archivos disponibles para descarga"""
    try:
        output_dir = PROJECT_ROOT / 'output'

        if not output_dir.exists():
            return jsonify({"archivos": []}), 200

        archivos = []
        for f in output_dir.iterdir():
            if f.is_file() and f.suffix in ['.xlsx', '.txt']:
                archivos.append({
                    'nombre': f.name,
                    'tamaño': f.stat().st_size,
                    'fecha_modificacion': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })

        archivos.sort(key=lambda x: x['fecha_modificacion'], reverse=True)

        return jsonify({"archivos": archivos}), 200

    except Exception as e:
        logger.error(f"Error al listar archivos: {e}")
        return jsonify({"error": "Error al listar archivos"}), 500


# HEALTH CHECK
@app.route('/api/health', methods=['GET'])
def health():
    """Health check - sin autenticación"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }), 200


# ERROR HANDLERS
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 2500))
    logger.info(f"Iniciando API en puerto {port}")
    logger.info(f"Base de datos: {DB_PATH}")
    app.run(host='0.0.0.0', port=port, debug=True)
