"""
Módulo de Gestión de Notas Crédito - VERSIÓN OPTIMIZADA v3.3

FIX v3.3 - Funciona con AMBOS formatos de factura:
───────────────────────────────────────────────────────────────
FORMATO CRUDO (API):          FORMATO TRANSFORMADO (excel_processor):
  f_cliente_desp                nit_comprador
  f_desc_item                   nombre_producto
  f_cod_item                    codigo_producto_api
  f_cant_base                   cantidad_original (base)
  f_valor_subtotal_local        valor_total
  f_prefijo + f_nrodocto        numero_factura

MATCH: NIT + NOMBRE_PRODUCTO (normalizado UPPER + STRIP)
  - La nota tiene nombre en nombre_producto O en codigo_producto
  - La factura tiene nombre en nombre_producto O f_desc_item O producto
  - Helper _extraer_nombre_producto() busca en todos los campos posibles

CANTIDADES: Se usa cantidad_original / f_cant_base (BASE, sin convertir)
  - La nota tiene f_cant_base = 425
  - La factura transformada tiene cantidad_original = 425
  - NO usar 'cantidad' (que es la convertida: 17000)
───────────────────────────────────────────────────────────────
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

_schema_initialized = False


class NotasCreditoManager:

    def __init__(self):
        global _schema_initialized
        if not _schema_initialized:
            self._crear_base_datos()
            _schema_initialized = True
            logger.info("NotasCreditoManager: Schema inicializado")
        else:
            logger.debug("NotasCreditoManager: Schema ya inicializado")

    def _get_conn(self):
        return get_connection()

    # ═════════════════════════════════════════════════════════════
    # HELPERS PARA EXTRAER CAMPOS (crudo o transformado)
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def _extraer_nit(factura: Dict) -> str:
        """Extrae NIT del comprador, funciona con ambos formatos"""
        return str(
            factura.get('nit_comprador')       # transformado
            or factura.get('f_cliente_desp')    # crudo API
            or factura.get('nit_cliente')       # desde BD
            or ''
        ).strip()

    @staticmethod
    def _extraer_nombre_producto(factura: Dict) -> str:
        """
        Extrae nombre del producto normalizado (UPPER + STRIP).
        Busca en TODOS los campos posibles.
        """
        nombre = str(
            factura.get('nombre_producto')     # transformado / BD
            or factura.get('f_desc_item')      # crudo API
            or factura.get('producto')         # BD campo alterno
            or ''
        ).strip().upper()
        return nombre

    @staticmethod
    def _extraer_codigo_producto(factura: Dict) -> str:
        """Extrae código de producto real"""
        return str(
            factura.get('codigo_producto_api')  # transformado
            or factura.get('f_cod_item')        # crudo API
            or factura.get('codigo_producto')   # BD
            or ''
        ).strip()

    @staticmethod
    def _extraer_cantidad_base(factura: Dict) -> float:
        """
        Extrae cantidad BASE (sin convertir por multiplicador).
        IMPORTANTE: usar 'cantidad_original' (no 'cantidad' que es la convertida)
        """
        return abs(float(
            factura.get('cantidad_original')          # transformado (base)
            or factura.get('f_cant_base')              # crudo API (base)
            or factura.get('cantidad')                 # fallback
            or 0
        ))

    @staticmethod
    def _extraer_valor_total(factura: Dict) -> float:
        """Extrae valor total"""
        return abs(float(
            factura.get('valor_total')                 # transformado / BD
            or factura.get('f_valor_subtotal_local')   # crudo API
            or 0
        ))

    @staticmethod
    def _extraer_numero_factura(factura: Dict) -> str:
        """Extrae número de factura completo"""
        numero = str(factura.get('numero_factura', '')).strip()
        if numero:
            return numero
        prefijo = str(factura.get('f_prefijo', '')).strip()
        nrodocto = str(factura.get('f_nrodocto', '')).strip()
        return f"{prefijo}{nrodocto}"

    @staticmethod
    def _extraer_fecha(factura: Dict) -> str:
        """Extrae fecha de la factura"""
        fecha_raw = factura.get('fecha_factura') or factura.get('f_fecha')
        if not fecha_raw:
            return datetime.now().strftime('%Y-%m-%d')
        if isinstance(fecha_raw, str):
            try:
                return datetime.fromisoformat(str(fecha_raw).replace('T00:00:00', '')).strftime('%Y-%m-%d')
            except Exception:
                return datetime.now().strftime('%Y-%m-%d')
        elif hasattr(fecha_raw, 'strftime'):
            return fecha_raw.strftime('%Y-%m-%d')
        return datetime.now().strftime('%Y-%m-%d')

    # ═════════════════════════════════════════════════════════════
    # SCHEMA
    # ═════════════════════════════════════════════════════════════

    def _crear_base_datos(self):
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

        for name, table, cols in [
            ('idx_f_numero', 'facturas', 'numero_factura'),
            ('idx_f_cliente', 'facturas', 'nit_cliente'),
            ('idx_f_producto', 'facturas', 'codigo_producto'),
            ('idx_f_fecha', 'facturas', 'fecha_factura'),
            ('idx_f_cli_prod', 'facturas', 'nit_cliente, codigo_producto'),
            ('idx_r_fecha', 'facturas_rechazadas', 'fecha_factura'),
            ('idx_n_cliente', 'notas_credito', 'nit_cliente'),
            ('idx_n_estado', 'notas_credito', 'estado'),
            ('idx_n_cli_est', 'notas_credito', 'nit_cliente, estado'),
            ('idx_a_nota', 'aplicaciones_notas', 'numero_nota'),
            ('idx_a_factura', 'aplicaciones_notas', 'numero_factura'),
        ]:
            try:
                cursor.execute(f"CREATE INDEX {name} ON {table}({cols})")
            except Exception:
                pass

        self._sync_nullable_columns(cursor)
        conn.commit()
        conn.close()
        logger.info("BD inicializada correctamente")

    def _sync_nullable_columns(self, cursor):
        for q in [
            "UPDATE facturas SET producto = COALESCE(producto, nombre_producto) WHERE producto IS NULL AND nombre_producto IS NOT NULL",
            "UPDATE facturas SET nombre_producto = COALESCE(nombre_producto, producto) WHERE nombre_producto IS NULL AND producto IS NOT NULL",
            "UPDATE facturas SET nit_encrypted = COALESCE(nit_encrypted, nit_cliente) WHERE nit_encrypted IS NULL",
            "UPDATE facturas SET nit_hash = COALESCE(nit_hash, nit_cliente) WHERE nit_hash IS NULL",
            "UPDATE facturas SET nombre_cliente_encrypted = COALESCE(nombre_cliente_encrypted, nombre_cliente) WHERE nombre_cliente_encrypted IS NULL",
            "UPDATE facturas SET cantidad_restante = COALESCE(cantidad_restante, cantidad_original) WHERE cantidad_restante IS NULL",
            "UPDATE facturas SET valor_restante = COALESCE(valor_restante, valor_total) WHERE valor_restante IS NULL",
            "UPDATE facturas SET fecha_proceso = COALESCE(fecha_proceso, fecha_factura) WHERE fecha_proceso IS NULL",
            "UPDATE notas_credito SET nit_encrypted = COALESCE(nit_encrypted, nit_cliente) WHERE nit_encrypted IS NULL",
            "UPDATE notas_credito SET nit_hash = COALESCE(nit_hash, nit_cliente) WHERE nit_hash IS NULL",
            "UPDATE notas_credito SET nombre_cliente_encrypted = COALESCE(nombre_cliente_encrypted, nombre_cliente) WHERE nombre_cliente_encrypted IS NULL",
            "UPDATE notas_credito SET saldo_pendiente = COALESCE(saldo_pendiente, valor_total) WHERE saldo_pendiente IS NULL",
            "UPDATE notas_credito SET cantidad_pendiente = COALESCE(cantidad_pendiente, cantidad) WHERE cantidad_pendiente IS NULL",
            "UPDATE facturas_rechazadas SET nit_encrypted = COALESCE(nit_encrypted, nit_cliente) WHERE nit_encrypted IS NULL",
            "UPDATE facturas_rechazadas SET nit_hash = COALESCE(nit_hash, nit_cliente) WHERE nit_hash IS NULL",
            "UPDATE facturas_rechazadas SET nombre_cliente_encrypted = COALESCE(nombre_cliente_encrypted, nombre_cliente) WHERE nombre_cliente_encrypted IS NULL",
        ]:
            try:
                cursor.execute(q)
            except Exception:
                pass

    # ═════════════════════════════════════════════════════════════
    # BATCH OPERATIONS
    # ═════════════════════════════════════════════════════════════

    def registrar_facturas_batch(self, facturas: List[Dict]) -> int:
        if not facturas:
            return 0
        conn = self._get_conn()
        cursor = conn.cursor()
        registradas = 0
        try:
            rows = []
            for f in facturas:
                row = self._preparar_factura_para_insert(f)
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
            logger.info(f"Batch: {registradas} facturas registradas")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error batch facturas: {e}")
            import traceback; traceback.print_exc()
        finally:
            conn.close()
        return registradas

    def _preparar_factura_para_insert(self, factura: Dict) -> Optional[tuple]:
        try:
            es_cruda = any(k in factura for k in ('f_prefijo', 'f_nrodocto', 'f_cod_item'))
            fecha_factura = self._extraer_fecha(factura)

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
                numero_factura = self._extraer_numero_factura(factura)
                indice_linea = int(factura.get('indice_linea', factura.get('_indice_linea', 0)) or 0)
                codigo_producto = self._extraer_codigo_producto(factura)
                producto = self._extraer_nombre_producto(factura)  # nombre normalizado
                nit_cliente = self._extraer_nit(factura)
                nombre_cliente = str(factura.get('nombre_comprador') or factura.get('nombre_cliente', '')).strip()
                cantidad_original = self._extraer_cantidad_base(factura)
                valor_total = self._extraer_valor_total(factura)
                precio_unitario = float(factura.get('precio_unitario', 0.0) or 0.0)
                tipo_inventario = str(factura.get('descripcion') or factura.get('tipo_inventario', '')).strip()

            return (
                numero_factura, numero_factura, indice_linea, producto, producto,
                codigo_producto, codigo_producto, nit_cliente, nit_cliente, nit_cliente,
                nombre_cliente, nombre_cliente, cantidad_original, precio_unitario,
                valor_total, cantidad_original, valor_total, tipo_inventario,
                fecha_factura, fecha_factura, 1, 1, valor_total
            )
        except Exception as e:
            logger.error(f"Error preparando factura: {e}")
            return None

    def registrar_rechazadas_batch(self, rechazadas: List[Dict]) -> int:
        if not rechazadas:
            return 0
        conn = self._get_conn()
        cursor = conn.cursor()
        registradas = 0
        try:
            rows = []
            for item in rechazadas:
                f = item['factura']
                razon = item['razon_rechazo']
                prefijo = str(f.get('f_prefijo', '')).strip()
                nrodocto = f.get('f_nrodocto', '')
                rows.append((
                    f"{prefijo}{nrodocto}", f"{prefijo}{nrodocto}",
                    str(f.get('f_cod_item', '')).strip(),
                    str(f.get('f_desc_item', '')).strip(),
                    str(f.get('f_cliente_desp', '')).strip(),
                    str(f.get('f_cliente_fact_razon_soc', '')).strip(),
                    float(f.get('f_cant_base', 0.0) or 0.0),
                    float(f.get('f_valor_subtotal_local', 0.0) or 0.0),
                    str(f.get('f_cod_tipo_inv', '')).strip(),
                    str(f.get('f_cliente_desp', '')).strip(),
                    str(f.get('f_cliente_desp', '')).strip(),
                    str(f.get('f_cliente_fact_razon_soc', '')).strip(),
                    razon, self._extraer_fecha(f)
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
        if not notas:
            return 0, 0
        conn = self._get_conn()
        cursor = conn.cursor()
        nuevas = 0
        filtradas = 0
        try:
            numeros_check = list(set(
                f"{n.get('f_prefijo', '')}{n.get('f_nrodocto', '')}" for n in notas
            ))
            existentes = set()
            if numeros_check:
                ph = ','.join(['%s'] * len(numeros_check))
                cursor.execute(f'SELECT numero_nota, codigo_producto FROM notas_credito WHERE numero_nota IN ({ph})', numeros_check)
                for row in cursor.fetchall():
                    r = row if isinstance(row, dict) else {'numero_nota': row[0], 'codigo_producto': row[1]}
                    existentes.add((r['numero_nota'], r['codigo_producto']))

            rows_to_insert = []
            for nota in notas:
                numero_nota = f"{nota.get('f_prefijo', '')}{nota.get('f_nrodocto', '')}"
                fecha_nota = self._extraer_fecha(nota)
                nit_cliente = str(nota.get('f_cliente_desp', '')).strip()
                nombre_cliente = str(nota.get('f_cliente_fact_razon_soc', '')).strip()
                nombre_producto = str(nota.get('f_desc_item', '')).strip()
                tipo_inventario = str(nota.get('f_cod_tipo_inv') or nota.get('f_tipo_inv') or '').strip().upper()
                causal = str(nota.get('f_notas_causal_dev', '') or '').strip() or None

                codigo_raw = nota.get('f_cod_item')
                if codigo_raw and str(codigo_raw).strip():
                    codigo_producto = str(codigo_raw).strip()
                else:
                    codigo_producto = nombre_producto

                valor_total = float(nota.get('f_valor_subtotal_local', 0.0) or 0.0)
                cantidad = float(nota.get('f_cant_base', 0.0) or 0.0)

                if cantidad != 0 and valor_total == 0:
                    filtradas += 1
                    continue
                if not codigo_producto and not nombre_producto:
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
        Aplica notas crédito a facturas.
        Match por: NIT + NOMBRE DE PRODUCTO (normalizado UPPER).
        Funciona con datos crudos API o transformados por ExcelProcessor.
        """
        if not facturas:
            return []

        # ── DEBUG: Mostrar formato de la primera factura ──
        sample = facturas[0]
        es_cruda = any(k in sample for k in ('f_prefijo', 'f_nrodocto'))
        es_transformada = 'nombre_producto' in sample and 'nit_comprador' in sample
        logger.info(f"Formato facturas: {'CRUDO API' if es_cruda else 'TRANSFORMADO' if es_transformada else 'DESCONOCIDO'}")
        logger.info(f"Campos de muestra: {list(sample.keys())[:10]}...")

        # ── Paso 1: Extraer pares únicos (nit, nombre_producto) ──
        pares_unicos = set()
        for factura in facturas:
            nit = self._extraer_nit(factura)
            nombre_prod = self._extraer_nombre_producto(factura)
            if nit and nombre_prod:
                pares_unicos.add((nit, nombre_prod))

        if not pares_unicos:
            logger.warning("No hay pares NIT+producto para buscar notas")
            return []

        logger.info(f"Pares únicos (NIT, nombre_producto): {len(pares_unicos)}")
        # Mostrar algunos pares para debug
        for par in list(pares_unicos)[:3]:
            logger.info(f"  Par ejemplo: NIT='{par[0]}' PRODUCTO='{par[1]}'")

        # ── Paso 2: Cargar TODAS las notas pendientes (1 query) ──
        conn = self._get_conn()
        cursor = conn.cursor()

        nits_unicos = list(set(p[0] for p in pares_unicos))
        ph = ','.join(['%s'] * len(nits_unicos))

        cursor.execute(f'''
            SELECT * FROM notas_credito
            WHERE nit_cliente IN ({ph})
            AND estado IN ('PENDIENTE', 'PARCIAL')
            AND saldo_pendiente > 0
            ORDER BY fecha_nota ASC
        ''', nits_unicos)

        todas_notas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not todas_notas:
            logger.info("No hay notas pendientes para los clientes")
            return []

        logger.info(f"Notas pendientes cargadas: {len(todas_notas)}")

        # ── Organizar notas por (nit, NOMBRE_PRODUCTO) ──
        notas_por_par = defaultdict(list)
        notas_sin_match = []

        for nota in todas_notas:
            nit_nota = str(nota['nit_cliente']).strip()
            # El nombre puede estar en nombre_producto O codigo_producto (cuando f_cod_item era NULL)
            nombre_nota = str(nota.get('nombre_producto') or '').strip().upper()
            codigo_nota = str(nota.get('codigo_producto') or '').strip().upper()

            # Intentar match con nombre_producto primero
            key_nombre = (nit_nota, nombre_nota)
            key_codigo = (nit_nota, codigo_nota)

            matched = False
            if nombre_nota and key_nombre in pares_unicos:
                notas_por_par[key_nombre].append(nota)
                matched = True
            elif codigo_nota and key_codigo in pares_unicos:
                notas_por_par[key_codigo].append(nota)
                matched = True

            if not matched:
                notas_sin_match.append(nota)
                logger.debug(
                    f"  Nota {nota['numero_nota']}: NIT='{nit_nota}' "
                    f"nombre='{nombre_nota}' codigo='{codigo_nota}' → SIN MATCH en pares"
                )

        if notas_sin_match:
            logger.warning(f"Notas sin match de par: {len(notas_sin_match)}")
            for n in notas_sin_match[:5]:
                logger.warning(
                    f"  {n['numero_nota']}: NIT='{n['nit_cliente']}' "
                    f"nombre='{n.get('nombre_producto', '')}' "
                    f"codigo='{n.get('codigo_producto', '')}'"
                )

        if not notas_por_par:
            logger.warning("Ninguna nota coincide con facturas")
            # Debug extra
            nombres_fact = set(p[1] for p in pares_unicos)
            nombres_nota = set()
            for n in todas_notas:
                nombres_nota.add(str(n.get('nombre_producto') or '').strip().upper())
                nombres_nota.add(str(n.get('codigo_producto') or '').strip().upper())
            logger.warning(f"  Nombres en facturas (muestra): {list(nombres_fact)[:5]}")
            logger.warning(f"  Nombres en notas (muestra):    {list(nombres_nota)[:5]}")
            return []

        logger.info(f"Pares con notas aplicables: {len(notas_por_par)}")

        # ── Paso 3: Construir mapa de facturas con saldos en memoria ──
        facturas_por_par = defaultdict(list)
        for i, factura in enumerate(facturas):
            nit = self._extraer_nit(factura)
            nombre_prod = self._extraer_nombre_producto(factura)
            if not nit or not nombre_prod:
                continue

            codigo_producto_bd = self._extraer_codigo_producto(factura)
            cantidad_base = self._extraer_cantidad_base(factura)
            valor_total = self._extraer_valor_total(factura)
            numero_factura = self._extraer_numero_factura(factura)
            fecha_factura = self._extraer_fecha(factura)

            indice_linea = factura.get('indice_linea', factura.get('_indice_linea'))
            if indice_linea is not None:
                try:
                    indice_linea = int(indice_linea)
                except (TypeError, ValueError):
                    indice_linea = None

            facturas_por_par[(nit, nombre_prod)].append({
                '_idx': i,
                'numero_factura': numero_factura,
                'codigo_producto': codigo_producto_bd,
                'nombre_producto': nombre_prod,
                'nit_cliente': nit,
                'fecha_factura': fecha_factura,
                'indice_linea': indice_linea,
                'cantidad_restante': cantidad_base,
                'valor_restante': valor_total,
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
                    logger.debug(f"Par {key} tiene notas pero sin facturas candidatas")
                    continue

                logger.info(
                    f"Par NIT={key[0]} PROD='{key[1]}': "
                    f"{len(notas_disponibles)} notas, {len(facturas_candidatas)} facturas"
                )

                for nota in notas_disponibles:
                    if nota['saldo_pendiente'] <= 0 or nota['cantidad_pendiente'] <= 0:
                        continue

                    cantidad_nota = abs(float(nota['cantidad_pendiente']))
                    valor_nota = abs(float(nota['saldo_pendiente']))
                    nota_aplicada = False

                    for fmem in facturas_candidatas:
                        cant_rest = fmem['cantidad_restante']
                        val_rest = fmem['valor_restante']

                        logger.debug(
                            f"  Intentando: Nota {nota['numero_nota']} "
                            f"(cant={cantidad_nota}, val=${valor_nota:,.2f}) → "
                            f"Factura {fmem['numero_factura']} "
                            f"(cant_rest={cant_rest}, val_rest=${val_rest:,.2f})"
                        )

                        if valor_nota > val_rest:
                            logger.debug(f"    ❌ valor nota > valor restante factura")
                            continue
                        if cantidad_nota > cant_rest:
                            logger.debug(f"    ❌ cantidad nota > cantidad restante factura")
                            continue

                        # ═══ APLICAR NOTA COMPLETA ═══
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
                            fmem['codigo_producto'],
                            cantidad_nota, valor_nota
                        ))

                        cursor_apply.execute('''
                            UPDATE notas_credito
                            SET saldo_pendiente = 0, cantidad_pendiente = 0,
                                estado = 'APLICADA', fecha_aplicacion_completa = %s
                            WHERE id = %s
                        ''', (datetime.now().isoformat(), nota['id']))

                        nueva_cant = cant_rest - cantidad_nota
                        nuevo_val = val_rest - valor_nota

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

                        fmem['cantidad_restante'] = nueva_cant
                        fmem['valor_restante'] = nuevo_val
                        fmem['total_descuento_cantidad'] += cantidad_nota
                        fmem['total_descuento_valor'] += valor_nota
                        fmem['notas_aplicadas'].append(nota['numero_nota'])

                        nota['saldo_pendiente'] = 0
                        nota['cantidad_pendiente'] = 0

                        aplicaciones.append({
                            'numero_nota': nota['numero_nota'],
                            'numero_factura': fmem['numero_factura'],
                            'codigo_producto': fmem['codigo_producto'],
                            'nombre_producto': fmem['nombre_producto'],
                            'cantidad_aplicada': cantidad_nota,
                            'valor_aplicado': valor_nota,
                            'cantidad_restante_factura': nueva_cant,
                            'valor_restante_factura': nuevo_val,
                            'estado_nota': 'APLICADA'
                        })

                        logger.info(
                            f"  ✅ Nota {nota['numero_nota']} → {fmem['numero_factura']}: "
                            f"Cant={cantidad_nota} Val=${valor_nota:,.2f} | "
                            f"Restante: Cant={nueva_cant} Val=${nuevo_val:,.2f}"
                        )
                        nota_aplicada = True
                        break

                    if not nota_aplicada:
                        logger.warning(
                            f"  ⚠️ Nota {nota['numero_nota']} NO CABE en ninguna factura "
                            f"(Cant={cantidad_nota} Val=${valor_nota:,.2f})"
                        )

            conn_apply.commit()
        except Exception as e:
            conn_apply.rollback()
            logger.error(f"Error aplicando notas: {e}")
            import traceback; traceback.print_exc()
        finally:
            conn_apply.close()

        logger.info(f"Total aplicaciones: {len(aplicaciones)}")

        # ── Paso 5: Actualizar facturas originales para Excel ──
        for key, facturas_mem in facturas_por_par.items():
            for fmem in facturas_mem:
                if fmem['total_descuento_valor'] > 0:
                    idx = fmem['_idx']
                    facturas[idx]['descuento_valor'] = fmem['total_descuento_valor']
                    facturas[idx]['descuento_cantidad'] = fmem['total_descuento_cantidad']
                    facturas[idx]['nota_aplicada'] = ','.join(fmem['notas_aplicadas'])

        return aplicaciones

    # Aliases
    def procesar_notas_para_facturas(self, facturas: List[Dict]) -> List[Dict]:
        return self.procesar_notas_para_facturas_optimizado(facturas)

    def registrar_nota_credito(self, nota: Dict) -> bool:
        n, _ = self.registrar_notas_batch([nota]); return n > 0

    def registrar_factura(self, factura: Dict) -> bool:
        return self.registrar_facturas_batch([factura]) > 0

    def registrar_factura_rechazada(self, factura: Dict, razon: str) -> bool:
        return self.registrar_rechazadas_batch([{'factura': factura, 'razon_rechazo': razon}]) > 0

    def registrar_factura_completa(self, ft: Dict) -> bool:
        return self.registrar_factura(ft)

    def aplicar_nota_a_factura(self, nota: Dict, factura: Dict, cursor=None) -> Optional[Dict]:
        nombre_fact = self._extraer_nombre_producto(factura)
        nombre_nota = str(nota.get('nombre_producto') or nota.get('codigo_producto') or '').strip().upper()
        nit_fact = self._extraer_nit(factura)

        if nota['nit_cliente'] != nit_fact: return None
        if nombre_nota != nombre_fact: return None

        cant_fact = self._extraer_cantidad_base(factura)
        val_fact = self._extraer_valor_total(factura)
        cant_nota = abs(float(nota['cantidad_pendiente']))
        val_nota = abs(float(nota['saldo_pendiente']))

        if val_nota > val_fact: return None
        if cant_nota > cant_fact: return None

        conn = None
        if cursor is None: conn = self._get_conn(); cursor = conn.cursor()
        try:
            nf = self._extraer_numero_factura(factura)
            cp = self._extraer_codigo_producto(factura)
            ff = self._extraer_fecha(factura)
            il = factura.get('indice_linea', factura.get('_indice_linea'))
            if il is not None:
                try: il = int(il)
                except: il = None

            cursor.execute('INSERT INTO aplicaciones_notas (id_nota,numero_nota,numero_factura,numero_linea,fecha_factura,nit_cliente,codigo_producto,cantidad_aplicada,valor_aplicado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (nota['id'],nota['numero_nota'],nf,nf,ff,nota['nit_cliente'],cp,cant_nota,val_nota))
            cursor.execute('UPDATE notas_credito SET saldo_pendiente=0,cantidad_pendiente=0,estado=%s,fecha_aplicacion_completa=%s WHERE id=%s',
                ('APLICADA',datetime.now().isoformat(),nota['id']))
            nc=cant_fact-cant_nota; nv=val_fact-val_nota
            if il is not None:
                cursor.execute('UPDATE facturas SET nota_aplicada=1,numero_nota_aplicada=%s,descuento_cantidad=descuento_cantidad+%s,descuento_valor=descuento_valor+%s,cantidad_restante=%s,valor_restante=%s WHERE numero_factura=%s AND codigo_producto=%s AND indice_linea=%s AND fecha_proceso=%s',
                    (nota['numero_nota'],cant_nota,val_nota,nc,nv,nf,cp,il,ff))
            else:
                cursor.execute('UPDATE facturas SET nota_aplicada=1,numero_nota_aplicada=%s,descuento_cantidad=descuento_cantidad+%s,descuento_valor=descuento_valor+%s,cantidad_restante=%s,valor_restante=%s WHERE numero_factura=%s AND codigo_producto=%s',
                    (nota['numero_nota'],cant_nota,val_nota,nc,nv,nf,cp))
            if conn: conn.commit()
            return {'numero_nota':nota['numero_nota'],'numero_factura':nf,'cantidad_aplicada':cant_nota,'valor_aplicado':val_nota,'cantidad_restante_factura':nc,'valor_restante_factura':nv,'estado_nota':'APLICADA'}
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Error: {e}"); return None
        finally:
            if conn: conn.close()

    def _parsear_fecha(self, fecha_raw) -> Optional[str]:
        return self._extraer_fecha({'fecha_factura': fecha_raw, 'f_fecha': fecha_raw})

    # ═════════════════════════════════════════════════════════════
    # CONSULTAS
    # ═════════════════════════════════════════════════════════════

    def obtener_notas_pendientes(self, nit_cliente: str, codigo_producto: str) -> List[Dict]:
        try:
            conn=self._get_conn();cursor=conn.cursor()
            cursor.execute('SELECT * FROM notas_credito WHERE nit_cliente=%s AND (codigo_producto=%s OR nombre_producto=%s) AND estado IN ("PENDIENTE","PARCIAL") AND saldo_pendiente>0 ORDER BY fecha_nota ASC',(nit_cliente,codigo_producto,codigo_producto))
            r=[dict(row) for row in cursor.fetchall()];conn.close();return r
        except Exception as e: logger.error(f"Error: {e}"); return []

    def obtener_resumen_notas(self) -> Dict:
        try:
            conn=self._get_conn();cursor=conn.cursor()
            cursor.execute("SELECT COUNT(*),SUM(saldo_pendiente) FROM notas_credito WHERE estado='PENDIENTE'")
            row=cursor.fetchone()
            if isinstance(row,dict): p=row.get('COUNT(*)',0);s=row.get('SUM(saldo_pendiente)',0.0)
            else: p=row[0] if row else 0;s=row[1] if row and len(row)>1 else 0.0
            cursor.execute("SELECT COUNT(*) FROM notas_credito WHERE estado='APLICADA'");a=cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*),SUM(valor_aplicado) FROM aplicaciones_notas');na,ta=cursor.fetchone()
            conn.close()
            return {'notas_pendientes':p or 0,'saldo_pendiente_total':s or 0.0,'notas_aplicadas':a or 0,'total_aplicaciones':na or 0,'monto_total_aplicado':ta or 0.0}
        except Exception as e: logger.error(f"Error: {e}"); return {}

    def obtener_resumen_facturas(self) -> Dict:
        try:
            conn=self._get_conn();cursor=conn.cursor()
            cursor.execute('SELECT COUNT(*),SUM(valor_total) FROM facturas');tv,vt=cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM facturas WHERE nota_aplicada=1');cn=cursor.fetchone()[0]
            cursor.execute('SELECT SUM(descuento_valor) FROM facturas WHERE nota_aplicada=1');td=cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas');tr=cursor.fetchone()[0]
            conn.close()
            return {'facturas_validas':tv or 0,'valor_total_facturado':vt or 0.0,'facturas_con_notas':cn or 0,'total_descontado':td or 0.0,'facturas_rechazadas':tr or 0}
        except Exception as e: logger.error(f"Error: {e}"); return {}

    def obtener_historial_nota(self, numero_nota: str) -> List[Dict]:
        try:
            conn=self._get_conn();cursor=conn.cursor()
            cursor.execute('SELECT * FROM aplicaciones_notas WHERE numero_nota=%s ORDER BY fecha_aplicacion DESC',(numero_nota,))
            r=[dict(row) for row in cursor.fetchall()];conn.close();return r
        except Exception as e: logger.error(f"Error: {e}"); return []

    def obtener_resumen_rechazos(self, dias: int = 7) -> Dict:
        try:
            conn=self._get_conn();cursor=conn.cursor()
            fl=(datetime.now()-timedelta(days=dias)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*),SUM(valor_total) FROM facturas_rechazadas WHERE fecha_registro>=%s',(fl,));tr,vt=cursor.fetchone()
            cursor.execute('SELECT razon_rechazo,COUNT(*),SUM(valor_total) FROM facturas_rechazadas WHERE fecha_registro>=%s GROUP BY razon_rechazo ORDER BY COUNT(*) DESC',(fl,))
            pr=[{'razon':r[0],'cantidad':r[1],'valor':r[2]} for r in cursor.fetchall()];conn.close()
            return {'total_rechazos':tr or 0,'valor_total_rechazado':vt or 0.0,'por_razon':pr}
        except Exception as e: logger.error(f"Error: {e}"); return {}

    def actualizar_factura_con_nota(self, numero_factura, codigo_producto, numero_nota, valor_aplicado, cantidad_aplicada) -> bool:
        try:
            conn=self._get_conn();cursor=conn.cursor()
            cursor.execute('UPDATE facturas SET nota_aplicada=1,numero_nota_aplicada=%s,descuento_valor=descuento_valor+%s,descuento_cantidad=descuento_cantidad+%s WHERE numero_factura=%s AND codigo_producto=%s',
                (numero_nota,abs(valor_aplicado),abs(cantidad_aplicada),numero_factura,codigo_producto))
            conn.commit();conn.close();return True
        except Exception as e: logger.error(f"Error: {e}"); return False