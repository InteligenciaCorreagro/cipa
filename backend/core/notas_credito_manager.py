"""
Módulo de Gestión de Notas Crédito - VERSIÓN OPTIMIZADA v3.1

REGLAS DE NEGOCIO PARA APLICACIÓN DE NOTAS:
───────────────────────────────────────────────────────────────
1. Match por: NIT cliente + código producto
2. La nota se aplica COMPLETA (100%) a UNA sola factura, o NO se aplica
   - Si valor_nota > valor_restante_factura → NO aplica, buscar otra factura
   - Si cantidad_nota > cantidad_restante_factura → NO aplica, buscar otra factura
3. La nota NUNCA se divide entre múltiples facturas
4. La factura SÍ puede quedar con saldo restante (se le resta lo de la nota)
5. Una factura puede recibir múltiples notas sucesivas
   - Cada nota siguiente compara contra el saldo RESTANTE
6. Las notas se procesan en orden de fecha (ASC) - FIFO

EJEMPLO:
  Factura F1: cantidad=100, valor=$1,000,000
  Nota N1:    cantidad=30,  valor=$300,000  → Aplica a F1
  F1 después: cantidad_restante=70, valor_restante=$700,000
  Nota N2:    cantidad=80,  valor=$800,000  → NO aplica a F1 (80 > 70)
  N2 busca otra factura F2 donde quepa...
───────────────────────────────────────────────────────────────

OPTIMIZACIONES v3.1:
- Schema initialization con flag global (1 sola vez)
- Batch INSERT con executemany + transacción única
- Pre-carga de notas pendientes en 1 query
- Match en memoria con tracking de saldos restantes por factura
- Placeholders %s para MySQL (PyMySQL/mysql-connector)
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from db import get_connection
except ImportError:
    from backend.db import get_connection

logger = logging.getLogger(__name__)

# Flag global para evitar re-inicialización del schema
_schema_initialized = False


class NotasCreditoManager:
    """Gestiona la aplicación de notas crédito a facturas"""

    def __init__(self):
        global _schema_initialized
        if not _schema_initialized:
            self._crear_base_datos()
            _schema_initialized = True
            logger.info("NotasCreditoManager: Schema inicializado (primera vez)")
        else:
            logger.debug("NotasCreditoManager: Schema ya inicializado, saltando")

    def _get_conn(self):
        return get_connection()

    # ═════════════════════════════════════════════════════════════
    # SCHEMA INITIALIZATION (ejecuta UNA sola vez)
    # ═════════════════════════════════════════════════════════════

    def _crear_base_datos(self):
        """Crea las tablas necesarias si no existen"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_linea VARCHAR(255) NOT NULL,
                numero_factura VARCHAR(255) NOT NULL,
                indice_linea INT DEFAULT 0,
                producto TEXT NOT NULL,
                codigo_producto VARCHAR(255) NOT NULL,
                nit_cliente VARCHAR(255) NOT NULL,
                nombre_cliente TEXT NOT NULL,
                cantidad_original DECIMAL(18,6) NOT NULL,
                precio_unitario DECIMAL(18,6) NOT NULL,
                valor_total DECIMAL(18,2) NOT NULL,
                nota_aplicada TINYINT DEFAULT 0,
                numero_nota_aplicada VARCHAR(255),
                descuento_cantidad DECIMAL(18,6) DEFAULT 0,
                descuento_valor DECIMAL(18,2) DEFAULT 0,
                cantidad_restante DECIMAL(18,6),
                valor_restante DECIMAL(18,2),
                tipo_inventario VARCHAR(255),
                fecha_factura DATE NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_proceso DATE,
                estado VARCHAR(30) DEFAULT 'PROCESADA',
                nombre_producto TEXT,
                codigo_factura VARCHAR(255),
                nit_encrypted VARCHAR(255),
                nit_hash VARCHAR(255),
                nombre_cliente_encrypted TEXT,
                registrable TINYINT DEFAULT 1,
                total_repeticiones INT DEFAULT 1,
                suma_total_repeticiones DECIMAL(18,2) DEFAULT 0,
                UNIQUE KEY uq_factura_linea (numero_factura, codigo_producto, indice_linea, fecha_proceso)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas_rechazadas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_factura VARCHAR(255) NOT NULL,
                numero_linea VARCHAR(255),
                codigo_producto VARCHAR(255),
                producto TEXT,
                nit_cliente VARCHAR(255),
                nombre_cliente TEXT,
                cantidad DECIMAL(18,6),
                valor_total DECIMAL(18,2),
                tipo_inventario VARCHAR(255),
                razon_rechazo TEXT NOT NULL,
                fecha_factura DATE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nit_encrypted VARCHAR(255),
                nit_hash VARCHAR(255),
                nombre_cliente_encrypted TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_credito (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numero_nota VARCHAR(255) NOT NULL,
                fecha_nota DATE NOT NULL,
                nit_cliente VARCHAR(255) NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto VARCHAR(255) NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario VARCHAR(255),
                valor_total DECIMAL(18,2) NOT NULL,
                cantidad DECIMAL(18,6) NOT NULL,
                saldo_pendiente DECIMAL(18,2) NOT NULL,
                cantidad_pendiente DECIMAL(18,6) NOT NULL,
                estado VARCHAR(20) DEFAULT 'PENDIENTE',
                causal_devolucion TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aplicacion_completa TIMESTAMP NULL,
                nit_encrypted VARCHAR(255),
                nit_hash VARCHAR(255),
                nombre_cliente_encrypted TEXT,
                UNIQUE KEY uq_nota_producto (numero_nota, codigo_producto)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aplicaciones_notas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                id_nota INT NOT NULL,
                numero_nota VARCHAR(255) NOT NULL,
                numero_factura VARCHAR(255) NOT NULL,
                numero_linea VARCHAR(255),
                fecha_factura DATE NOT NULL,
                nit_cliente VARCHAR(255) NOT NULL,
                codigo_producto VARCHAR(255) NOT NULL,
                cantidad_aplicada DECIMAL(18,6) NOT NULL,
                valor_aplicado DECIMAL(18,2) NOT NULL,
                fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nota) REFERENCES notas_credito(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')

        # Índices
        indices = [
            ('idx_f_numero', 'facturas', 'numero_factura'),
            ('idx_f_linea', 'facturas', 'numero_linea'),
            ('idx_f_cliente', 'facturas', 'nit_cliente'),
            ('idx_f_producto', 'facturas', 'codigo_producto'),
            ('idx_f_nota', 'facturas', 'nota_aplicada'),
            ('idx_f_fecha', 'facturas', 'fecha_factura'),
            ('idx_f_indice', 'facturas', 'indice_linea'),
            ('idx_f_cli_prod', 'facturas', 'nit_cliente, codigo_producto'),
            ('idx_r_fecha', 'facturas_rechazadas', 'fecha_factura'),
            ('idx_n_cliente', 'notas_credito', 'nit_cliente'),
            ('idx_n_producto', 'notas_credito', 'codigo_producto'),
            ('idx_n_estado', 'notas_credito', 'estado'),
            ('idx_n_cli_prod_est', 'notas_credito', 'nit_cliente, codigo_producto, estado'),
            ('idx_a_nota', 'aplicaciones_notas', 'numero_nota'),
            ('idx_a_factura', 'aplicaciones_notas', 'numero_factura'),
        ]
        for name, table, cols in indices:
            try:
                cursor.execute(f"CREATE INDEX {name} ON {table}({cols})")
            except Exception:
                pass

        self._sync_nullable_columns(cursor)
        conn.commit()
        conn.close()
        logger.info("BD inicializada correctamente")

    def _sync_nullable_columns(self, cursor):
        """Sincroniza columnas redundantes SOLO donde hay NULLs."""
        sync_queries = [
            "UPDATE facturas SET producto = COALESCE(producto, nombre_producto) WHERE producto IS NULL AND nombre_producto IS NOT NULL",
            "UPDATE facturas SET nombre_producto = COALESCE(nombre_producto, producto) WHERE nombre_producto IS NULL AND producto IS NOT NULL",
            "UPDATE facturas SET codigo_producto = COALESCE(codigo_producto, codigo_factura) WHERE codigo_producto IS NULL AND codigo_factura IS NOT NULL",
            "UPDATE facturas SET codigo_factura = COALESCE(codigo_factura, codigo_producto) WHERE codigo_factura IS NULL AND codigo_producto IS NOT NULL",
            "UPDATE facturas SET nit_encrypted = COALESCE(nit_encrypted, nit_cliente) WHERE nit_encrypted IS NULL AND nit_cliente IS NOT NULL",
            "UPDATE facturas SET nit_hash = COALESCE(nit_hash, nit_cliente) WHERE nit_hash IS NULL AND nit_cliente IS NOT NULL",
            "UPDATE facturas SET nombre_cliente_encrypted = COALESCE(nombre_cliente_encrypted, nombre_cliente) WHERE nombre_cliente_encrypted IS NULL AND nombre_cliente IS NOT NULL",
            "UPDATE facturas SET numero_linea = COALESCE(numero_linea, numero_factura) WHERE numero_linea IS NULL",
            "UPDATE facturas SET cantidad_restante = COALESCE(cantidad_restante, cantidad_original) WHERE cantidad_restante IS NULL",
            "UPDATE facturas SET valor_restante = COALESCE(valor_restante, valor_total) WHERE valor_restante IS NULL",
            "UPDATE facturas SET fecha_proceso = COALESCE(fecha_proceso, fecha_factura) WHERE fecha_proceso IS NULL",
            "UPDATE notas_credito SET nit_encrypted = COALESCE(nit_encrypted, nit_cliente) WHERE nit_encrypted IS NULL AND nit_cliente IS NOT NULL",
            "UPDATE notas_credito SET nit_hash = COALESCE(nit_hash, nit_cliente) WHERE nit_hash IS NULL AND nit_cliente IS NOT NULL",
            "UPDATE notas_credito SET nombre_cliente_encrypted = COALESCE(nombre_cliente_encrypted, nombre_cliente) WHERE nombre_cliente_encrypted IS NULL AND nombre_cliente IS NOT NULL",
            "UPDATE notas_credito SET saldo_pendiente = COALESCE(saldo_pendiente, valor_total) WHERE saldo_pendiente IS NULL",
            "UPDATE notas_credito SET cantidad_pendiente = COALESCE(cantidad_pendiente, cantidad) WHERE cantidad_pendiente IS NULL",
            "UPDATE facturas_rechazadas SET nit_encrypted = COALESCE(nit_encrypted, nit_cliente) WHERE nit_encrypted IS NULL AND nit_cliente IS NOT NULL",
            "UPDATE facturas_rechazadas SET nit_hash = COALESCE(nit_hash, nit_cliente) WHERE nit_hash IS NULL AND nit_cliente IS NOT NULL",
            "UPDATE facturas_rechazadas SET nombre_cliente_encrypted = COALESCE(nombre_cliente_encrypted, nombre_cliente) WHERE nombre_cliente_encrypted IS NULL AND nombre_cliente IS NOT NULL",
        ]
        for query in sync_queries:
            try:
                cursor.execute(query)
            except Exception as e:
                logger.debug(f"Sync column skip: {e}")

    # ═════════════════════════════════════════════════════════════
    # BATCH OPERATIONS
    # ═════════════════════════════════════════════════════════════

    def registrar_facturas_batch(self, facturas: List[Dict]) -> int:
        """Registra múltiples facturas en UNA transacción."""
        if not facturas:
            return 0

        conn = self._get_conn()
        cursor = conn.cursor()
        registradas = 0

        try:
            rows = []
            for factura in facturas:
                row = self._preparar_factura_para_insert(factura)
                if row:
                    rows.append(row)

            if rows:
                cursor.executemany('''
                    INSERT INTO facturas (
                        numero_linea, numero_factura, indice_linea, producto, nombre_producto,
                        codigo_producto, codigo_factura, nit_cliente, nit_encrypted, nit_hash,
                        nombre_cliente, nombre_cliente_encrypted, cantidad_original, precio_unitario,
                        valor_total, cantidad_restante, valor_restante, tipo_inventario,
                        fecha_factura, fecha_proceso, estado, registrable, total_repeticiones,
                        suma_total_repeticiones
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'PROCESADA', %s, %s, %s
                    )
                    ON DUPLICATE KEY UPDATE
                        cantidad_original = VALUES(cantidad_original),
                        valor_total = VALUES(valor_total),
                        precio_unitario = VALUES(precio_unitario),
                        cantidad_restante = VALUES(cantidad_restante),
                        valor_restante = VALUES(valor_restante),
                        fecha_proceso = VALUES(fecha_proceso),
                        nombre_producto = VALUES(nombre_producto),
                        codigo_factura = VALUES(codigo_factura)
                ''', rows)
                registradas = len(rows)

            conn.commit()
            logger.info(f"Batch: {registradas} facturas registradas en 1 transacción")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error en batch facturas: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

        return registradas

    def _preparar_factura_para_insert(self, factura: Dict) -> Optional[tuple]:
        """Prepara una factura como tupla para executemany"""
        try:
            es_cruda = any(k in factura for k in ('f_prefijo', 'f_nrodocto', 'f_cod_item'))

            if es_cruda:
                fecha_raw = factura.get('f_fecha')
            else:
                fecha_raw = factura.get('fecha_factura')

            fecha_factura = self._parsear_fecha(fecha_raw)

            if es_cruda:
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

            return (
                numero_linea, numero_factura, indice_linea, producto, producto,
                codigo_producto, codigo_producto, nit_cliente, nit_cliente, nit_cliente,
                nombre_cliente, nombre_cliente, cantidad_original, precio_unitario,
                valor_total, cantidad_original, valor_total, tipo_inventario,
                fecha_factura, fecha_proceso, 1, 1, valor_total
            )
        except Exception as e:
            logger.error(f"Error preparando factura: {e}")
            return None

    def registrar_rechazadas_batch(self, rechazadas: List[Dict]) -> int:
        """Registra múltiples facturas rechazadas en UNA transacción."""
        if not rechazadas:
            return 0

        conn = self._get_conn()
        cursor = conn.cursor()
        registradas = 0

        try:
            rows = []
            for item in rechazadas:
                factura = item['factura']
                razon = item['razon_rechazo']

                prefijo = str(factura.get('f_prefijo', '')).strip()
                nrodocto = factura.get('f_nrodocto', '')
                numero_factura = f"{prefijo}{nrodocto}"

                fecha_factura = self._parsear_fecha(factura.get('f_fecha', ''))
                codigo_producto = str(factura.get('f_cod_item', '')).strip()
                producto = str(factura.get('f_desc_item', '')).strip()
                nit_cliente = str(factura.get('f_cliente_desp', '')).strip()
                nombre_cliente = str(factura.get('f_cliente_fact_razon_soc', '')).strip()
                cantidad = float(factura.get('f_cant_base', 0.0) or 0.0)
                valor_total = float(factura.get('f_valor_subtotal_local', 0.0) or 0.0)
                tipo_inventario = str(factura.get('f_cod_tipo_inv', '')).strip()

                rows.append((
                    numero_factura, numero_factura, codigo_producto, producto,
                    nit_cliente, nombre_cliente, cantidad, valor_total,
                    tipo_inventario, nit_cliente, nit_cliente, nombre_cliente,
                    razon, fecha_factura
                ))

            if rows:
                cursor.executemany('''
                    INSERT INTO facturas_rechazadas
                    (numero_factura, numero_linea, codigo_producto, producto,
                     nit_cliente, nombre_cliente, cantidad, valor_total,
                     tipo_inventario, nit_encrypted, nit_hash, nombre_cliente_encrypted,
                     razon_rechazo, fecha_factura)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', rows)
                registradas = len(rows)

            conn.commit()
            logger.info(f"Batch: {registradas} rechazadas registradas")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error batch rechazadas: {e}")
        finally:
            conn.close()

        return registradas

    def registrar_notas_batch(self, notas: List[Dict]) -> Tuple[int, int]:
        """Registra múltiples notas crédito en UNA transacción."""
        if not notas:
            return 0, 0

        conn = self._get_conn()
        cursor = conn.cursor()
        nuevas = 0
        filtradas = 0

        try:
            # Pre-cargar notas existentes para evitar N SELECTs individuales
            numeros_nota_check = list(set(
                f"{n.get('f_prefijo', '')}{n.get('f_nrodocto', '')}" for n in notas
            ))
            existentes = set()

            if numeros_nota_check:
                placeholders = ','.join(['%s'] * len(numeros_nota_check))
                cursor.execute(
                    f'SELECT numero_nota, codigo_producto FROM notas_credito WHERE numero_nota IN ({placeholders})',
                    numeros_nota_check
                )
                for row in cursor.fetchall():
                    if isinstance(row, dict):
                        existentes.add((row['numero_nota'], row['codigo_producto']))
                    else:
                        existentes.add((row[0], row[1]))

            rows_to_insert = []
            for nota in notas:
                numero_nota = f"{nota.get('f_prefijo', '')}{nota.get('f_nrodocto', '')}"
                fecha_nota = self._parsear_fecha(nota.get('f_fecha', ''))
                nit_cliente = str(nota.get('f_cliente_desp', '')).strip()
                nombre_cliente = str(nota.get('f_cliente_fact_razon_soc', '')).strip()
                codigo_producto = str(nota.get('f_cod_item') or nota.get('f_desc_item', '')).strip()
                nombre_producto = str(nota.get('f_desc_item', '')).strip()
                valor_total = float(nota.get('f_valor_subtotal_local', 0.0) or 0.0)
                cantidad = float(nota.get('f_cant_base', 0.0) or 0.0)
                tipo_inventario = str(nota.get('f_cod_tipo_inv') or nota.get('f_tipo_inv') or '').strip().upper()
                causal = str(nota.get('f_notas_causal_dev', '') or '').strip() or None

                if cantidad != 0 and valor_total == 0:
                    filtradas += 1
                    continue
                if not codigo_producto:
                    continue
                if (numero_nota, codigo_producto) in existentes:
                    continue

                rows_to_insert.append((
                    numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                    codigo_producto, nombre_producto, tipo_inventario,
                    nit_cliente, nit_cliente, nombre_cliente,
                    valor_total, cantidad, valor_total, cantidad, causal
                ))

            if rows_to_insert:
                cursor.executemany('''
                    INSERT INTO notas_credito
                    (numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                     codigo_producto, nombre_producto, tipo_inventario,
                     nit_encrypted, nit_hash, nombre_cliente_encrypted,
                     valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                     causal_devolucion, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDIENTE')
                ''', rows_to_insert)
                nuevas = len(rows_to_insert)

            conn.commit()
            logger.info(f"Batch: {nuevas} notas nuevas, {filtradas} filtradas")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error batch notas: {e}")
        finally:
            conn.close()

        return nuevas, filtradas

    # ═════════════════════════════════════════════════════════════
    # APLICACIÓN DE NOTAS CRÉDITO
    # ═════════════════════════════════════════════════════════════

    def procesar_notas_para_facturas_optimizado(self, facturas: List[Dict]) -> List[Dict]:
        """
        Aplica notas crédito a facturas con tracking de saldos restantes.

        FLUJO:
        1. Extraer pares únicos (nit, producto) de las facturas
        2. Cargar TODAS las notas pendientes en 1 query
        3. Para cada nota pendiente:
           a. Buscar facturas del mismo (nit, producto)
           b. Intentar aplicar COMPLETA a la primera factura donde quepa
           c. Si no cabe (valor o cantidad) → siguiente factura
           d. Si cabe → aplicar, actualizar saldo restante en MEMORIA
        4. Commit de todas las operaciones al final
        """
        if not facturas:
            return []

        # ── Paso 1: Extraer pares únicos (nit, producto) ──
        pares_unicos = set()
        for factura in facturas:
            nit = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
            cod = str(factura.get('codigo_producto_api') or factura.get('f_cod_item', '')).strip()
            if nit and cod:
                pares_unicos.add((nit, cod))

        if not pares_unicos:
            logger.info("No hay pares cliente-producto para buscar notas")
            return []

        # ── Paso 2: Cargar TODAS las notas pendientes (1 query) ──
        conn = self._get_conn()
        cursor = conn.cursor()

        nits_unicos = list(set(p[0] for p in pares_unicos))
        placeholders = ','.join(['%s'] * len(nits_unicos))

        cursor.execute(f'''
            SELECT * FROM notas_credito
            WHERE nit_cliente IN ({placeholders})
            AND estado IN ('PENDIENTE', 'PARCIAL')
            AND saldo_pendiente > 0
            ORDER BY fecha_nota ASC
        ''', nits_unicos)

        todas_notas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not todas_notas:
            logger.info("No hay notas pendientes para los clientes de estas facturas")
            return []

        # Organizar notas por (nit, producto)
        notas_por_par = defaultdict(list)
        for nota in todas_notas:
            key = (nota['nit_cliente'], nota['codigo_producto'])
            if key in pares_unicos:
                notas_por_par[key].append(nota)

        if not notas_por_par:
            logger.info("Ninguna nota coincide con los productos de las facturas")
            return []

        logger.info(f"Notas pendientes: {len(todas_notas)} para {len(notas_por_par)} pares cliente-producto")

        # ── Paso 3: Construir mapa de facturas con saldos en memoria ──
        # CLAVE: Cada factura tiene cantidad_restante y valor_restante
        # que se van reduciendo a medida que se aplican notas
        facturas_por_par = defaultdict(list)
        for i, factura in enumerate(facturas):
            nit = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
            cod = str(factura.get('codigo_producto_api') or factura.get('f_cod_item', '')).strip()
            if not nit or not cod:
                continue

            cantidad_original = abs(float(
                factura.get('cantidad_original') or factura.get('cantidad')
                or factura.get('f_cant_base', 0) or 0
            ))
            valor_total = abs(float(
                factura.get('valor_total') or factura.get('f_valor_subtotal_local', 0) or 0
            ))

            prefijo = str(factura.get('f_prefijo', '')).strip()
            nrodocto = str(factura.get('f_nrodocto', '')).strip()
            numero_factura = str(factura.get('numero_factura', '')).strip()
            if not numero_factura:
                numero_factura = f"{prefijo}{nrodocto}"

            fecha_factura = self._parsear_fecha(factura.get('fecha_factura') or factura.get('f_fecha'))

            indice_linea = factura.get('indice_linea', factura.get('_indice_linea'))
            if indice_linea is not None:
                try:
                    indice_linea = int(indice_linea)
                except (TypeError, ValueError):
                    indice_linea = None

            facturas_por_par[(nit, cod)].append({
                '_idx': i,
                'numero_factura': numero_factura,
                'codigo_producto': cod,
                'nit_cliente': nit,
                'fecha_factura': fecha_factura,
                'indice_linea': indice_linea,
                # ── Saldos en memoria (se reducen con cada nota) ──
                'cantidad_restante': cantidad_original,
                'valor_restante': valor_total,
                # Acumuladores
                'total_descuento_cantidad': 0.0,
                'total_descuento_valor': 0.0,
                'notas_aplicadas': [],
            })

        # ── Paso 4: Para cada nota, buscar factura donde quepa COMPLETA ──
        aplicaciones = []
        conn_apply = self._get_conn()
        cursor_apply = conn_apply.cursor()

        try:
            for key, notas_disponibles in notas_por_par.items():
                facturas_candidatas = facturas_por_par.get(key, [])
                if not facturas_candidatas:
                    continue

                for nota in notas_disponibles:
                    if nota['saldo_pendiente'] <= 0 or nota['cantidad_pendiente'] <= 0:
                        continue

                    cantidad_nota = abs(float(nota['cantidad_pendiente']))
                    valor_nota = abs(float(nota['saldo_pendiente']))
                    nota_aplicada = False

                    for fmem in facturas_candidatas:
                        cant_rest = fmem['cantidad_restante']
                        val_rest = fmem['valor_restante']

                        # La nota debe caber COMPLETA en esta factura
                        if valor_nota > val_rest:
                            continue
                        if cantidad_nota > cant_rest:
                            continue

                        # ═══ APLICAR NOTA COMPLETA ═══

                        # INSERT aplicación
                        cursor_apply.execute('''
                            INSERT INTO aplicaciones_notas
                            (id_nota, numero_nota, numero_factura, numero_linea,
                             fecha_factura, nit_cliente, codigo_producto,
                             cantidad_aplicada, valor_aplicado)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            nota['id'], nota['numero_nota'],
                            fmem['numero_factura'], fmem['numero_factura'],
                            fmem['fecha_factura'], nota['nit_cliente'],
                            nota['codigo_producto'], cantidad_nota, valor_nota
                        ))

                        # UPDATE nota → APLICADA (100%)
                        cursor_apply.execute('''
                            UPDATE notas_credito
                            SET saldo_pendiente = 0, cantidad_pendiente = 0,
                                estado = 'APLICADA', fecha_aplicacion_completa = %s
                            WHERE id = %s
                        ''', (datetime.now().isoformat(), nota['id']))

                        # Nuevos saldos de la factura
                        nueva_cant = cant_rest - cantidad_nota
                        nuevo_val = val_rest - valor_nota

                        # UPDATE factura en BD
                        if fmem['indice_linea'] is not None:
                            cursor_apply.execute('''
                                UPDATE facturas
                                SET nota_aplicada = 1, numero_nota_aplicada = %s,
                                    descuento_cantidad = descuento_cantidad + %s,
                                    descuento_valor = descuento_valor + %s,
                                    cantidad_restante = %s, valor_restante = %s
                                WHERE numero_factura = %s AND codigo_producto = %s
                                  AND indice_linea = %s AND fecha_proceso = %s
                            ''', (
                                nota['numero_nota'], cantidad_nota, valor_nota,
                                nueva_cant, nuevo_val,
                                fmem['numero_factura'], fmem['codigo_producto'],
                                fmem['indice_linea'], fmem['fecha_factura']
                            ))
                        else:
                            cursor_apply.execute('''
                                UPDATE facturas
                                SET nota_aplicada = 1, numero_nota_aplicada = %s,
                                    descuento_cantidad = descuento_cantidad + %s,
                                    descuento_valor = descuento_valor + %s,
                                    cantidad_restante = %s, valor_restante = %s
                                WHERE numero_factura = %s AND codigo_producto = %s
                            ''', (
                                nota['numero_nota'], cantidad_nota, valor_nota,
                                nueva_cant, nuevo_val,
                                fmem['numero_factura'], fmem['codigo_producto']
                            ))

                        # ══ ACTUALIZAR SALDOS EN MEMORIA ══
                        fmem['cantidad_restante'] = nueva_cant
                        fmem['valor_restante'] = nuevo_val
                        fmem['total_descuento_cantidad'] += cantidad_nota
                        fmem['total_descuento_valor'] += valor_nota
                        fmem['notas_aplicadas'].append(nota['numero_nota'])

                        # Nota consumida
                        nota['saldo_pendiente'] = 0
                        nota['cantidad_pendiente'] = 0

                        aplicaciones.append({
                            'numero_nota': nota['numero_nota'],
                            'numero_factura': fmem['numero_factura'],
                            'numero_linea': fmem['numero_factura'],
                            'codigo_producto': nota['codigo_producto'],
                            'cantidad_aplicada': cantidad_nota,
                            'valor_aplicado': valor_nota,
                            'cantidad_restante_factura': nueva_cant,
                            'valor_restante_factura': nuevo_val,
                            'saldo_restante_nota': 0,
                            'estado_nota': 'APLICADA'
                        })

                        logger.info(
                            f"Nota {nota['numero_nota']} aplicada COMPLETA a "
                            f"{fmem['numero_factura']}: "
                            f"Cant={cantidad_nota} Val=${valor_nota:,.2f} | "
                            f"Factura restante: Cant={nueva_cant} Val=${nuevo_val:,.2f}"
                        )

                        nota_aplicada = True
                        break  # Nota aplicada, siguiente nota

                    if not nota_aplicada:
                        logger.debug(
                            f"Nota {nota['numero_nota']} "
                            f"(Cant={cantidad_nota}, Val=${valor_nota:,.2f}) "
                            f"no cabe en ninguna factura del par {key}"
                        )

            conn_apply.commit()

        except Exception as e:
            conn_apply.rollback()
            logger.error(f"Error aplicando notas: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn_apply.close()

        logger.info(f"Total aplicaciones realizadas: {len(aplicaciones)}")

        # ── Paso 5: Actualizar facturas originales para el Excel ──
        for key, facturas_mem in facturas_por_par.items():
            for fmem in facturas_mem:
                if fmem['total_descuento_valor'] > 0:
                    idx = fmem['_idx']
                    facturas[idx]['descuento_valor'] = fmem['total_descuento_valor']
                    facturas[idx]['descuento_cantidad'] = fmem['total_descuento_cantidad']
                    facturas[idx]['nota_aplicada'] = ','.join(fmem['notas_aplicadas'])

        return aplicaciones

    # Alias de compatibilidad
    def procesar_notas_para_facturas(self, facturas: List[Dict]) -> List[Dict]:
        return self.procesar_notas_para_facturas_optimizado(facturas)

    def aplicar_nota_a_factura(self, nota: Dict, factura: Dict, cursor=None) -> Optional[Dict]:
        """Compatibilidad: aplica nota individual (debe caber completa)."""
        nit_factura = str(factura.get('nit_comprador') or factura.get('f_cliente_desp', '')).strip()
        codigo_factura = str(factura.get('codigo_producto_api') or factura.get('f_cod_item', '')).strip()

        if nota['nit_cliente'] != nit_factura:
            return None
        if nota['codigo_producto'] != codigo_factura:
            return None

        cantidad_factura = abs(float(
            factura.get('cantidad_original') or factura.get('cantidad') or factura.get('f_cant_base', 0) or 0
        ))
        valor_factura = abs(float(
            factura.get('valor_total') or factura.get('f_valor_subtotal_local', 0) or 0
        ))
        cantidad_nota = abs(float(nota['cantidad_pendiente']))
        valor_nota = abs(float(nota['saldo_pendiente']))

        if valor_nota > valor_factura:
            return None
        if cantidad_nota > cantidad_factura:
            return None

        conn = None
        if cursor is None:
            conn = self._get_conn()
            cursor = conn.cursor()

        try:
            numero_factura = str(factura.get('numero_factura', '')).strip()
            if not numero_factura:
                numero_factura = f"{str(factura.get('f_prefijo', '')).strip()}{str(factura.get('f_nrodocto', '')).strip()}"

            fecha_factura = self._parsear_fecha(factura.get('fecha_factura') or factura.get('f_fecha'))
            indice_linea = factura.get('indice_linea', factura.get('_indice_linea'))
            if indice_linea is not None:
                try:
                    indice_linea = int(indice_linea)
                except (TypeError, ValueError):
                    indice_linea = None

            cursor.execute('''
                INSERT INTO aplicaciones_notas
                (id_nota, numero_nota, numero_factura, numero_linea, fecha_factura,
                 nit_cliente, codigo_producto, cantidad_aplicada, valor_aplicado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (nota['id'], nota['numero_nota'], numero_factura, numero_factura,
                  fecha_factura, nota['nit_cliente'], nota['codigo_producto'],
                  cantidad_nota, valor_nota))

            cursor.execute('''
                UPDATE notas_credito
                SET saldo_pendiente = 0, cantidad_pendiente = 0,
                    estado = 'APLICADA', fecha_aplicacion_completa = %s
                WHERE id = %s
            ''', (datetime.now().isoformat(), nota['id']))

            nueva_cant = cantidad_factura - cantidad_nota
            nuevo_val = valor_factura - valor_nota

            if indice_linea is not None:
                cursor.execute('''
                    UPDATE facturas
                    SET nota_aplicada = 1, numero_nota_aplicada = %s,
                        descuento_cantidad = descuento_cantidad + %s,
                        descuento_valor = descuento_valor + %s,
                        cantidad_restante = %s, valor_restante = %s
                    WHERE numero_factura = %s AND codigo_producto = %s
                      AND indice_linea = %s AND fecha_proceso = %s
                ''', (nota['numero_nota'], cantidad_nota, valor_nota,
                      nueva_cant, nuevo_val,
                      numero_factura, codigo_factura, indice_linea, fecha_factura))
            else:
                cursor.execute('''
                    UPDATE facturas
                    SET nota_aplicada = 1, numero_nota_aplicada = %s,
                        descuento_cantidad = descuento_cantidad + %s,
                        descuento_valor = descuento_valor + %s,
                        cantidad_restante = %s, valor_restante = %s
                    WHERE numero_factura = %s AND codigo_producto = %s
                ''', (nota['numero_nota'], cantidad_nota, valor_nota,
                      nueva_cant, nuevo_val, numero_factura, codigo_factura))

            if conn is not None:
                conn.commit()

            return {
                'numero_nota': nota['numero_nota'],
                'numero_factura': numero_factura,
                'codigo_producto': nota['codigo_producto'],
                'cantidad_aplicada': cantidad_nota,
                'valor_aplicado': valor_nota,
                'cantidad_restante_factura': nueva_cant,
                'valor_restante_factura': nuevo_val,
                'saldo_restante_nota': 0,
                'estado_nota': 'APLICADA'
            }
        except Exception as e:
            if conn is not None:
                conn.rollback()
            logger.error(f"Error aplicando nota individual: {e}")
            return None
        finally:
            if conn is not None:
                conn.close()

    def registrar_factura_completa(self, factura_transformada: Dict) -> bool:
        return self.registrar_factura(factura_transformada)

    # ═════════════════════════════════════════════════════════════
    # UTILIDADES
    # ═════════════════════════════════════════════════════════════

    def _parsear_fecha(self, fecha_raw) -> Optional[str]:
        if not fecha_raw:
            return datetime.now().strftime('%Y-%m-%d')
        if isinstance(fecha_raw, str):
            try:
                return datetime.fromisoformat(str(fecha_raw).replace('T00:00:00', '')).strftime('%Y-%m-%d')
            except Exception:
                try:
                    return datetime.strptime(fecha_raw, '%Y-%m-%d').strftime('%Y-%m-%d')
                except Exception:
                    return datetime.now().strftime('%Y-%m-%d')
        elif hasattr(fecha_raw, 'strftime'):
            return fecha_raw.strftime('%Y-%m-%d')
        return datetime.now().strftime('%Y-%m-%d')

    # ═════════════════════════════════════════════════════════════
    # CONSULTAS
    # ═════════════════════════════════════════════════════════════

    def obtener_notas_pendientes(self, nit_cliente: str, codigo_producto: str) -> List[Dict]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM notas_credito
                WHERE nit_cliente = %s AND codigo_producto = %s
                AND estado IN ('PENDIENTE', 'PARCIAL') AND saldo_pendiente > 0
                ORDER BY fecha_nota ASC
            ''', (nit_cliente, codigo_producto))
            notas = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return notas
        except Exception as e:
            logger.error(f"Error obteniendo notas pendientes: {e}")
            return []

    def obtener_resumen_notas(self) -> Dict:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(saldo_pendiente) FROM notas_credito WHERE estado = 'PENDIENTE'")
            row = cursor.fetchone()
            if isinstance(row, dict):
                pendientes = row.get('COUNT(*)', 0)
                saldo = row.get('SUM(saldo_pendiente)', 0.0)
            else:
                pendientes = row[0] if row and len(row) > 0 else 0
                saldo = row[1] if row and len(row) > 1 else 0.0

            cursor.execute("SELECT COUNT(*) FROM notas_credito WHERE estado = 'APLICADA'")
            aplicadas = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*), SUM(valor_aplicado) FROM aplicaciones_notas')
            num_apps, total_aplicado = cursor.fetchone()

            conn.close()
            return {
                'notas_pendientes': pendientes or 0,
                'saldo_pendiente_total': saldo or 0.0,
                'notas_aplicadas': aplicadas or 0,
                'total_aplicaciones': num_apps or 0,
                'monto_total_aplicado': total_aplicado or 0.0
            }
        except Exception as e:
            logger.error(f"Error resumen notas: {e}")
            return {}

    def obtener_resumen_facturas(self) -> Dict:
        try:
            conn = self._get_conn()
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
            logger.error(f"Error resumen facturas: {e}")
            return {}

    def obtener_historial_nota(self, numero_nota: str) -> List[Dict]:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM aplicaciones_notas WHERE numero_nota = %s ORDER BY fecha_aplicacion DESC', (numero_nota,))
            apps = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return apps
        except Exception as e:
            logger.error(f"Error historial nota: {e}")
            return []

    def obtener_resumen_rechazos(self, dias: int = 7) -> Dict:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*), SUM(valor_total) FROM facturas_rechazadas WHERE fecha_registro >= %s', (fecha_limite,))
            total_rechazos, valor_total = cursor.fetchone()
            cursor.execute('''
                SELECT razon_rechazo, COUNT(*), SUM(valor_total)
                FROM facturas_rechazadas WHERE fecha_registro >= %s
                GROUP BY razon_rechazo ORDER BY COUNT(*) DESC
            ''', (fecha_limite,))
            por_razon = [{'razon': row[0], 'cantidad': row[1], 'valor': row[2]} for row in cursor.fetchall()]
            conn.close()
            return {'total_rechazos': total_rechazos or 0, 'valor_total_rechazado': valor_total or 0.0, 'por_razon': por_razon}
        except Exception as e:
            logger.error(f"Error resumen rechazos: {e}")
            return {}

    def actualizar_factura_con_nota(self, numero_factura: str, codigo_producto: str,
                                    numero_nota: str, valor_aplicado: float,
                                    cantidad_aplicada: float) -> bool:
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE facturas SET nota_aplicada = 1, numero_nota_aplicada = %s,
                    descuento_valor = descuento_valor + %s, descuento_cantidad = descuento_cantidad + %s
                WHERE numero_factura = %s AND codigo_producto = %s
            ''', (numero_nota, abs(valor_aplicado), abs(cantidad_aplicada), numero_factura, codigo_producto))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error actualizando factura con nota: {e}")
            return False