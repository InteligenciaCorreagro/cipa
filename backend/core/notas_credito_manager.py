"""
Módulo de Gestión de Notas Crédito - VERSIÓN REESTRUCTURADA
Maneja la aplicación de notas crédito a facturas con persistencia en SQLite

ESTRUCTURA DE BD:
- facturas: Líneas de facturas válidas con info de notas aplicadas
- facturas_rechazadas: Facturas que no cumplen reglas de negocio
- notas_credito: Notas de crédito que cumplen reglas de negocio
- usuarios: Usuarios del dashboard
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import os
import re
import json
try:
    from db import get_connection, get_engine, get_sqlite_path
except ImportError:
    from backend.db import get_connection, get_engine, get_sqlite_path

logger = logging.getLogger(__name__)


class NotasCreditoManager:
    """Gestiona la aplicación de notas crédito a facturas"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el gestor de notas crédito

        Args:
            db_path: Ruta de la base de datos SQLite
        """
        self.db_path = db_path
        self._crear_base_datos()
        if get_engine(self.db_path) == 'mysql':
            logger.info("NotasCreditoManager inicializado con BD: MySQL")
        else:
            logger.info(f"NotasCreditoManager inicializado con BD: {db_path or get_sqlite_path('./data/notas_credito.db')}")

    def _crear_base_datos(self):
        """Crea las tablas necesarias en la base de datos si no existen"""
        engine = get_engine(self.db_path)
        if engine == 'sqlite':
            os.makedirs(os.path.dirname(self.db_path or get_sqlite_path('./data/notas_credito.db')), exist_ok=True)
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        if engine == 'mysql':
            def _create_index(name: str, table: str, columns: str):
                try:
                    cursor.execute(f"CREATE INDEX {name} ON {table}({columns})")
                except Exception:
                    pass
            def _ensure_column(table: str, column_def: str):
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
                except Exception:
                    pass
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facturas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_linea VARCHAR(100) NOT NULL,
                    numero_factura VARCHAR(100) NOT NULL,
                    indice_linea INT DEFAULT 0,
                    codigo_producto VARCHAR(100) NOT NULL,
                    nombre_producto TEXT NOT NULL,
                    nit_encrypted VARCHAR(50) NOT NULL,
                    nit_hash VARCHAR(50) NOT NULL,
                    nombre_cliente_encrypted TEXT NOT NULL,
                    cantidad_original DOUBLE NOT NULL,
                    valor_total DOUBLE NOT NULL,
                    cantidad_restante DOUBLE NOT NULL,
                    valor_restante DOUBLE NOT NULL,
                    estado VARCHAR(20) DEFAULT 'ACTIVA',
                    codigo_factura VARCHAR(100) NOT NULL,
                    repeticion_index INT DEFAULT 1,
                    total_repeticiones INT DEFAULT 1,
                    suma_total_repeticiones DOUBLE DEFAULT 0,
                    registrable INT DEFAULT 1,
                    fecha_factura DATE NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_facturas (numero_factura, codigo_producto, indice_linea, fecha_factura)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            _create_index('idx_facturas_numero', 'facturas', 'numero_factura')
            _create_index('idx_facturas_linea', 'facturas', 'numero_linea')
            _create_index('idx_facturas_producto', 'facturas', 'codigo_producto')
            _create_index('idx_facturas_fecha', 'facturas', 'fecha_factura')
            _create_index('idx_facturas_indice', 'facturas', 'indice_linea')
            _create_index('idx_facturas_nit', 'facturas', 'nit_encrypted')
            _create_index('idx_facturas_codigo_factura', 'facturas', 'codigo_factura')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS facturas_rechazadas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_factura VARCHAR(100) NOT NULL,
                    numero_linea VARCHAR(100),
                    codigo_producto VARCHAR(100),
                    producto TEXT,
                    nit_encrypted VARCHAR(50),
                    nit_hash VARCHAR(50),
                    nombre_cliente_encrypted TEXT,
                    cantidad DOUBLE,
                    valor_total DOUBLE,
                    tipo_inventario VARCHAR(100),
                    razon_rechazo TEXT NOT NULL,
                    fecha_factura DATE,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            _create_index('idx_rechazadas_fecha', 'facturas_rechazadas', 'fecha_factura')
            _create_index('idx_rechazadas_razon', 'facturas_rechazadas', 'razon_rechazo(255)')
            _create_index('idx_rechazadas_nit', 'facturas_rechazadas', 'nit_encrypted')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notas_credito (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_nota VARCHAR(100) NOT NULL,
                    fecha_nota DATE NOT NULL,
                    nit_encrypted VARCHAR(50) NOT NULL,
                    nit_hash VARCHAR(50) NOT NULL,
                    nombre_cliente_encrypted TEXT NOT NULL,
                    codigo_producto VARCHAR(100) NOT NULL,
                    nombre_producto TEXT NOT NULL,
                    valor_total DOUBLE NOT NULL,
                    cantidad DOUBLE NOT NULL,
                    saldo_pendiente DOUBLE NOT NULL,
                    cantidad_pendiente DOUBLE NOT NULL,
                    estado VARCHAR(20) DEFAULT 'PENDIENTE',
                    causal_devolucion TEXT,
                    es_agente INT DEFAULT 0,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_aplicacion_completa TIMESTAMP NULL,
                    UNIQUE KEY uniq_notas (numero_nota, codigo_producto)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            _create_index('idx_notas_cliente', 'notas_credito', 'nit_encrypted')
            _create_index('idx_notas_producto', 'notas_credito', 'codigo_producto')
            _create_index('idx_notas_estado', 'notas_credito', 'estado')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aplicaciones_notas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_nota INT NOT NULL,
                    id_factura INT NOT NULL,
                    numero_nota VARCHAR(100) NOT NULL,
                    numero_factura VARCHAR(100) NOT NULL,
                    numero_linea VARCHAR(100),
                    fecha_factura DATE NOT NULL,
                    nit_hash VARCHAR(50) NOT NULL,
                    codigo_producto VARCHAR(100) NOT NULL,
                    cantidad_aplicada DOUBLE NOT NULL,
                    valor_aplicado DOUBLE NOT NULL,
                    cantidad_factura_antes DOUBLE NOT NULL,
                    cantidad_factura_despues DOUBLE NOT NULL,
                    valor_factura_antes DOUBLE NOT NULL,
                    valor_factura_despues DOUBLE NOT NULL,
                    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            _create_index('idx_aplicaciones_nota', 'aplicaciones_notas', 'numero_nota')
            _create_index('idx_aplicaciones_factura', 'aplicaciones_notas', 'numero_factura')
            _create_index('idx_aplicaciones_nit', 'aplicaciones_notas', 'nit_hash')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS log_motivos_no_aplicacion (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_nota INT,
                    numero_nota VARCHAR(100) NOT NULL,
                    numero_factura VARCHAR(100),
                    motivo TEXT NOT NULL,
                    detalle TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            _create_index('idx_log_no_aplicacion_nota', 'log_motivos_no_aplicacion', 'numero_nota')
            _create_index('idx_log_no_aplicacion_fecha', 'log_motivos_no_aplicacion', 'fecha_registro')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    entidad VARCHAR(100) NOT NULL,
                    accion VARCHAR(100) NOT NULL,
                    entidad_id VARCHAR(100),
                    usuario VARCHAR(100),
                    payload TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            _create_index('idx_audit_entidad', 'audit_logs', 'entidad')
            _create_index('idx_audit_fecha', 'audit_logs', 'fecha_registro')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    email VARCHAR(255),
                    rol VARCHAR(20) DEFAULT 'viewer',
                    activo INT DEFAULT 1,
                    intentos_fallidos INT DEFAULT 0,
                    bloqueado_hasta TIMESTAMP NULL,
                    ultimo_acceso TIMESTAMP NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sesiones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    token_jti VARCHAR(255) NOT NULL UNIQUE,
                    refresh_jti VARCHAR(255) UNIQUE,
                    ip_address VARCHAR(100),
                    user_agent TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_expiracion TIMESTAMP NULL,
                    activa INT DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intentos_login (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    ip_address VARCHAR(100),
                    exitoso INT NOT NULL,
                    razon_fallo TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notas_pendientes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_nota VARCHAR(100) NOT NULL,
                    prioridad VARCHAR(20) DEFAULT 'media',
                    fecha_vencimiento DATE,
                    responsable VARCHAR(100),
                    estado VARCHAR(20) DEFAULT 'PENDIENTE',
                    descripcion TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aplicaciones_sistema (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(200) NOT NULL,
                    version VARCHAR(50) NOT NULL,
                    fecha_instalacion DATE,
                    estado VARCHAR(20) DEFAULT 'ACTIVA',
                    uso_total INT DEFAULT 0,
                    ultimo_uso TIMESTAMP NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notas_aplicadas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_nota VARCHAR(100) NOT NULL,
                    numero_factura VARCHAR(100) NOT NULL,
                    numero_linea VARCHAR(100),
                    codigo_producto VARCHAR(100) NOT NULL,
                    nit_cliente VARCHAR(50),
                    cantidad_aplicada DOUBLE NOT NULL,
                    cantidad_aplicada_kilos DOUBLE DEFAULT 0,
                    valor_aplicado DOUBLE NOT NULL,
                    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payload_nota LONGTEXT,
                    payload_factura LONGTEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            _create_index('idx_notas_aplicadas_nota', 'notas_aplicadas', 'numero_nota')
            _create_index('idx_notas_aplicadas_factura', 'notas_aplicadas', 'numero_factura')

            _ensure_column('facturas', 'cantidad_kilos DOUBLE DEFAULT 0')
            _ensure_column('facturas', 'raw_payload LONGTEXT')
            _ensure_column('facturas_rechazadas', 'cantidad_kilos DOUBLE DEFAULT 0')
            _ensure_column('facturas_rechazadas', 'raw_payload LONGTEXT')
            _ensure_column('notas_credito', 'cantidad_kilos DOUBLE DEFAULT 0')
            _ensure_column('notas_credito', 'raw_payload LONGTEXT')
            _ensure_column('notas_pendientes', 'codigo_producto VARCHAR(100)')
            _ensure_column('notas_pendientes', 'nit_cliente VARCHAR(50)')
            _ensure_column('notas_pendientes', 'saldo_pendiente DOUBLE DEFAULT 0')
            _ensure_column('notas_pendientes', 'cantidad_pendiente DOUBLE DEFAULT 0')
            _ensure_column('notas_pendientes', 'cantidad_pendiente_kilos DOUBLE DEFAULT 0')
            _ensure_column('notas_pendientes', 'raw_payload LONGTEXT')

            conn.commit()
            conn.close()
            logger.info("Base de datos inicializada correctamente con todas las tablas")
            return

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_linea TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                indice_linea INTEGER DEFAULT 0,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                nit_encrypted TEXT NOT NULL,
                nit_hash TEXT NOT NULL,
                nombre_cliente_encrypted TEXT NOT NULL,
                cantidad_original REAL NOT NULL,
                valor_total REAL NOT NULL,
                cantidad_restante REAL NOT NULL,
                valor_restante REAL NOT NULL,
                estado TEXT DEFAULT 'ACTIVA',
                codigo_factura TEXT NOT NULL,
                repeticion_index INTEGER DEFAULT 1,
                total_repeticiones INTEGER DEFAULT 1,
                suma_total_repeticiones REAL DEFAULT 0,
                registrable INTEGER DEFAULT 1,
                fecha_factura DATE NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(numero_factura, codigo_producto, indice_linea, fecha_factura)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_linea ON facturas(numero_linea)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_producto ON facturas(codigo_producto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_indice ON facturas(indice_linea)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_nit ON facturas(nit_encrypted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_codigo_factura ON facturas(codigo_factura)')

        # =========================================================================
        # TABLA FACTURAS_RECHAZADAS
        # Facturas que no cumplen con las reglas de negocio
        # =========================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas_rechazadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT NOT NULL,
                numero_linea TEXT,
                codigo_producto TEXT,
                producto TEXT,
                nit_encrypted TEXT,
                nit_hash TEXT,
                nombre_cliente_encrypted TEXT,
                cantidad REAL,
                valor_total REAL,
                tipo_inventario TEXT,
                razon_rechazo TEXT NOT NULL,
                fecha_factura DATE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rechazadas_fecha ON facturas_rechazadas(fecha_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rechazadas_razon ON facturas_rechazadas(razon_rechazo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rechazadas_nit ON facturas_rechazadas(nit_encrypted)')

        # =========================================================================
        # TABLA NOTAS_CREDITO
        # Notas de crédito que cumplen con las reglas de negocio
        # =========================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_nota TEXT NOT NULL,
                fecha_nota DATE NOT NULL,
                nit_encrypted TEXT NOT NULL,
                nit_hash TEXT NOT NULL,
                nombre_cliente_encrypted TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,
                saldo_pendiente REAL NOT NULL,
                cantidad_pendiente REAL NOT NULL,
                estado TEXT DEFAULT 'PENDIENTE',
                causal_devolucion TEXT,
                es_agente INTEGER DEFAULT 0,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aplicacion_completa TIMESTAMP NULL,

                UNIQUE(numero_nota, codigo_producto)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas_credito(nit_encrypted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas_producto ON notas_credito(codigo_producto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas_estado ON notas_credito(estado)')

        # =========================================================================
        # TABLA APLICACIONES_NOTAS
        # Historial de aplicaciones de notas a facturas
        # =========================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aplicaciones_notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_nota INTEGER NOT NULL,
                id_factura INTEGER NOT NULL,
                numero_nota TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                numero_linea TEXT,
                fecha_factura DATE NOT NULL,
                nit_hash TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                cantidad_aplicada REAL NOT NULL,
                valor_aplicado REAL NOT NULL,
                cantidad_factura_antes REAL NOT NULL,
                cantidad_factura_despues REAL NOT NULL,
                valor_factura_antes REAL NOT NULL,
                valor_factura_despues REAL NOT NULL,
                fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nota) REFERENCES notas_credito(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aplicaciones_nota ON aplicaciones_notas(numero_nota)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aplicaciones_factura ON aplicaciones_notas(numero_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aplicaciones_nit ON aplicaciones_notas(nit_hash)')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_motivos_no_aplicacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_nota INTEGER,
                numero_nota TEXT NOT NULL,
                numero_factura TEXT,
                motivo TEXT NOT NULL,
                detalle TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nota) REFERENCES notas_credito(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_no_aplicacion_nota ON log_motivos_no_aplicacion(numero_nota)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_log_no_aplicacion_fecha ON log_motivos_no_aplicacion(fecha_registro)')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entidad TEXT NOT NULL,
                accion TEXT NOT NULL,
                entidad_id TEXT,
                usuario TEXT,
                payload TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_entidad ON audit_logs(entidad)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_fecha ON audit_logs(fecha_registro)')

        # =========================================================================
        # TABLA USUARIOS
        # Usuarios del dashboard
        # =========================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT,
                rol TEXT DEFAULT 'viewer',
                activo INTEGER DEFAULT 1,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado_hasta TIMESTAMP NULL,
                ultimo_acceso TIMESTAMP NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tablas de soporte para autenticación
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_jti TEXT NOT NULL UNIQUE,
                refresh_jti TEXT UNIQUE,
                ip_address TEXT,
                user_agent TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion TIMESTAMP NOT NULL,
                activa INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intentos_login (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT,
                exitoso INTEGER NOT NULL,
                razon_fallo TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_pendientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_nota TEXT NOT NULL,
                prioridad TEXT DEFAULT 'media',
                fecha_vencimiento DATE,
                responsable TEXT,
                estado TEXT DEFAULT 'PENDIENTE',
                descripcion TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aplicaciones_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                version TEXT NOT NULL,
                fecha_instalacion DATE,
                estado TEXT DEFAULT 'ACTIVA',
                uso_total INTEGER DEFAULT 0,
                ultimo_uso TIMESTAMP NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_aplicadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_nota TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                numero_linea TEXT,
                codigo_producto TEXT NOT NULL,
                nit_cliente TEXT,
                cantidad_aplicada REAL NOT NULL,
                cantidad_aplicada_kilos REAL DEFAULT 0,
                valor_aplicado REAL NOT NULL,
                fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payload_nota TEXT,
                payload_factura TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas_aplicadas_nota ON notas_aplicadas(numero_nota)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas_aplicadas_factura ON notas_aplicadas(numero_factura)')

        for table, column_def in [
            ('facturas', 'cantidad_kilos REAL DEFAULT 0'),
            ('facturas', 'raw_payload TEXT'),
            ('facturas_rechazadas', 'cantidad_kilos REAL DEFAULT 0'),
            ('facturas_rechazadas', 'raw_payload TEXT'),
            ('notas_credito', 'cantidad_kilos REAL DEFAULT 0'),
            ('notas_credito', 'raw_payload TEXT'),
            ('notas_pendientes', 'codigo_producto TEXT'),
            ('notas_pendientes', 'nit_cliente TEXT'),
            ('notas_pendientes', 'saldo_pendiente REAL DEFAULT 0'),
            ('notas_pendientes', 'cantidad_pendiente REAL DEFAULT 0'),
            ('notas_pendientes', 'cantidad_pendiente_kilos REAL DEFAULT 0'),
            ('notas_pendientes', 'raw_payload TEXT')
        ]:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column_def}')
            except Exception:
                pass

        conn.commit()
        conn.close()

        logger.info("Base de datos inicializada correctamente con todas las tablas")

    def _get_connection(self):
        return get_connection(self.db_path)

    def _is_encrypted_value(self, value: Optional[str]) -> bool:
        if not value:
            return False
        return str(value).startswith('gAAAA')

    def _validate_plain_text(self, value: Optional[str], field: str, factura_id: str):
        if self._is_encrypted_value(value):
            raise ValueError(f"factura_id={factura_id} campo={field} contiene_encriptacion")

    def _normalizar_producto(self, value: Optional[str]) -> str:
        return re.sub(r'\s+', ' ', str(value or '').strip().upper())

    def _validate_nit(self, nit: str, factura_id: str):
        if not nit.isdigit() or len(nit) < 5 or len(nit) > 20:
            raise ValueError(f"factura_id={factura_id} campo=nit_cliente formato_invalido")

    def _registrar_auditoria(self, conn: Any, entidad: str, accion: str,
                             entidad_id: Optional[str], usuario: Optional[str], payload: Dict):
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (entidad, accion, entidad_id, usuario, payload)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            entidad,
            accion,
            entidad_id,
            usuario,
            json.dumps(payload, ensure_ascii=False)
        ))

    def registrar_nota_credito(self, nota: Dict, usuario: Optional[str] = None) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            numero_nota = str(nota.get('numero_nota') or f"{nota.get('f_prefijo', '')}{nota.get('f_nrodocto', '')}").strip()
            fecha_nota_str = nota.get('fecha_nota') or nota.get('f_fecha', '')

            if fecha_nota_str:
                try:
                    fecha_nota = datetime.fromisoformat(str(fecha_nota_str).replace('T00:00:00', '')).date()
                except:
                    fecha_nota = datetime.now().date()
            else:
                fecha_nota = datetime.now().date()

            nit_cliente = str(nota.get('nit_cliente') or nota.get('f_cliente_desp', '')).strip()
            nombre_cliente = str(nota.get('nombre_cliente') or nota.get('f_cliente_fact_razon_soc', '')).strip()
            codigo_producto = str(
                nota.get('codigo_producto')
                or nota.get('f_cod_item')
                or nota.get('f_rowid_movto')
                or nota.get('f_rowid')
                or nota.get('f_desc_item', '')
            ).strip()
            nombre_producto = str(nota.get('nombre_producto') or nota.get('f_desc_item', '')).strip()
            valor_total = abs(float(nota.get('valor_total', nota.get('f_valor_subtotal_local', 0.0)) or 0.0))
            cantidad = abs(float(nota.get('cantidad', nota.get('f_cant_base', 0.0)) or 0.0))
            cantidad_kilos = abs(float(nota.get('cantidad_kilos', nota.get('f_peso', cantidad)) or 0.0))
            causal_devolucion = str(nota.get('causal_devolucion', nota.get('f_notas_causal_dev', '') or '')).strip() or None

            if not numero_nota or not codigo_producto or not nit_cliente:
                conn.close()
                return False

            self._validate_plain_text(nit_cliente, 'nit_cliente', numero_nota)
            self._validate_plain_text(nombre_cliente, 'nombre_cliente', numero_nota)
            self._validate_nit(nit_cliente, numero_nota)

            agente_raw = str(nota.get('es_agente', nota.get('f_02_014', ''))).upper()
            es_agente = 1 if 'AGENTE' in agente_raw and 'NO AGENTE' not in agente_raw else 0

            nit_hash = nit_cliente
            nit_enc = nit_cliente
            nombre_enc = nombre_cliente

            cursor.execute(
                'SELECT id FROM notas_credito WHERE numero_nota = ? AND codigo_producto = ?',
                (numero_nota, codigo_producto)
            )

            if cursor.fetchone():
                conn.close()
                return False

            cursor.execute('''
                INSERT INTO notas_credito
                (numero_nota, fecha_nota, nit_encrypted, nit_hash, nombre_cliente_encrypted,
                 codigo_producto, nombre_producto, valor_total, cantidad,
                 saldo_pendiente, cantidad_pendiente, cantidad_kilos, raw_payload, causal_devolucion, estado, es_agente)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)
            ''', (numero_nota, fecha_nota, nit_enc, nit_hash, nombre_enc,
                  codigo_producto, nombre_producto, valor_total, cantidad,
                  valor_total, cantidad, cantidad_kilos, json.dumps(nota, ensure_ascii=False), causal_devolucion, es_agente))

            try:
                cursor.execute('''
                    INSERT INTO notas_pendientes
                    (numero_nota, codigo_producto, nit_cliente, estado, descripcion,
                     saldo_pendiente, cantidad_pendiente, cantidad_pendiente_kilos, raw_payload)
                    VALUES (?, ?, ?, 'PENDIENTE', ?, ?, ?, ?, ?)
                ''', (
                    numero_nota,
                    codigo_producto,
                    nit_cliente,
                    causal_devolucion or 'Pendiente por aplicar',
                    valor_total,
                    cantidad,
                    cantidad_kilos,
                    json.dumps(nota, ensure_ascii=False)
                ))
            except Exception:
                pass

            self._registrar_auditoria(conn, 'nota_credito', 'crear', numero_nota, usuario, {
                'numero_nota': numero_nota,
                'codigo_producto': codigo_producto,
                'valor_total': valor_total,
                'cantidad': cantidad,
                'es_agente': bool(es_agente)
            })

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error al registrar nota crédito: {e}")
            import traceback
            traceback.print_exc()
            return False

    def registrar_factura(self, factura: Dict, usuario: Optional[str] = None,
                          conn: Optional[Any] = None,
                          cursor: Optional[Any] = None,
                          commit: bool = True) -> bool:
        try:
            local_conn = conn or self._get_connection()
            local_cursor = cursor or local_conn.cursor()
            if commit:
                local_cursor.execute('BEGIN')

            es_factura_cruda = any(k in factura for k in ('f_prefijo', 'f_nrodocto', 'f_cod_item'))

            if es_factura_cruda:
                fecha_raw = factura.get('f_fecha')
            else:
                fecha_raw = factura.get('fecha_factura')

            if isinstance(fecha_raw, str):
                try:
                    fecha_factura = datetime.fromisoformat(str(fecha_raw).replace('T00:00:00', '')).date()
                except:
                    try:
                        fecha_factura = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
                    except:
                        fecha_factura = datetime.now().date()
            elif hasattr(fecha_raw, 'date'):
                fecha_factura = fecha_raw.date() if callable(fecha_raw.date) else fecha_raw
            else:
                fecha_factura = datetime.now().date()

            if es_factura_cruda:
                prefijo = str(factura.get('f_prefijo', '')).strip()
                nrodocto = str(factura.get('f_nrodocto', '')).strip()
                numero_factura = f"{prefijo}{nrodocto}"
                indice_linea = int(factura.get('_indice_linea', factura.get('indice_linea', 0)) or 0)
                codigo_producto = str(
                    factura.get('f_cod_item')
                    or factura.get('f_rowid_movto')
                    or factura.get('f_rowid')
                    or factura.get('f_desc_item', '')
                ).strip()
                nombre_producto = str(factura.get('f_desc_item', '')).strip()
                nit_cliente = str(factura.get('f_cliente_desp', '')).strip()
                nombre_cliente = str(factura.get('f_cliente_fact_razon_soc', '')).strip()
                cantidad_original = float(factura.get('f_cant_base', 0.0) or 0.0)
                valor_total = float(factura.get('f_valor_subtotal_local', 0.0) or 0.0)
                codigo_factura = str(factura.get('f_codigo_factura', '') or numero_factura).strip()
            else:
                numero_factura = str(factura.get('numero_factura', '')).strip()
                indice_linea = int(factura.get('indice_linea', factura.get('_indice_linea', 0)) or 0)
                codigo_producto = str(
                    factura.get('codigo_producto_api')
                    or factura.get('codigo_producto')
                    or factura.get('rowid_movto')
                    or factura.get('rowid')
                    or factura.get('nombre_producto', '')
                ).strip()
                nombre_producto = str(factura.get('nombre_producto', '')).strip()
                nit_cliente = str(factura.get('nit_comprador', factura.get('nit_cliente', ''))).strip()
                nombre_cliente = str(factura.get('nombre_comprador', factura.get('nombre_cliente', ''))).strip()
                cantidad_original = float(factura.get('cantidad_original', factura.get('cantidad', 0.0)) or 0.0)
                valor_total = float(factura.get('valor_total', 0.0) or 0.0)
                codigo_factura = str(factura.get('codigo_factura', numero_factura)).strip()

            if not numero_factura or not codigo_producto or not nit_cliente:
                raise ValueError(f"factura_id={numero_factura or 'SIN_NUMERO'} campo=datos_incompletos")
            self._validate_plain_text(nit_cliente, 'nit_cliente', numero_factura)
            self._validate_plain_text(nombre_cliente, 'nombre_cliente', numero_factura)
            self._validate_nit(nit_cliente, numero_factura)

            nit_hash = nit_cliente
            nit_enc = nit_cliente
            nombre_enc = nombre_cliente

            codigo_factura_norm = codigo_factura.lower()
            numero_linea = numero_factura
            total_repeticiones = 1
            repeticion_index = 1
            suma_total_repeticiones = valor_total
            registrable = 1

            if codigo_factura_norm == 'abc123':
                local_cursor.execute('SELECT COUNT(*), COALESCE(SUM(valor_total), 0) FROM facturas WHERE codigo_factura = ?', (codigo_factura,))
                count, suma = local_cursor.fetchone()
                if count >= 5:
                    raise ValueError(f"factura_id={numero_factura} campo=codigo_factura limite_repeticiones")
                total_repeticiones = count + 1
                repeticion_index = count + 1
                suma_total_repeticiones = float(suma or 0) + valor_total
                registrable = 1 if suma_total_repeticiones > 524000 else 0
            else:
                if valor_total < 524000:
                    raise ValueError(f"factura_id={numero_factura} campo=valor_total monto_minimo_no_alcanzado")

            cantidad_kilos = abs(float(
                factura.get('cantidad_kilos', factura.get('f_peso', cantidad_original)) or 0.0
            ))
            raw_payload = json.dumps(factura, ensure_ascii=False)

            engine = getattr(local_conn, 'engine', get_engine(self.db_path))
            if engine == 'mysql':
                local_cursor.execute('''
                    INSERT INTO facturas (
                        numero_linea, numero_factura, indice_linea, codigo_producto, nombre_producto,
                        nit_encrypted, nit_hash, nombre_cliente_encrypted,
                        cantidad_original, valor_total, cantidad_restante, valor_restante,
                        estado, codigo_factura, repeticion_index, total_repeticiones,
                        suma_total_repeticiones, registrable, fecha_factura, cantidad_kilos, raw_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVA', ?, ?, ?, ?, ?, ?, ?, ?)
                    ON DUPLICATE KEY UPDATE
                        cantidad_original = VALUES(cantidad_original),
                        valor_total = VALUES(valor_total),
                        cantidad_restante = VALUES(cantidad_restante),
                        valor_restante = VALUES(valor_restante),
                        codigo_factura = VALUES(codigo_factura),
                        repeticion_index = VALUES(repeticion_index),
                        total_repeticiones = VALUES(total_repeticiones),
                        suma_total_repeticiones = VALUES(suma_total_repeticiones),
                        registrable = VALUES(registrable),
                        cantidad_kilos = VALUES(cantidad_kilos),
                        raw_payload = VALUES(raw_payload)
                ''', (
                    numero_linea, numero_factura, indice_linea, codigo_producto, nombre_producto,
                    nit_enc, nit_hash, nombre_enc,
                    cantidad_original, valor_total, cantidad_original, valor_total,
                    codigo_factura, repeticion_index, total_repeticiones,
                    suma_total_repeticiones, registrable, fecha_factura, cantidad_kilos, raw_payload
                ))
            else:
                local_cursor.execute('''
                    INSERT INTO facturas (
                        numero_linea, numero_factura, indice_linea, codigo_producto, nombre_producto,
                        nit_encrypted, nit_hash, nombre_cliente_encrypted,
                        cantidad_original, valor_total, cantidad_restante, valor_restante,
                        estado, codigo_factura, repeticion_index, total_repeticiones,
                        suma_total_repeticiones, registrable, fecha_factura, cantidad_kilos, raw_payload
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVA', ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(numero_factura, codigo_producto, indice_linea, fecha_factura) DO UPDATE SET
                        cantidad_original = excluded.cantidad_original,
                        valor_total = excluded.valor_total,
                        cantidad_restante = excluded.cantidad_restante,
                        valor_restante = excluded.valor_restante,
                        codigo_factura = excluded.codigo_factura,
                        repeticion_index = excluded.repeticion_index,
                        total_repeticiones = excluded.total_repeticiones,
                        suma_total_repeticiones = excluded.suma_total_repeticiones,
                        registrable = excluded.registrable,
                        cantidad_kilos = excluded.cantidad_kilos,
                        raw_payload = excluded.raw_payload
                ''', (
                    numero_linea, numero_factura, indice_linea, codigo_producto, nombre_producto,
                    nit_enc, nit_hash, nombre_enc,
                    cantidad_original, valor_total, cantidad_original, valor_total,
                    codigo_factura, repeticion_index, total_repeticiones,
                    suma_total_repeticiones, registrable, fecha_factura, cantidad_kilos, raw_payload
                ))

            if codigo_factura_norm == 'abc123':
                local_cursor.execute('''
                    UPDATE facturas
                    SET total_repeticiones = ?,
                        suma_total_repeticiones = ?,
                        registrable = ?
                    WHERE codigo_factura = ?
                ''', (total_repeticiones, suma_total_repeticiones, registrable, codigo_factura))

            self._registrar_auditoria(local_conn, 'factura', 'crear', numero_factura, usuario, {
                'numero_factura': numero_factura,
                'codigo_factura': codigo_factura,
                'codigo_producto': codigo_producto,
                'valor_total': valor_total,
                'registrable': bool(registrable)
            })

            if commit:
                local_conn.commit()
                local_conn.close()
            return True

        except ValueError as e:
            try:
                if commit and conn is None:
                    local_conn.rollback()
                    local_conn.close()
            except Exception:
                pass
            logger.error(f"Error al registrar factura: {e}")
            if not commit:
                raise
            return False
        except Exception as e:
            logger.error(f"Error al registrar factura: {e}")
            import traceback
            traceback.print_exc()
            if commit and conn is None:
                try:
                    local_conn.rollback()
                    local_conn.close()
                except Exception:
                    pass
            return False

    def registrar_factura_rechazada(self, factura: Dict, razon_rechazo: str, usuario: Optional[str] = None,
                                    conn: Optional[Any] = None,
                                    cursor: Optional[Any] = None,
                                    commit: bool = True) -> bool:
        try:
            local_conn = conn or self._get_connection()
            local_cursor = cursor or local_conn.cursor()
            if commit:
                local_cursor.execute('BEGIN')

            prefijo = str(factura.get('f_prefijo', '')).strip()
            nrodocto = factura.get('f_nrodocto', '')
            numero_factura = f"{prefijo}{nrodocto}"
            if not numero_factura:
                numero_factura = str(factura.get('numero_factura', '')).strip()
            numero_linea = numero_factura
            if not numero_factura:
                raise ValueError("factura_id=SIN_NUMERO campo=numero_factura vacio")

            fecha_str = factura.get('f_fecha', '')
            if fecha_str:
                try:
                    fecha_factura = datetime.fromisoformat(str(fecha_str).replace('T00:00:00', '')).date()
                except:
                    fecha_factura = datetime.now().date()
            else:
                fecha_factura = datetime.now().date()

            codigo_producto = str(
                factura.get('f_cod_item')
                or factura.get('codigo_producto')
                or factura.get('f_rowid_movto')
                or factura.get('f_rowid')
                or ''
            ).strip()
            producto = str(factura.get('f_desc_item', factura.get('nombre_producto', ''))).strip()
            nit_cliente = str(factura.get('f_cliente_desp', factura.get('nit_cliente', ''))).strip()
            nombre_cliente = str(factura.get('f_cliente_fact_razon_soc', factura.get('nombre_cliente', ''))).strip()
            cantidad = float(factura.get('f_cant_base', factura.get('cantidad_original', 0.0)) or 0.0)
            valor_total = float(factura.get('f_valor_subtotal_local', factura.get('valor_total', 0.0)) or 0.0)
            tipo_inventario = str(factura.get('f_cod_tipo_inv', factura.get('tipo_inventario', ''))).strip()
            cantidad_kilos = abs(float(factura.get('cantidad_kilos', factura.get('f_peso', cantidad)) or 0.0))

            if not razon_rechazo:
                raise ValueError(f"factura_id={numero_factura} campo=razon_rechazo vacio")

            if nit_cliente:
                try:
                    self._validate_plain_text(nit_cliente, 'nit_cliente', numero_factura)
                    self._validate_nit(nit_cliente, numero_factura)
                except ValueError:
                    nit_cliente = ''
            if nombre_cliente:
                try:
                    self._validate_plain_text(nombre_cliente, 'nombre_cliente', numero_factura)
                except ValueError:
                    nombre_cliente = ''

            nit_hash = nit_cliente if nit_cliente else None
            nit_enc = nit_cliente if nit_cliente else None
            nombre_enc = nombre_cliente if nombre_cliente else None

            local_cursor.execute('''
                INSERT INTO facturas_rechazadas
                (numero_factura, numero_linea, codigo_producto, producto,
                 nit_encrypted, nit_hash, nombre_cliente_encrypted, cantidad, valor_total,
                 tipo_inventario, razon_rechazo, fecha_factura, cantidad_kilos, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (numero_factura, numero_linea, codigo_producto, producto,
                  nit_enc, nit_hash, nombre_enc, cantidad, valor_total,
                  tipo_inventario, razon_rechazo, fecha_factura, cantidad_kilos, json.dumps(factura, ensure_ascii=False)))

            self._registrar_auditoria(local_conn, 'factura_rechazada', 'crear', numero_factura, usuario, {
                'numero_factura': numero_factura,
                'codigo_producto': codigo_producto,
                'razon_rechazo': razon_rechazo
            })

            if commit:
                local_conn.commit()
                local_conn.close()
            return True

        except ValueError as e:
            try:
                if commit and conn is None:
                    local_conn.rollback()
                    local_conn.close()
            except Exception:
                pass
            logger.error(f"Error al registrar factura rechazada: {e}")
            if not commit:
                raise
            return False
        except Exception as e:
            logger.error(f"Error al registrar factura rechazada: {e}")
            if commit and conn is None:
                try:
                    local_conn.rollback()
                    local_conn.close()
                except Exception:
                    pass
            return False

    def registrar_facturas_y_rechazos(self, facturas_validas: List[Dict],
                                      facturas_rechazadas: List[Dict],
                                      usuario: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('BEGIN')
            for factura in facturas_validas:
                try:
                    self.registrar_factura(factura, usuario, conn=conn, cursor=cursor, commit=False)
                except ValueError as e:
                    razon = str(e)
                    self.registrar_factura_rechazada(
                        factura,
                        razon,
                        usuario,
                        conn=conn,
                        cursor=cursor,
                        commit=False
                    )
            for item in facturas_rechazadas:
                razon = item.get('razon_rechazo')
                factura = item.get('factura') or {}
                self.registrar_factura_rechazada(factura, razon, usuario, conn=conn, cursor=cursor, commit=False)
            conn.commit()
            conn.close()
            return True, None
        except ValueError as e:
            conn.rollback()
            conn.close()
            return False, str(e)
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"factura_id=DESCONOCIDO campo=error {e}"

    def _registrar_motivo_no_aplicacion(self, nota: Dict, numero_factura: Optional[str],
                                        motivo: str, usuario: Optional[str] = None, detalle: Optional[str] = None):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO log_motivos_no_aplicacion
                (id_nota, numero_nota, numero_factura, motivo, detalle)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                nota.get('id'),
                nota.get('numero_nota'),
                numero_factura,
                motivo,
                detalle
            ))

            if int(nota.get('es_agente') or 0) == 1:
                cursor.execute('''
                    UPDATE notas_credito
                    SET estado = 'NO_APLICADA'
                    WHERE id = ?
                ''', (nota.get('id'),))

            self._registrar_auditoria(conn, 'nota_credito', 'no_aplicada', nota.get('numero_nota'), usuario, {
                'numero_nota': nota.get('numero_nota'),
                'numero_factura': numero_factura,
                'motivo': motivo
            })
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error al registrar motivo no aplicación: {e}")

    def obtener_notas_pendientes(self, nit_cliente: str, codigo_producto: str) -> List[Dict]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM notas_credito
                WHERE nit_encrypted = ?
                AND codigo_producto = ?
                AND estado = 'PENDIENTE'
                AND saldo_pendiente > 0
                ORDER BY fecha_nota ASC
            ''', (nit_cliente, codigo_producto))

            notas = []
            for row in cursor.fetchall():
                nota = dict(row)
                nota['nit_cliente'] = nota.get('nit_encrypted')
                nota['nombre_cliente'] = nota.get('nombre_cliente_encrypted')
                notas.append(nota)

            conn.close()
            return notas

        except Exception as e:
            logger.error(f"Error al obtener notas pendientes: {e}")
            return []

    def obtener_notas_pendientes_cliente(self, nit_cliente: str) -> List[Dict]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM notas_credito
                WHERE nit_encrypted = ?
                AND estado = 'PENDIENTE'
                AND saldo_pendiente > 0
                ORDER BY fecha_nota ASC
            ''', (nit_cliente,))

            notas = []
            for row in cursor.fetchall():
                nota = dict(row)
                nota['nit_cliente'] = nota.get('nit_encrypted')
                nota['nombre_cliente'] = nota.get('nombre_cliente_encrypted')
                notas.append(nota)

            conn.close()
            return notas

        except Exception as e:
            logger.error(f"Error al obtener notas pendientes por cliente: {e}")
            return []

    def obtener_facturas_rango(self, fecha_desde: str, fecha_hasta: str) -> List[Dict]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT numero_factura, codigo_producto, indice_linea, raw_payload
                FROM facturas
                WHERE fecha_factura >= ?
                  AND fecha_factura <= ?
                ORDER BY fecha_factura ASC, numero_factura ASC, indice_linea ASC
            ''', (fecha_desde, fecha_hasta))

            rows = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.error(f"Error al obtener facturas por rango: {e}")
            return []

    def aplicar_nota_a_factura(self, nota: Dict, factura: Dict, usuario: Optional[str] = None) -> Optional[Dict]:
        try:
            numero_factura = str(factura.get('numero_factura', '')).strip()
            if not numero_factura:
                prefijo = str(factura.get('f_prefijo', '')).strip()
                nrodocto = str(factura.get('f_nrodocto', '')).strip()
                numero_factura = f"{prefijo}{nrodocto}"

            nit_factura = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
            codigo_factura = str(
                factura.get('codigo_producto_api')
                or factura.get('codigo_producto')
                or factura.get('f_cod_item')
                or factura.get('f_rowid_movto')
                or factura.get('f_rowid')
                or ''
            ).strip()

            fecha_factura = factura.get('fecha_factura') or factura.get('f_fecha')
            if isinstance(fecha_factura, str):
                try:
                    fecha_factura = datetime.fromisoformat(str(fecha_factura).replace('T00:00:00', '')).date()
                except:
                    try:
                        fecha_factura = datetime.strptime(fecha_factura, '%Y-%m-%d').date()
                    except:
                        fecha_factura = datetime.now().date()
            elif hasattr(fecha_factura, 'date'):
                fecha_factura = fecha_factura.date() if callable(fecha_factura.date) else fecha_factura
            else:
                fecha_factura = datetime.now().date()

            indice_linea = factura.get('indice_linea', factura.get('_indice_linea'))
            if indice_linea is not None:
                try:
                    indice_linea = int(indice_linea)
                except (TypeError, ValueError):
                    indice_linea = None

            nit_nota = nota.get('nit_cliente') or nota.get('nit_encrypted')
            if nit_nota != nit_factura:
                self._registrar_motivo_no_aplicacion(nota, numero_factura, 'Cliente no coincide', usuario)
                return None

            if nota.get('codigo_producto') != codigo_factura:
                nota_nombre = self._normalizar_producto(nota.get('nombre_producto'))
                factura_nombre = self._normalizar_producto(
                    factura.get('f_desc_item') or factura.get('nombre_producto')
                )
                if nota_nombre != factura_nombre:
                    self._registrar_motivo_no_aplicacion(nota, numero_factura, 'Producto no coincide', usuario)
                    return None

            cantidad_origen = factura.get('cantidad_original')
            if cantidad_origen is None:
                cantidad_origen = factura.get('cantidad')
            if cantidad_origen is None:
                cantidad_origen = factura.get('f_cant_base', 0)
            cantidad_factura = abs(float(cantidad_origen or 0))

            valor_origen = factura.get('valor_total')
            if valor_origen is None:
                valor_origen = factura.get('f_valor_subtotal_local', 0)
            valor_factura = abs(float(valor_origen or 0))

            cantidad_nota = abs(nota['cantidad_pendiente'])
            valor_nota = abs(nota['saldo_pendiente'])
            es_agente = int(nota.get('es_agente') or 0) == 1

            cantidad_aplicar = min(cantidad_nota, cantidad_factura)
            valor_aplicar = min(valor_nota, valor_factura)
            cantidad_kilos_nota = abs(float(nota.get('cantidad_kilos', cantidad_nota) or 0))
            cantidad_aplicada_kilos = cantidad_aplicar
            if cantidad_nota > 0 and cantidad_kilos_nota > 0:
                cantidad_aplicada_kilos = (cantidad_aplicar / cantidad_nota) * cantidad_kilos_nota

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, cantidad_restante, valor_restante
                FROM facturas
                WHERE numero_factura = ?
                  AND codigo_producto = ?
                  AND indice_linea = ?
                  AND fecha_factura = ?
            ''', (numero_factura, codigo_factura, indice_linea or 0, fecha_factura))
            factura_row = cursor.fetchone()
            if not factura_row:
                conn.close()
                self._registrar_motivo_no_aplicacion(nota, numero_factura, 'Factura no encontrada', usuario)
                return None

            factura_id = factura_row['id']
            cantidad_base = factura_row['cantidad_restante']
            valor_base = factura_row['valor_restante']

            cantidad_restante = cantidad_base - cantidad_aplicar
            valor_restante = valor_base - valor_aplicar

            cursor.execute('''
                INSERT INTO aplicaciones_notas
                (id_nota, id_factura, numero_nota, numero_factura, numero_linea, fecha_factura,
                 nit_hash, codigo_producto, cantidad_aplicada, valor_aplicado,
                 cantidad_factura_antes, cantidad_factura_despues, valor_factura_antes, valor_factura_despues)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nota['id'], factura_id, nota['numero_nota'], numero_factura, numero_factura, fecha_factura,
                nit_factura, nota['codigo_producto'], cantidad_aplicar, valor_aplicar,
                cantidad_base, max(0, cantidad_restante), valor_base, max(0, valor_restante)
            ))

            cursor.execute('''
                INSERT INTO notas_aplicadas
                (numero_nota, numero_factura, numero_linea, codigo_producto, nit_cliente,
                 cantidad_aplicada, cantidad_aplicada_kilos, valor_aplicado, payload_nota, payload_factura)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nota['numero_nota'],
                numero_factura,
                numero_factura,
                nota['codigo_producto'],
                nit_factura,
                cantidad_aplicar,
                cantidad_aplicada_kilos,
                valor_aplicar,
                json.dumps(nota, ensure_ascii=False, default=str),
                json.dumps(factura, ensure_ascii=False, default=str)
            ))

            nuevo_saldo = nota['saldo_pendiente'] - valor_aplicar
            nueva_cantidad = nota['cantidad_pendiente'] - cantidad_aplicar

            if nuevo_saldo <= 0.01:
                estado = 'APLICADA'
                fecha_aplicacion_completa = datetime.now()
            else:
                estado = 'PENDIENTE'
                fecha_aplicacion_completa = None

            cursor.execute('''
                UPDATE notas_credito
                SET saldo_pendiente = ?,
                    cantidad_pendiente = ?,
                    estado = ?,
                    fecha_aplicacion_completa = ?
                WHERE id = ?
            ''', (max(0, nuevo_saldo), max(0, nueva_cantidad), estado, fecha_aplicacion_completa, nota['id']))

            try:
                cursor.execute('''
                    UPDATE notas_pendientes
                    SET estado = ?, saldo_pendiente = ?, cantidad_pendiente = ?, cantidad_pendiente_kilos = ?,
                        fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE numero_nota = ? AND codigo_producto = ?
                ''', (
                    'APLICADA' if estado == 'APLICADA' else 'PENDIENTE',
                    max(0, nuevo_saldo),
                    max(0, nueva_cantidad),
                    max(0, cantidad_kilos_nota - cantidad_aplicada_kilos),
                    nota['numero_nota'],
                    nota['codigo_producto']
                ))
            except Exception:
                pass

            if valor_restante <= 0.01 or cantidad_restante <= 0.01:
                cursor.execute('DELETE FROM facturas WHERE id = ?', (factura_id,))
            else:
                cursor.execute('''
                    UPDATE facturas
                    SET cantidad_restante = ?,
                        valor_restante = ?
                    WHERE id = ?
                ''', (max(0, cantidad_restante), max(0, valor_restante), factura_id))

            self._registrar_auditoria(conn, 'aplicacion_nota', 'crear', str(nota['id']), usuario, {
                'numero_nota': nota['numero_nota'],
                'numero_factura': numero_factura,
                'cantidad_aplicada': cantidad_aplicar,
                'valor_aplicado': valor_aplicar,
                'estado_nota': estado
            })

            conn.commit()
            conn.close()

            return {
                'numero_nota': nota['numero_nota'],
                'numero_factura': numero_factura,
                'numero_linea': numero_factura,
                'codigo_producto': codigo_factura,
                'indice_linea': indice_linea or 0,
                'cantidad_aplicada': cantidad_aplicar,
                'valor_aplicado': valor_aplicar,
                'cantidad_restante_factura': max(0, cantidad_restante),
                'valor_restante_factura': max(0, valor_restante),
                'saldo_restante_nota': max(0, nuevo_saldo),
                'estado_nota': estado
            }

        except Exception as e:
            logger.error(f"Error al aplicar nota: {e}")
            import traceback
            traceback.print_exc()
            return None

    def procesar_notas_para_facturas(self, facturas: List[Dict], usuario: Optional[str] = None) -> List[Dict]:
        aplicaciones = []

        for factura in facturas:
            nit_cliente = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
            codigo_producto = str(
                factura.get('codigo_producto_api')
                or factura.get('codigo_producto')
                or factura.get('f_cod_item')
                or factura.get('f_rowid_movto')
                or factura.get('f_rowid')
                or ''
            ).strip()
            nombre_producto = self._normalizar_producto(
                factura.get('f_desc_item') or factura.get('nombre_producto')
            )

            if not nit_cliente or not codigo_producto:
                continue

            notas_pendientes = self.obtener_notas_pendientes(nit_cliente, codigo_producto)
            if not notas_pendientes:
                notas_pendientes = [
                    nota
                    for nota in self.obtener_notas_pendientes_cliente(nit_cliente)
                    if self._normalizar_producto(nota.get('nombre_producto')) == nombre_producto
                ]

            for nota in notas_pendientes:
                aplicacion = self.aplicar_nota_a_factura(nota, factura, usuario)
                if aplicacion:
                    aplicaciones.append(aplicacion)

        logger.info(f"Se realizaron {len(aplicaciones)} aplicaciones de notas crédito")
        return aplicaciones

    def obtener_resumen_notas(self) -> Dict:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*), SUM(saldo_pendiente)
                FROM notas_credito WHERE estado = 'PENDIENTE'
            ''')
            pendientes, saldo_pendiente = cursor.fetchone()

            cursor.execute('SELECT COUNT(*) FROM notas_credito WHERE estado = "APLICADA"')
            aplicadas = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM notas_credito WHERE estado = "NO_APLICADA"')
            no_aplicadas = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*), SUM(valor_aplicado) FROM aplicaciones_notas')
            num_aplicaciones, total_aplicado = cursor.fetchone()

            conn.close()

            return {
                'notas_pendientes': pendientes or 0,
                'saldo_pendiente_total': saldo_pendiente or 0.0,
                'notas_aplicadas': aplicadas or 0,
                'notas_no_aplicadas': no_aplicadas or 0,
                'total_aplicaciones': num_aplicaciones or 0,
                'monto_total_aplicado': total_aplicado or 0.0
            }

        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            return {}

    def obtener_resumen_facturas(self) -> Dict:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM facturas')
            total_validas, valor_total = cursor.fetchone()

            cursor.execute('SELECT COUNT(*) FROM facturas WHERE registrable = 1')
            registrables = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM facturas WHERE registrable = 0')
            no_registrables = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas')
            total_rechazadas = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*), SUM(valor_aplicado) FROM aplicaciones_notas')
            total_aplicaciones, total_aplicado = cursor.fetchone()

            conn.close()

            return {
                'facturas_validas': total_validas or 0,
                'valor_total_facturado': valor_total or 0.0,
                'facturas_registrables': registrables or 0,
                'facturas_no_registrables': no_registrables or 0,
                'facturas_rechazadas': total_rechazadas or 0,
                'aplicaciones_total': total_aplicaciones or 0,
                'total_aplicado': total_aplicado or 0.0
            }

        except Exception as e:
            logger.error(f"Error al obtener resumen facturas: {e}")
            return {}

    def obtener_historial_nota(self, numero_nota: str) -> List[Dict]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM aplicaciones_notas
                WHERE numero_nota = ?
                ORDER BY fecha_aplicacion DESC
            ''', (numero_nota,))

            aplicaciones = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return aplicaciones

        except Exception as e:
            logger.error(f"Error al obtener historial: {e}")
            return []

    def obtener_resumen_rechazos(self, dias: int = 7) -> Dict:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT COUNT(*), SUM(valor_total)
                FROM facturas_rechazadas WHERE fecha_registro >= ?
            ''', (fecha_limite,))
            total_rechazos, valor_total = cursor.fetchone()

            cursor.execute('''
                SELECT razon_rechazo, COUNT(*), SUM(valor_total)
                FROM facturas_rechazadas WHERE fecha_registro >= ?
                GROUP BY razon_rechazo ORDER BY COUNT(*) DESC
            ''', (fecha_limite,))
            por_razon = [
                {'razon': row[0], 'cantidad': row[1], 'valor': row[2]}
                for row in cursor.fetchall()
            ]

            conn.close()

            return {
                'total_rechazos': total_rechazos or 0,
                'valor_total_rechazado': valor_total or 0.0,
                'por_razon': por_razon
            }

        except Exception as e:
            logger.error(f"Error al obtener resumen rechazos: {e}")
            return {}

    # Alias para compatibilidad con código existente
    def registrar_factura_completa(self, factura_transformada: Dict) -> bool:
        """Alias para registrar_factura por compatibilidad"""
        return self.registrar_factura(factura_transformada)

    def actualizar_factura_con_nota(self, numero_factura: str, codigo_producto: str,
                                    numero_nota: str, valor_aplicado: float,
                                    cantidad_aplicada: float) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, cantidad_restante, valor_restante
                FROM facturas
                WHERE numero_factura = ? AND codigo_producto = ?
            ''', (numero_factura, codigo_producto))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            cantidad_restante = float(row['cantidad_restante'] or 0) - abs(cantidad_aplicada)
            valor_restante = float(row['valor_restante'] or 0) - abs(valor_aplicado)

            if valor_restante <= 0.01 or cantidad_restante <= 0.01:
                cursor.execute('DELETE FROM facturas WHERE id = ?', (row['id'],))
            else:
                cursor.execute('''
                    UPDATE facturas
                    SET cantidad_restante = ?,
                        valor_restante = ?
                    WHERE id = ?
                ''', (max(0, cantidad_restante), max(0, valor_restante), row['id']))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error al actualizar factura con nota: {e}")
            return False
