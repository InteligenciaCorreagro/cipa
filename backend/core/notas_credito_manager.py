"""
Módulo de Gestión de Notas Crédito - VERSIÓN REESTRUCTURADA
Maneja la aplicación de notas crédito a facturas con persistencia en SQLite

ESTRUCTURA DE BD:
- facturas: Líneas de facturas válidas con info de notas aplicadas
- facturas_rechazadas: Facturas que no cumplen reglas de negocio
- notas_credito: Notas de crédito que cumplen reglas de negocio
- usuarios: Usuarios del dashboard
"""
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class NotasCreditoManager:
    """Gestiona la aplicación de notas crédito a facturas"""

    def __init__(self, db_path: str = './data/notas_credito.db'):
        """
        Inicializa el gestor de notas crédito

        Args:
            db_path: Ruta de la base de datos SQLite
        """
        self.db_path = db_path
        self._crear_base_datos()
        logger.info(f"NotasCreditoManager inicializado con BD: {db_path}")

    def _crear_base_datos(self):
        """Crea las tablas necesarias en la base de datos si no existen"""
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # =========================================================================
        # PRIMERO: Verificar si necesitamos migrar la tabla facturas existente
        # =========================================================================
        self._migrar_tabla_facturas_si_necesario(cursor)

        # =========================================================================
        # TABLA FACTURAS
        # Guarda cada línea de factura válida con toda la información requerida
        # IMPORTANTE: indice_linea permite guardar múltiples líneas del mismo
        # producto en la misma factura sin que se sobrescriban
        # =========================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Identificación de la línea
                numero_linea TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                indice_linea INTEGER DEFAULT 0,
                producto TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,

                -- Datos del cliente
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,

                -- Valores originales
                cantidad_original REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                valor_total REAL NOT NULL,

                -- Información de nota aplicada
                nota_aplicada INTEGER DEFAULT 0,
                numero_nota_aplicada TEXT,
                descuento_cantidad REAL DEFAULT 0,
                descuento_valor REAL DEFAULT 0,
                cantidad_restante REAL,
                valor_restante REAL,

                -- Metadata
                tipo_inventario TEXT,
                fecha_factura DATE NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_proceso DATE,
                estado TEXT DEFAULT 'PROCESADA',

                UNIQUE(numero_factura, codigo_producto, indice_linea, fecha_proceso)
            )
        ''')

        # Índices para facturas (solo después de asegurar que la tabla tiene el esquema correcto)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_linea ON facturas(numero_linea)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(nit_cliente)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_producto ON facturas(codigo_producto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_nota ON facturas(nota_aplicada)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_indice ON facturas(indice_linea)')

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
                nit_cliente TEXT,
                nombre_cliente TEXT,
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

        # =========================================================================
        # TABLA NOTAS_CREDITO
        # Notas de crédito que cumplen con las reglas de negocio
        # =========================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_nota TEXT NOT NULL,
                fecha_nota DATE NOT NULL,

                -- Cliente
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,

                -- Producto
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT,

                -- Valores originales
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,

                -- Saldos pendientes
                saldo_pendiente REAL NOT NULL,
                cantidad_pendiente REAL NOT NULL,

                -- Estado y tracking
                estado TEXT DEFAULT 'PENDIENTE',
                causal_devolucion TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aplicacion_completa TIMESTAMP NULL,

                UNIQUE(numero_nota, codigo_producto)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas_credito(nit_cliente)')
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
                numero_nota TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                numero_linea TEXT,
                fecha_factura DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                cantidad_aplicada REAL NOT NULL,
                valor_aplicado REAL NOT NULL,
                fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nota) REFERENCES notas_credito(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aplicaciones_nota ON aplicaciones_notas(numero_nota)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_aplicaciones_factura ON aplicaciones_notas(numero_factura)')

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

        conn.commit()
        conn.close()

        logger.info("Base de datos inicializada correctamente con todas las tablas")

    def _migrar_tabla_facturas_si_necesario(self, cursor):
        """
        Migra la tabla facturas para agregar la columna indice_linea y actualizar
        el constraint UNIQUE. Esto es necesario para BD creadas antes de este cambio.

        IMPORTANTE: Esta función se llama ANTES de crear índices para evitar errores.
        """
        try:
            # Verificar si la tabla facturas existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='facturas'")
            tabla_existe = cursor.fetchone() is not None

            if not tabla_existe:
                # La tabla no existe, será creada después con el esquema correcto
                logger.debug("Tabla facturas no existe, se creará con el nuevo esquema")
                return

            # Verificar si la columna indice_linea existe
            cursor.execute("PRAGMA table_info(facturas)")
            columnas = [col[1] for col in cursor.fetchall()]

            if 'indice_linea' not in columnas:
                logger.info("Migrando tabla facturas: agregando columna indice_linea...")

                # SQLite requiere recrear la tabla para cambiar el UNIQUE constraint
                # 1. Renombrar tabla actual
                cursor.execute('ALTER TABLE facturas RENAME TO facturas_old')

                # 2. Crear nueva tabla con el nuevo esquema
                cursor.execute('''
                    CREATE TABLE facturas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        numero_linea TEXT NOT NULL,
                        numero_factura TEXT NOT NULL,
                        indice_linea INTEGER DEFAULT 0,
                        producto TEXT NOT NULL,
                        codigo_producto TEXT NOT NULL,
                        nit_cliente TEXT NOT NULL,
                        nombre_cliente TEXT NOT NULL,
                        cantidad_original REAL NOT NULL,
                        precio_unitario REAL NOT NULL,
                        valor_total REAL NOT NULL,
                        nota_aplicada INTEGER DEFAULT 0,
                        numero_nota_aplicada TEXT,
                        descuento_cantidad REAL DEFAULT 0,
                        descuento_valor REAL DEFAULT 0,
                        cantidad_restante REAL,
                        valor_restante REAL,
                        tipo_inventario TEXT,
                        fecha_factura DATE NOT NULL,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_proceso DATE,
                        estado TEXT DEFAULT 'PROCESADA',
                        UNIQUE(numero_factura, codigo_producto, indice_linea, fecha_proceso)
                    )
                ''')

                # 3. Copiar datos existentes (con indice_linea=0)
                cursor.execute('''
                    INSERT INTO facturas (
                        id, numero_linea, numero_factura, indice_linea, producto, codigo_producto,
                        nit_cliente, nombre_cliente, cantidad_original, precio_unitario,
                        valor_total, nota_aplicada, numero_nota_aplicada, descuento_cantidad,
                        descuento_valor, cantidad_restante, valor_restante, tipo_inventario,
                        fecha_factura, fecha_registro, fecha_proceso, estado
                    )
                    SELECT
                        id, numero_linea, numero_factura, 0, producto, codigo_producto,
                        nit_cliente, nombre_cliente, cantidad_original, precio_unitario,
                        valor_total, nota_aplicada, numero_nota_aplicada, descuento_cantidad,
                        descuento_valor, cantidad_restante, valor_restante, tipo_inventario,
                        fecha_factura, fecha_registro, fecha_proceso, estado
                    FROM facturas_old
                ''')

                # 4. Eliminar tabla antigua
                cursor.execute('DROP TABLE facturas_old')

                logger.info("Migración completada: tabla facturas actualizada con indice_linea")
            else:
                logger.debug("Columna indice_linea ya existe, no se requiere migración")

        except Exception as e:
            logger.error(f"Error en migración de tabla facturas: {e}")
            import traceback
            traceback.print_exc()

    def registrar_nota_credito(self, nota: Dict) -> bool:
        """
        Registra una nueva nota crédito en la base de datos
        FILTRA notas que tienen cantidad pero valor cero

        Args:
            nota: Datos de la nota crédito desde la API

        Returns:
            True si se registró correctamente, False si ya existía o fue filtrada
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Extraer datos de la nota
            numero_nota = f"{nota.get('f_prefijo', '')}{nota.get('f_nrodocto', '')}"
            fecha_nota_str = nota.get('f_fecha', '')

            # Parsear fecha
            fecha_nota = None
            if fecha_nota_str:
                try:
                    fecha_nota = datetime.fromisoformat(str(fecha_nota_str).replace('T00:00:00', '')).date()
                except:
                    fecha_nota = datetime.now().date()
            else:
                fecha_nota = datetime.now().date()

            nit_cliente = str(nota.get('f_cliente_desp', '')).strip()
            nombre_cliente = str(nota.get('f_cliente_fact_razon_soc', '')).strip()
            codigo_producto = str(nota.get('f_cod_item') or nota.get('f_desc_item', '')).strip()
            nombre_producto = str(nota.get('f_desc_item', '')).strip()
            valor_total = float(nota.get('f_valor_subtotal_local', 0.0) or 0.0)
            cantidad = float(nota.get('f_cant_base', 0.0) or 0.0)
            tipo_inventario = str(nota.get('f_cod_tipo_inv') or nota.get('f_tipo_inv') or '').strip().upper()
            causal_devolucion = str(nota.get('f_notas_causal_dev', '') or '').strip() or None

            # FILTRO: Rechazar notas con cantidad pero sin valor
            if cantidad != 0 and valor_total == 0:
                logger.warning(f"Nota crédito {numero_nota} rechazada: cantidad ({cantidad}) sin valor")
                conn.close()
                return False

            # Validación: código de producto no puede estar vacío
            if not codigo_producto:
                logger.error(f"Nota crédito {numero_nota} sin código de producto - Rechazada")
                conn.close()
                return False

            # Verificar si ya existe
            cursor.execute(
                'SELECT id FROM notas_credito WHERE numero_nota = ? AND codigo_producto = ?',
                (numero_nota, codigo_producto)
            )

            if cursor.fetchone():
                logger.info(f"Nota crédito {numero_nota} - Producto {codigo_producto[:30]}... ya existe")
                conn.close()
                return False

            # Insertar nota crédito
            cursor.execute('''
                INSERT INTO notas_credito
                (numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                 codigo_producto, nombre_producto, tipo_inventario, valor_total, cantidad,
                 saldo_pendiente, cantidad_pendiente, causal_devolucion, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
            ''', (numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                  codigo_producto, nombre_producto, tipo_inventario, valor_total, cantidad,
                  valor_total, cantidad, causal_devolucion))

            conn.commit()
            conn.close()

            logger.info(f"Nota crédito registrada: {numero_nota} - Producto: {codigo_producto[:30]}... - "
                       f"Valor: ${valor_total:,.2f} - Cantidad: {cantidad}")

            return True

        except Exception as e:
            logger.error(f"Error al registrar nota crédito: {e}")
            return False

    def registrar_factura(self, factura: Dict) -> bool:
        """
        Registra una línea de factura en la base de datos.

        IMPORTANTE: Cada línea se identifica por (numero_factura, codigo_producto,
        indice_linea, fecha_proceso). Esto permite guardar múltiples líneas del
        mismo producto en la misma factura.

        Acepta factura en formato crudo de API (f_*) o formato transformado.

        Args:
            factura: Factura cruda o transformada

        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Detectar formato de entrada
            es_factura_cruda = any(k in factura for k in ('f_prefijo', 'f_nrodocto', 'f_cod_item'))

            # Parsear fecha
            if es_factura_cruda:
                fecha_raw = factura.get('f_fecha')
            else:
                fecha_raw = factura.get('fecha_factura')

            fecha_factura = None
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

            # Extraer datos según formato
            if es_factura_cruda:
                prefijo = str(factura.get('f_prefijo', '')).strip()
                nrodocto = str(factura.get('f_nrodocto', '')).strip()
                numero_factura = f"{prefijo}{nrodocto}"
                indice_linea = int(factura.get('_indice_linea', factura.get('indice_linea', 0)) or 0)
                codigo_producto = str(factura.get('f_cod_item', '')).strip()
                producto = str(factura.get('f_desc_item', '')).strip()
                nit_cliente = str(factura.get('f_cliente_desp', '')).strip()
                nombre_cliente = str(factura.get('f_cliente_fact_razon_soc', '')).strip()
                cantidad_original = float(factura.get('f_cant_base', 0.0) or 0.0)
                valor_total = float(factura.get('f_valor_subtotal_local', 0.0) or 0.0)
                precio_unitario = (valor_total / cantidad_original) if cantidad_original != 0 else 0.0
                tipo_inventario = str(factura.get('f_cod_tipo_inv') or factura.get('f_tipo_inv') or '').strip()
            else:
                numero_factura = str(factura.get('numero_factura', '')).strip()
                indice_linea = int(factura.get('indice_linea', factura.get('_indice_linea', 0)) or 0)
                codigo_producto = str(factura.get('codigo_producto_api', '')).strip()
                producto = str(factura.get('nombre_producto', '')).strip()
                nit_cliente = str(factura.get('nit_comprador', '')).strip()
                nombre_cliente = str(factura.get('nombre_comprador', '')).strip()
                cantidad_original = float(factura.get('cantidad_original', factura.get('cantidad', 0.0)) or 0.0)
                valor_total = float(factura.get('valor_total', 0.0) or 0.0)
                precio_unitario = float(factura.get('precio_unitario', 0.0) or 0.0)
                tipo_inventario = str(factura.get('descripcion', '')).strip()

            numero_linea = numero_factura
            fecha_proceso = fecha_factura

            cursor.execute('''
                INSERT INTO facturas (
                    numero_linea, numero_factura, indice_linea, producto, codigo_producto,
                    nit_cliente, nombre_cliente, cantidad_original, precio_unitario,
                    valor_total, cantidad_restante, valor_restante, tipo_inventario,
                    fecha_factura, fecha_proceso, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PROCESADA')
                ON CONFLICT(numero_factura, codigo_producto, indice_linea, fecha_proceso) DO UPDATE SET
                    cantidad_original = excluded.cantidad_original,
                    valor_total = excluded.valor_total,
                    precio_unitario = excluded.precio_unitario
            ''', (
                numero_linea, numero_factura, indice_linea, producto, codigo_producto,
                nit_cliente, nombre_cliente, cantidad_original, precio_unitario,
                valor_total, cantidad_original, valor_total, tipo_inventario,
                fecha_factura, fecha_proceso
            ))

            conn.commit()
            conn.close()

            logger.debug(f"Factura registrada: {numero_linea} línea {indice_linea} - {codigo_producto}")
            return True

        except Exception as e:
            logger.error(f"Error al registrar factura: {e}")
            import traceback
            traceback.print_exc()
            return False

    def registrar_factura_rechazada(self, factura: Dict, razon_rechazo: str) -> bool:
        """
        Registra una factura rechazada en la base de datos

        Args:
            factura: Datos de la factura desde la API
            razon_rechazo: Razón por la cual fue rechazada

        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            prefijo = str(factura.get('f_prefijo', '')).strip()
            nrodocto = factura.get('f_nrodocto', '')
            numero_factura = f"{prefijo}{nrodocto}"
            numero_linea = numero_factura

            fecha_str = factura.get('f_fecha', '')
            fecha_factura = None
            if fecha_str:
                try:
                    fecha_factura = datetime.fromisoformat(str(fecha_str).replace('T00:00:00', '')).date()
                except:
                    fecha_factura = datetime.now().date()

            codigo_producto = str(factura.get('f_cod_item', '')).strip()
            producto = str(factura.get('f_desc_item', '')).strip()
            nit_cliente = str(factura.get('f_cliente_desp', '')).strip()
            nombre_cliente = str(factura.get('f_cliente_fact_razon_soc', '')).strip()
            cantidad = float(factura.get('f_cant_base', 0.0) or 0.0)
            valor_total = float(factura.get('f_valor_subtotal_local', 0.0) or 0.0)
            tipo_inventario = str(factura.get('f_cod_tipo_inv', '')).strip()

            cursor.execute('''
                INSERT INTO facturas_rechazadas
                (numero_factura, numero_linea, codigo_producto, producto,
                 nit_cliente, nombre_cliente, cantidad, valor_total,
                 tipo_inventario, razon_rechazo, fecha_factura)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (numero_factura, numero_linea, codigo_producto, producto,
                  nit_cliente, nombre_cliente, cantidad, valor_total,
                  tipo_inventario, razon_rechazo, fecha_factura))

            conn.commit()
            conn.close()

            logger.debug(f"Factura rechazada registrada: {numero_factura} - {razon_rechazo}")
            return True

        except Exception as e:
            logger.error(f"Error al registrar factura rechazada: {e}")
            return False

    def obtener_notas_pendientes(self, nit_cliente: str, codigo_producto: str) -> List[Dict]:
        """
        Obtiene notas crédito pendientes para un cliente y producto

        Args:
            nit_cliente: NIT del cliente
            codigo_producto: Código del producto

        Returns:
            Lista de notas crédito pendientes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM notas_credito
                WHERE nit_cliente = ?
                AND codigo_producto = ?
                AND estado = 'PENDIENTE'
                AND saldo_pendiente > 0
                ORDER BY fecha_nota ASC
            ''', (nit_cliente, codigo_producto))

            notas = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return notas

        except Exception as e:
            logger.error(f"Error al obtener notas pendientes: {e}")
            return []

    def aplicar_nota_a_factura(self, nota: Dict, factura: Dict) -> Optional[Dict]:
        """
        Aplica una nota crédito a una factura si cumple las condiciones:
        - La cantidad de la nota debe ser <= cantidad de la línea
        - El valor de la nota debe ser <= valor de la línea

        CASO ESPECIAL: Si nota tiene cantidad 24 y línea 25, valor línea 100.000
                       pero valor nota 101.000 -> NO SE PUEDE APLICAR

        Args:
            nota: Datos de la nota crédito (desde BD)
            factura: Datos de la factura (transformada)

        Returns:
            Diccionario con información de la aplicación o None si no se pudo aplicar
        """
        try:
            # Permitir factura en formato transformado o crudo (API)
            numero_factura = str(factura.get('numero_factura', '')).strip()
            if not numero_factura:
                prefijo = str(factura.get('f_prefijo', '')).strip()
                nrodocto = str(factura.get('f_nrodocto', '')).strip()
                numero_factura = f"{prefijo}{nrodocto}"

            nit_factura = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
            codigo_factura = str(factura.get('codigo_producto_api') or factura.get('f_cod_item', '')).strip()

            # Parsear fecha de factura
            fecha_factura = factura.get('fecha_factura')
            if not fecha_factura:
                fecha_factura = factura.get('f_fecha')

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

            # Índice de línea (si existe) para actualizar solo la línea exacta
            indice_linea = factura.get('indice_linea', factura.get('_indice_linea'))
            if indice_linea is not None:
                try:
                    indice_linea = int(indice_linea)
                except (TypeError, ValueError):
                    indice_linea = None

            # Validar cliente y producto
            if nota['nit_cliente'] != nit_factura:
                return None

            if nota['codigo_producto'] != codigo_factura:
                return None

            # Obtener valores
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

            # =========================================================================
            # VALIDACIÓN CRÍTICA: El valor de la nota NO puede superar el valor de la línea
            # Esto previene el caso extraño donde nota tiene valor mayor a la factura
            # =========================================================================
            if valor_nota > valor_factura:
                logger.warning(
                    f"Nota {nota['numero_nota']} NO puede aplicarse a factura {numero_factura}: "
                    f"Valor nota (${valor_nota:,.2f}) > Valor factura (${valor_factura:,.2f})"
                )
                return None

            # La cantidad de la nota no puede superar la cantidad de la factura
            if cantidad_nota > cantidad_factura:
                logger.warning(
                    f"Nota {nota['numero_nota']} NO puede aplicarse a factura {numero_factura}: "
                    f"Cantidad nota ({cantidad_nota}) > Cantidad factura ({cantidad_factura})"
                )
                return None

            # Si pasa las validaciones, aplicar la nota
            cantidad_aplicar = cantidad_nota
            valor_aplicar = valor_nota

            # Registrar aplicación
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            numero_linea = numero_factura

            cursor.execute('''
                INSERT INTO aplicaciones_notas
                (id_nota, numero_nota, numero_factura, numero_linea, fecha_factura,
                 nit_cliente, codigo_producto, cantidad_aplicada, valor_aplicado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nota['id'], nota['numero_nota'], numero_factura, numero_linea,
                  fecha_factura, nota['nit_cliente'],
                  nota['codigo_producto'], cantidad_aplicar, valor_aplicar))

            # Actualizar saldos de la nota
            nuevo_saldo = nota['saldo_pendiente'] - valor_aplicar
            nueva_cantidad = nota['cantidad_pendiente'] - cantidad_aplicar

            # Determinar nuevo estado
            if nuevo_saldo <= 0.01:
                estado = 'APLICADA'
                fecha_aplicacion_completa = datetime.now()
            else:
                estado = 'PARCIAL'
                fecha_aplicacion_completa = None

            cursor.execute('''
                UPDATE notas_credito
                SET saldo_pendiente = ?,
                    cantidad_pendiente = ?,
                    estado = ?,
                    fecha_aplicacion_completa = ?
                WHERE id = ?
            ''', (max(0, nuevo_saldo), max(0, nueva_cantidad),
                  estado, fecha_aplicacion_completa, nota['id']))

            # Actualizar la factura con la nota aplicada
            cantidad_restante = cantidad_factura - cantidad_aplicar
            valor_restante = valor_factura - valor_aplicar

            if indice_linea is None:
                cursor.execute('''
                    UPDATE facturas
                    SET nota_aplicada = 1,
                        numero_nota_aplicada = ?,
                        descuento_cantidad = descuento_cantidad + ?,
                        descuento_valor = descuento_valor + ?,
                        cantidad_restante = ?,
                        valor_restante = ?
                    WHERE numero_factura = ? AND codigo_producto = ?
                ''', (nota['numero_nota'], cantidad_aplicar, valor_aplicar,
                      cantidad_restante, valor_restante, numero_factura, codigo_factura))
            else:
                cursor.execute('''
                    UPDATE facturas
                    SET nota_aplicada = 1,
                        numero_nota_aplicada = ?,
                        descuento_cantidad = descuento_cantidad + ?,
                        descuento_valor = descuento_valor + ?,
                        cantidad_restante = ?,
                        valor_restante = ?
                    WHERE numero_factura = ?
                      AND codigo_producto = ?
                      AND indice_linea = ?
                      AND fecha_proceso = ?
                ''', (nota['numero_nota'], cantidad_aplicar, valor_aplicar,
                      cantidad_restante, valor_restante,
                      numero_factura, codigo_factura, indice_linea, fecha_factura))

            conn.commit()
            conn.close()

            logger.info(
                f"Nota {nota['numero_nota']} aplicada a línea {numero_linea}: "
                f"Cantidad: {cantidad_aplicar} | Valor: ${valor_aplicar:,.2f} | "
                f"Cantidad restante en línea: {cantidad_restante} | Estado nota: {estado}"
            )

            return {
                'numero_nota': nota['numero_nota'],
                'numero_factura': numero_factura,
                'numero_linea': numero_linea,
                'cantidad_aplicada': cantidad_aplicar,
                'valor_aplicado': valor_aplicar,
                'cantidad_restante_factura': cantidad_restante,
                'valor_restante_factura': valor_restante,
                'saldo_restante_nota': max(0, nuevo_saldo),
                'estado_nota': estado
            }

        except Exception as e:
            logger.error(f"Error al aplicar nota: {e}")
            import traceback
            traceback.print_exc()
            return None

    def procesar_notas_para_facturas(self, facturas: List[Dict]) -> List[Dict]:
        """
        Procesa la aplicación de notas crédito pendientes a un lote de facturas

        Args:
            facturas: Lista de facturas transformadas o crudas (API)

        Returns:
            Lista de aplicaciones realizadas
        """
        aplicaciones = []

        for factura in facturas:
            nit_cliente = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
            codigo_producto = str(factura.get('codigo_producto_api') or factura.get('f_cod_item', '')).strip()

            if not nit_cliente or not codigo_producto:
                continue

            notas_pendientes = self.obtener_notas_pendientes(nit_cliente, codigo_producto)

            for nota in notas_pendientes:
                aplicacion = self.aplicar_nota_a_factura(nota, factura)

                if aplicacion:
                    aplicaciones.append(aplicacion)

                    if aplicacion['estado_nota'] == 'APLICADA':
                        logger.info(f"Nota {aplicacion['numero_nota']} aplicada completamente")

        logger.info(f"Se realizaron {len(aplicaciones)} aplicaciones de notas crédito")
        return aplicaciones

    def obtener_resumen_notas(self) -> Dict:
        """
        Obtiene un resumen del estado de las notas crédito

        Returns:
            Diccionario con estadísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*), SUM(saldo_pendiente)
                FROM notas_credito WHERE estado = 'PENDIENTE'
            ''')
            pendientes, saldo_pendiente = cursor.fetchone()

            cursor.execute('SELECT COUNT(*) FROM notas_credito WHERE estado = "APLICADA"')
            aplicadas = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*), SUM(valor_aplicado) FROM aplicaciones_notas')
            num_aplicaciones, total_aplicado = cursor.fetchone()

            conn.close()

            return {
                'notas_pendientes': pendientes or 0,
                'saldo_pendiente_total': saldo_pendiente or 0.0,
                'notas_aplicadas': aplicadas or 0,
                'total_aplicaciones': num_aplicaciones or 0,
                'monto_total_aplicado': total_aplicado or 0.0
            }

        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            return {}

    def obtener_resumen_facturas(self) -> Dict:
        """
        Obtiene un resumen del estado de las facturas

        Returns:
            Diccionario con estadísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM facturas')
            total_validas, valor_total = cursor.fetchone()

            cursor.execute('SELECT COUNT(*) FROM facturas WHERE nota_aplicada = 1')
            con_notas = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(descuento_valor) FROM facturas WHERE nota_aplicada = 1')
            total_descontado = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas')
            total_rechazadas = cursor.fetchone()[0]

            conn.close()

            return {
                'facturas_validas': total_validas or 0,
                'valor_total_facturado': valor_total or 0.0,
                'facturas_con_notas': con_notas or 0,
                'total_descontado': total_descontado or 0.0,
                'facturas_rechazadas': total_rechazadas or 0
            }

        except Exception as e:
            logger.error(f"Error al obtener resumen facturas: {e}")
            return {}

    def obtener_historial_nota(self, numero_nota: str) -> List[Dict]:
        """
        Obtiene el historial de aplicaciones de una nota específica
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
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
        """
        Obtiene un resumen de facturas rechazadas en los últimos días
        """
        try:
            conn = sqlite3.connect(self.db_path)
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
        """Actualiza una factura marcándola con nota de crédito aplicada - Compatibilidad"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE facturas
                SET nota_aplicada = 1,
                    numero_nota_aplicada = ?,
                    descuento_valor = descuento_valor + ?,
                    descuento_cantidad = descuento_cantidad + ?
                WHERE numero_factura = ? AND codigo_producto = ?
            ''', (numero_nota, abs(valor_aplicado), abs(cantidad_aplicada),
                  numero_factura, codigo_producto))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error al actualizar factura con nota: {e}")
            return False
