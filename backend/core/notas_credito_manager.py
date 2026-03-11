"""
Módulo de Gestión de Notas Crédito - VERSIÓN OPTIMIZADA v3.4

FIX CRÍTICO v3.4:
───────────────────────────────────────────────────────────────
PROBLEMA: Los valores de notas crédito vienen NEGATIVOS desde SIESA:
  cantidad = -425, valor_total = -29,388,750
  saldo_pendiente = -29,388,750, cantidad_pendiente = -425

  La query "WHERE saldo_pendiente > 0" NUNCA las encuentra.

SOLUCIÓN: 
  - SQL: WHERE ABS(saldo_pendiente) > 0  (o saldo_pendiente != 0)
  - Python: abs() en TODAS las comparaciones de cantidad y valor
───────────────────────────────────────────────────────────────

MATCH: NIT + NOMBRE_PRODUCTO (normalizado UPPER + STRIP)
CANTIDADES: cantidad_original / f_cant_base (BASE, sin convertir)
NOTA: Se aplica COMPLETA o no se aplica. NUNCA se divide.
FACTURA: Puede recibir múltiples notas (saldo se reduce).
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

    def _get_conn(self):
        return get_connection()

    # ═════════════════════════════════════════════════════════════
    # HELPERS - extraen campos de ambos formatos (crudo / transformado)
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def _extraer_nit(factura: Dict) -> str:
        return str(
            factura.get('nit_comprador')
            or factura.get('f_cliente_desp')
            or factura.get('nit_cliente')
            or ''
        ).strip()

    @staticmethod
    def _extraer_nombre_producto(factura: Dict) -> str:
        return str(
            factura.get('nombre_producto')
            or factura.get('f_desc_item')
            or factura.get('producto')
            or ''
        ).strip().upper()

    @staticmethod
    def _extraer_codigo_producto(factura: Dict) -> str:
        return str(
            factura.get('codigo_producto_api')
            or factura.get('f_cod_item')
            or factura.get('codigo_producto')
            or ''
        ).strip()

    @staticmethod
    def _extraer_cantidad_base(factura: Dict) -> float:
        """Cantidad BASE (sin convertir). Siempre positiva."""
        return abs(float(
            factura.get('cantidad_original')
            or factura.get('f_cant_base')
            or factura.get('cantidad')
            or 0
        ))

    @staticmethod
    def _extraer_valor_total(factura: Dict) -> float:
        """Valor total. Siempre positivo."""
        return abs(float(
            factura.get('valor_total')
            or factura.get('f_valor_subtotal_local')
            or 0
        ))

    @staticmethod
    def _extraer_numero_factura(factura: Dict) -> str:
        n = str(factura.get('numero_factura', '')).strip()
        if n:
            return n
        return f"{str(factura.get('f_prefijo', '')).strip()}{str(factura.get('f_nrodocto', '')).strip()}"

    @staticmethod
    def _extraer_fecha(factura: Dict) -> str:
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

    def _parsear_fecha(self, fecha_raw) -> Optional[str]:
        return self._extraer_fecha({'fecha_factura': fecha_raw, 'f_fecha': fecha_raw})

    # ═════════════════════════════════════════════════════════════
    # SCHEMA (1 sola vez)
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
            ('idx_r_fecha', 'facturas_rechazadas', 'fecha_factura'),
            ('idx_n_cliente', 'notas_credito', 'nit_cliente'),
            ('idx_n_estado', 'notas_credito', 'estado'),
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
        logger.info("BD inicializada")

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
            rows = [r for r in (self._preparar_factura_para_insert(f) for f in facturas) if r]
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
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        'PROCESADA',%s,%s,%s
                    ) ON DUPLICATE KEY UPDATE
                        cantidad_original=VALUES(cantidad_original), valor_total=VALUES(valor_total),
                        precio_unitario=VALUES(precio_unitario), cantidad_restante=VALUES(cantidad_restante),
                        valor_restante=VALUES(valor_restante), fecha_proceso=VALUES(fecha_proceso),
                        nombre_producto=VALUES(nombre_producto), codigo_factura=VALUES(codigo_factura)
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
            fecha = self._extraer_fecha(factura)
            if es_cruda:
                nf = f"{str(factura.get('f_prefijo','')).strip()}{str(factura.get('f_nrodocto','')).strip()}"
                il = int(factura.get('_indice_linea', factura.get('indice_linea', 0)) or 0)
                cp = str(factura.get('f_cod_item','')).strip()
                prod = str(factura.get('f_desc_item','')).strip()
                nit = str(factura.get('f_cliente_desp','')).strip()
                nc = str(factura.get('f_cliente_fact_razon_soc','')).strip()
                co = float(factura.get('f_cant_base',0) or 0)
                vt = float(factura.get('f_valor_subtotal_local',0) or 0)
                pu = (vt/co) if co != 0 else 0.0
                ti = str(factura.get('f_cod_tipo_inv') or factura.get('f_tipo_inv') or '').strip()
            else:
                nf = self._extraer_numero_factura(factura)
                il = int(factura.get('indice_linea', factura.get('_indice_linea', 0)) or 0)
                cp = self._extraer_codigo_producto(factura)
                prod = self._extraer_nombre_producto(factura)
                nit = self._extraer_nit(factura)
                nc = str(factura.get('nombre_comprador') or factura.get('nombre_cliente','')).strip()
                co = self._extraer_cantidad_base(factura)
                vt = self._extraer_valor_total(factura)
                pu = float(factura.get('precio_unitario',0) or 0)
                ti = str(factura.get('descripcion') or factura.get('tipo_inventario','')).strip()
            return (nf,nf,il,prod,prod,cp,cp,nit,nit,nit,nc,nc,co,pu,vt,co,vt,ti,fecha,fecha,1,1,vt)
        except Exception as e:
            logger.error(f"Error preparando factura: {e}"); return None

    def registrar_rechazadas_batch(self, rechazadas: List[Dict]) -> int:
        if not rechazadas:
            return 0
        conn = self._get_conn()
        cursor = conn.cursor()
        registradas = 0
        try:
            rows = []
            for item in rechazadas:
                f = item['factura']; razon = item['razon_rechazo']
                nf = f"{str(f.get('f_prefijo','')).strip()}{f.get('f_nrodocto','')}"
                rows.append((
                    nf, nf, str(f.get('f_cod_item','')).strip(), str(f.get('f_desc_item','')).strip(),
                    str(f.get('f_cliente_desp','')).strip(), str(f.get('f_cliente_fact_razon_soc','')).strip(),
                    float(f.get('f_cant_base',0) or 0), float(f.get('f_valor_subtotal_local',0) or 0),
                    str(f.get('f_cod_tipo_inv','')).strip(),
                    str(f.get('f_cliente_desp','')).strip(), str(f.get('f_cliente_desp','')).strip(),
                    str(f.get('f_cliente_fact_razon_soc','')).strip(), razon, self._extraer_fecha(f)
                ))
            if rows:
                cursor.executemany('''
                    INSERT INTO facturas_rechazadas
                    (numero_factura,numero_linea,codigo_producto,producto,nit_cliente,nombre_cliente,
                     cantidad,valor_total,tipo_inventario,nit_encrypted,nit_hash,nombre_cliente_encrypted,
                     razon_rechazo,fecha_factura)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ''', rows)
                registradas = len(rows)
            conn.commit()
            logger.info(f"Batch: {registradas} rechazadas")
        except Exception as e:
            conn.rollback(); logger.error(f"Error batch rechazadas: {e}")
        finally:
            conn.close()
        return registradas

    def registrar_notas_batch(self, notas: List[Dict]) -> Tuple[int, int]:
        if not notas:
            return 0, 0
        conn = self._get_conn()
        cursor = conn.cursor()
        nuevas = 0; filtradas = 0
        try:
            nums = list(set(f"{n.get('f_prefijo','')}{n.get('f_nrodocto','')}" for n in notas))
            existentes = set()
            if nums:
                ph = ','.join(['%s']*len(nums))
                cursor.execute(f'SELECT numero_nota,codigo_producto FROM notas_credito WHERE numero_nota IN ({ph})', nums)
                for r in cursor.fetchall():
                    r = r if isinstance(r, dict) else {'numero_nota':r[0],'codigo_producto':r[1]}
                    existentes.add((r['numero_nota'], r['codigo_producto']))

            rows = []
            for nota in notas:
                nn = f"{nota.get('f_prefijo','')}{nota.get('f_nrodocto','')}"
                np = str(nota.get('f_desc_item','')).strip()
                cr = nota.get('f_cod_item')
                cp = str(cr).strip() if cr and str(cr).strip() else np
                vt = float(nota.get('f_valor_subtotal_local',0) or 0)
                ca = float(nota.get('f_cant_base',0) or 0)
                ti = str(nota.get('f_cod_tipo_inv') or nota.get('f_tipo_inv') or '').strip().upper()
                cs = str(nota.get('f_notas_causal_dev','') or '').strip() or None
                nit = str(nota.get('f_cliente_desp','')).strip()
                nc = str(nota.get('f_cliente_fact_razon_soc','')).strip()

                if ca != 0 and vt == 0: filtradas += 1; continue
                if not cp and not np: continue
                if (nn, cp) in existentes: continue
                rows.append((nn, self._extraer_fecha(nota), nit, nc, cp, np, ti, nit, nit, nc, vt, ca, vt, ca, cs))

            if rows:
                cursor.executemany('''
                    INSERT INTO notas_credito
                    (numero_nota,fecha_nota,nit_cliente,nombre_cliente,codigo_producto,nombre_producto,
                     tipo_inventario,nit_encrypted,nit_hash,nombre_cliente_encrypted,
                     valor_total,cantidad,saldo_pendiente,cantidad_pendiente,causal_devolucion,estado)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PENDIENTE')
                ''', rows)
                nuevas = len(rows)
            conn.commit()
            logger.info(f"Batch: {nuevas} notas nuevas, {filtradas} filtradas")
        except Exception as e:
            conn.rollback(); logger.error(f"Error batch notas: {e}")
        finally:
            conn.close()
        return nuevas, filtradas

    # ═════════════════════════════════════════════════════════════
    # APLICACIÓN DE NOTAS CRÉDITO
    # ═════════════════════════════════════════════════════════════
    #
    # FIX v3.4: Valores NEGATIVOS desde SIESA
    #   saldo_pendiente = -29,388,750 → ABS() = 29,388,750
    #   cantidad_pendiente = -425     → abs() = 425
    #
    # SQL:    WHERE ABS(saldo_pendiente) > 0 AND estado IN (...)
    # Python: abs() en TODAS las comparaciones
    #
    # ═════════════════════════════════════════════════════════════

    def procesar_notas_para_facturas_optimizado(self, facturas: List[Dict]) -> List[Dict]:
        if not facturas:
            return []

        # Debug formato
        sample = facturas[0]
        es_transformada = 'nombre_producto' in sample and 'nit_comprador' in sample
        logger.info(f"Formato: {'TRANSFORMADO' if es_transformada else 'CRUDO API'}")

        # Paso 1: Pares únicos (nit, nombre_producto)
        pares_unicos = set()
        for f in facturas:
            nit = self._extraer_nit(f)
            nombre = self._extraer_nombre_producto(f)
            if nit and nombre:
                pares_unicos.add((nit, nombre))

        if not pares_unicos:
            logger.warning("No hay pares NIT+producto"); return []

        logger.info(f"Pares únicos: {len(pares_unicos)}")
        for p in list(pares_unicos)[:3]:
            logger.info(f"  NIT='{p[0]}' PROD='{p[1]}'")

        # Paso 2: Cargar notas pendientes
        # ══ FIX v3.4: ABS(saldo_pendiente) > 0 en vez de saldo_pendiente > 0 ══
        conn = self._get_conn()
        cursor = conn.cursor()
        nits = list(set(p[0] for p in pares_unicos))
        ph = ','.join(['%s']*len(nits))

        cursor.execute(f'''
            SELECT * FROM notas_credito
            WHERE nit_cliente IN ({ph})
            AND estado IN ('PENDIENTE', 'PARCIAL')
            AND ABS(saldo_pendiente) > 0
            ORDER BY fecha_nota ASC
        ''', nits)
        todas_notas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not todas_notas:
            logger.info("No hay notas pendientes"); return []

        logger.info(f"Notas pendientes cargadas: {len(todas_notas)}")
        for n in todas_notas[:3]:
            logger.info(
                f"  Nota {n['numero_nota']}: NIT={n['nit_cliente']} "
                f"nombre='{n.get('nombre_producto','')}' "
                f"codigo='{n.get('codigo_producto','')}' "
                f"saldo={n['saldo_pendiente']} cant={n['cantidad_pendiente']}"
            )

        # Organizar notas por (nit, NOMBRE_PRODUCTO)
        notas_por_par = defaultdict(list)
        for nota in todas_notas:
            nit_n = str(nota['nit_cliente']).strip()
            nombre_n = str(nota.get('nombre_producto') or '').strip().upper()
            codigo_n = str(nota.get('codigo_producto') or '').strip().upper()

            key_nombre = (nit_n, nombre_n)
            key_codigo = (nit_n, codigo_n)

            if nombre_n and key_nombre in pares_unicos:
                notas_por_par[key_nombre].append(nota)
            elif codigo_n and key_codigo in pares_unicos:
                notas_por_par[key_codigo].append(nota)
            else:
                logger.debug(f"  Nota {nota['numero_nota']} sin match: nombre='{nombre_n}' codigo='{codigo_n}'")

        if not notas_por_par:
            nombres_f = set(p[1] for p in pares_unicos)
            nombres_n = set()
            for n in todas_notas:
                nombres_n.add(str(n.get('nombre_producto','') or '').strip().upper())
                nombres_n.add(str(n.get('codigo_producto','') or '').strip().upper())
            logger.warning(f"Sin match. Facturas: {list(nombres_f)[:3]} | Notas: {list(nombres_n)[:3]}")
            return []

        logger.info(f"Pares con notas: {len(notas_por_par)}")

        # Paso 3: Mapa de facturas con saldos en memoria
        # Pre-cargar IDs de facturas desde BD (necesario para id_factura en aplicaciones_notas)
        conn_ids = self._get_conn()
        cur_ids = conn_ids.cursor()
        ph_nits = ','.join(['%s'] * len(nits))
        cur_ids.execute(f'''
            SELECT id, numero_factura, codigo_producto, indice_linea, fecha_proceso
            FROM facturas WHERE nit_cliente IN ({ph_nits})
        ''', nits)
        # Indexar por (numero_factura, codigo_producto, indice_linea, fecha_proceso)
        factura_ids_map = {}
        for row in cur_ids.fetchall():
            r = row if isinstance(row, dict) else {
                'id': row[0], 'numero_factura': row[1], 'codigo_producto': row[2],
                'indice_linea': row[3], 'fecha_proceso': row[4]
            }
            key_id = (
                str(r['numero_factura']).strip(),
                str(r['codigo_producto']).strip(),
                self._safe_int(r['indice_linea']),
                str(r['fecha_proceso']) if r['fecha_proceso'] else None
            )
            factura_ids_map[key_id] = r['id']
            # También guardar sin indice_linea para fallback
            key_simple = (str(r['numero_factura']).strip(), str(r['codigo_producto']).strip())
            if key_simple not in factura_ids_map:
                factura_ids_map[key_simple] = r['id']
        conn_ids.close()
        logger.info(f"IDs de facturas pre-cargados: {len(factura_ids_map)}")

        facturas_por_par = defaultdict(list)
        for i, f in enumerate(facturas):
            nit = self._extraer_nit(f)
            nombre = self._extraer_nombre_producto(f)
            if not nit or not nombre:
                continue

            num_fac = self._extraer_numero_factura(f)
            cod_prod = self._extraer_codigo_producto(f)
            fecha_fac = self._extraer_fecha(f)
            idx_linea = self._safe_int(f.get('indice_linea', f.get('_indice_linea')))

            # Buscar id_factura en BD
            id_factura = factura_ids_map.get(
                (num_fac, cod_prod, idx_linea, fecha_fac)
            ) or factura_ids_map.get(
                (num_fac, cod_prod)
            )

            facturas_por_par[(nit, nombre)].append({
                '_idx': i,
                'id_factura': id_factura,
                'numero_factura': num_fac,
                'codigo_producto': cod_prod,
                'nombre_producto': nombre,
                'nit_cliente': nit,
                'fecha_factura': fecha_fac,
                'indice_linea': idx_linea,
                'cantidad_restante': self._extraer_cantidad_base(f),
                'valor_restante': self._extraer_valor_total(f),
                'total_descuento_cantidad': 0.0,
                'total_descuento_valor': 0.0,
                'notas_aplicadas': [],
            })

        # Paso 4: Aplicar notas
        aplicaciones = []
        conn_a = self._get_conn()
        cur = conn_a.cursor()

        try:
            for key, notas_disp in notas_por_par.items():
                facs = facturas_por_par.get(key, [])
                if not facs:
                    continue

                logger.info(f"Par {key}: {len(notas_disp)} notas, {len(facs)} facturas")

                for nota in notas_disp:
                    # ══ FIX v3.4: abs() para valores negativos ══
                    cant_nota = abs(float(nota['cantidad_pendiente']))
                    val_nota = abs(float(nota['saldo_pendiente']))

                    if val_nota <= 0 and cant_nota <= 0:
                        continue

                    aplicada = False

                    for fm in facs:
                        cr = fm['cantidad_restante']
                        vr = fm['valor_restante']

                        logger.debug(
                            f"  Nota {nota['numero_nota']}(cant={cant_nota},val=${val_nota:,.0f}) "
                            f"→ Fac {fm['numero_factura']}(cant_r={cr},val_r=${vr:,.0f})"
                        )

                        if val_nota > vr:
                            logger.debug(f"    ❌ valor nota {val_nota} > valor restante {vr}")
                            continue
                        if cant_nota > cr:
                            logger.debug(f"    ❌ cant nota {cant_nota} > cant restante {cr}")
                            continue

                        # ═══ APLICAR COMPLETA ═══
                        cur.execute('''
                            INSERT INTO aplicaciones_notas
                            (id_nota, id_factura, numero_nota, numero_factura, numero_linea,
                             fecha_factura, nit_hash, nit_cliente, codigo_producto,
                             cantidad_aplicada, valor_aplicado,
                             cantidad_factura_antes, cantidad_factura_despues,
                             valor_factura_antes, valor_factura_despues)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ''', (nota['id'], fm.get('id_factura') or 0,
                              nota['numero_nota'], fm['numero_factura'],
                              fm['numero_factura'], fm['fecha_factura'],
                              nota['nit_cliente'], nota['nit_cliente'],
                              fm['codigo_producto'],
                              cant_nota, val_nota,
                              cr, cr - cant_nota,
                              vr, vr - val_nota))

                        cur.execute('''
                            UPDATE notas_credito
                            SET saldo_pendiente=0, cantidad_pendiente=0,
                                estado='APLICADA', fecha_aplicacion_completa=%s
                            WHERE id=%s
                        ''', (datetime.now().isoformat(), nota['id']))

                        nc = cr - cant_nota
                        nv = vr - val_nota

                        if fm['indice_linea'] is not None:
                            cur.execute('''
                                UPDATE facturas
                                SET cantidad_restante=%s, valor_restante=%s
                                WHERE numero_factura=%s AND codigo_producto=%s
                                  AND indice_linea=%s AND fecha_factura=%s
                            ''', (nc, nv,
                                  fm['numero_factura'], fm['codigo_producto'],
                                  fm['indice_linea'], fm['fecha_factura']))
                        else:
                            cur.execute('''
                                UPDATE facturas
                                SET cantidad_restante=%s, valor_restante=%s
                                WHERE numero_factura=%s AND codigo_producto=%s
                            ''', (nc, nv,
                                  fm['numero_factura'], fm['codigo_producto']))

                        fm['cantidad_restante'] = nc
                        fm['valor_restante'] = nv
                        fm['total_descuento_cantidad'] += cant_nota
                        fm['total_descuento_valor'] += val_nota
                        fm['notas_aplicadas'].append(nota['numero_nota'])

                        nota['saldo_pendiente'] = 0
                        nota['cantidad_pendiente'] = 0

                        aplicaciones.append({
                            'numero_nota': nota['numero_nota'],
                            'numero_factura': fm['numero_factura'],
                            'codigo_producto': fm['codigo_producto'],
                            'nombre_producto': fm['nombre_producto'],
                            'cantidad_aplicada': cant_nota,
                            'valor_aplicado': val_nota,
                            'cantidad_restante_factura': nc,
                            'valor_restante_factura': nv,
                            'estado_nota': 'APLICADA'
                        })

                        logger.info(
                            f"  ✅ {nota['numero_nota']} → {fm['numero_factura']}: "
                            f"Cant={cant_nota} Val=${val_nota:,.0f} | "
                            f"Rest: Cant={nc} Val=${nv:,.0f}"
                        )
                        aplicada = True
                        break

                    if not aplicada:
                        logger.warning(
                            f"  ⚠️ Nota {nota['numero_nota']} NO CABE "
                            f"(Cant={cant_nota} Val=${val_nota:,.0f})"
                        )

            conn_a.commit()
        except Exception as e:
            conn_a.rollback()
            logger.error(f"Error aplicando notas: {e}")
            import traceback; traceback.print_exc()
        finally:
            conn_a.close()

        logger.info(f"Total aplicaciones: {len(aplicaciones)}")

        # Paso 5: Actualizar facturas originales para Excel
        for key, fmems in facturas_por_par.items():
            for fm in fmems:
                if fm['total_descuento_valor'] > 0:
                    idx = fm['_idx']
                    facturas[idx]['descuento_valor'] = fm['total_descuento_valor']
                    facturas[idx]['descuento_cantidad'] = fm['total_descuento_cantidad']
                    facturas[idx]['nota_aplicada'] = ','.join(fm['notas_aplicadas'])

        return aplicaciones

    @staticmethod
    def _safe_int(val):
        if val is None: return None
        try: return int(val)
        except: return None

    # ═════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDAD
    # ═════════════════════════════════════════════════════════════

    def procesar_notas_para_facturas(self, f): return self.procesar_notas_para_facturas_optimizado(f)
    def registrar_nota_credito(self, n): r,_=self.registrar_notas_batch([n]); return r>0
    def registrar_factura(self, f): return self.registrar_facturas_batch([f])>0
    def registrar_factura_rechazada(self, f, r): return self.registrar_rechazadas_batch([{'factura':f,'razon_rechazo':r}])>0
    def registrar_factura_completa(self, f): return self.registrar_factura(f)

    def aplicar_nota_a_factura(self, nota, factura, cursor=None):
        nf = self._extraer_nit(factura)
        if nota['nit_cliente'] != nf: return None
        nn = str(nota.get('nombre_producto') or nota.get('codigo_producto') or '').strip().upper()
        nfp = self._extraer_nombre_producto(factura)
        if nn != nfp: return None
        cf = self._extraer_cantidad_base(factura); vf = self._extraer_valor_total(factura)
        cn = abs(float(nota['cantidad_pendiente'])); vn = abs(float(nota['saldo_pendiente']))
        if vn > vf or cn > cf: return None

        own_conn = cursor is None
        if own_conn: conn=self._get_conn(); cursor=conn.cursor()
        try:
            nfn=self._extraer_numero_factura(factura); cp=self._extraer_codigo_producto(factura)
            ff=self._extraer_fecha(factura)
            il=self._safe_int(factura.get('indice_linea',factura.get('_indice_linea')))
            # Buscar id_factura en BD
            id_factura = factura.get('id') or 0
            if not id_factura:
                cursor.execute('SELECT id FROM facturas WHERE numero_factura=%s AND codigo_producto=%s LIMIT 1', (nfn, cp))
                row = cursor.fetchone()
                id_factura = (row[0] if row and not isinstance(row, dict) else row.get('id', 0) if row else 0)
            cursor.execute('''INSERT INTO aplicaciones_notas 
                (id_nota, id_factura, numero_nota, numero_factura, numero_linea,
                 fecha_factura, nit_hash, nit_cliente, codigo_producto,
                 cantidad_aplicada, valor_aplicado,
                 cantidad_factura_antes, cantidad_factura_despues,
                 valor_factura_antes, valor_factura_despues)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (nota['id'], id_factura, nota['numero_nota'], nfn, nfn, ff,
                 nota['nit_cliente'], nota['nit_cliente'], cp,
                 cn, vn, cf, cf - cn, vf, vf - vn))
            cursor.execute('UPDATE notas_credito SET saldo_pendiente=0,cantidad_pendiente=0,estado="APLICADA",fecha_aplicacion_completa=%s WHERE id=%s',(datetime.now().isoformat(),nota['id']))
            nc=cf-cn; nv=vf-vn
            if il is not None:
                cursor.execute('UPDATE facturas SET cantidad_restante=%s,valor_restante=%s WHERE numero_factura=%s AND codigo_producto=%s AND indice_linea=%s AND fecha_proceso=%s',
                    (nc,nv,nfn,cp,il,ff))
            else:
                cursor.execute('UPDATE facturas SET cantidad_restante=%s,valor_restante=%s WHERE numero_factura=%s AND codigo_producto=%s',
                    (nc,nv,nfn,cp))
            if own_conn: conn.commit()
            return {'numero_nota':nota['numero_nota'],'numero_factura':nfn,'cantidad_aplicada':cn,'valor_aplicado':vn,'cantidad_restante_factura':nc,'valor_restante_factura':nv,'estado_nota':'APLICADA'}
        except Exception as e:
            if own_conn: conn.rollback()
            logger.error(f"Error: {e}"); return None
        finally:
            if own_conn: conn.close()

    # ═════════════════════════════════════════════════════════════
    # CONSULTAS
    # ═════════════════════════════════════════════════════════════

    def obtener_notas_pendientes(self, nit_cliente, codigo_producto):
        try:
            conn=self._get_conn(); cursor=conn.cursor()
            cursor.execute('''SELECT * FROM notas_credito
                WHERE nit_cliente=%s AND (codigo_producto=%s OR nombre_producto=%s)
                AND estado IN ('PENDIENTE','PARCIAL') AND ABS(saldo_pendiente)>0
                ORDER BY fecha_nota ASC''', (nit_cliente, codigo_producto, codigo_producto))
            r=[dict(row) for row in cursor.fetchall()]; conn.close(); return r
        except Exception as e: logger.error(f"Error: {e}"); return []

    def obtener_resumen_notas(self):
        try:
            conn=self._get_conn(); cursor=conn.cursor()
            cursor.execute("SELECT COUNT(*),SUM(ABS(saldo_pendiente)) FROM notas_credito WHERE estado='PENDIENTE'")
            row=cursor.fetchone()
            if isinstance(row,dict): p=row.get('COUNT(*)',0); s=row.get('SUM(ABS(saldo_pendiente))',0.0)
            else: p=row[0] if row else 0; s=row[1] if row and len(row)>1 else 0.0
            cursor.execute("SELECT COUNT(*) FROM notas_credito WHERE estado='APLICADA'"); a=cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*),SUM(valor_aplicado) FROM aplicaciones_notas'); na,ta=cursor.fetchone()
            conn.close()
            return {'notas_pendientes':p or 0,'saldo_pendiente_total':s or 0.0,'notas_aplicadas':a or 0,'total_aplicaciones':na or 0,'monto_total_aplicado':ta or 0.0}
        except Exception as e: logger.error(f"Error: {e}"); return {}

    def obtener_resumen_facturas(self):
        try:
            conn=self._get_conn(); cursor=conn.cursor()
            cursor.execute('SELECT COUNT(*),SUM(valor_total) FROM facturas'); tv,vt=cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM facturas WHERE nota_aplicada=1'); cn=cursor.fetchone()[0]
            cursor.execute('SELECT SUM(descuento_valor) FROM facturas WHERE nota_aplicada=1'); td=cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas'); tr=cursor.fetchone()[0]
            conn.close()
            return {'facturas_validas':tv or 0,'valor_total_facturado':vt or 0.0,'facturas_con_notas':cn or 0,'total_descontado':td or 0.0,'facturas_rechazadas':tr or 0}
        except Exception as e: logger.error(f"Error: {e}"); return {}

    def obtener_historial_nota(self, numero_nota):
        try:
            conn=self._get_conn(); cursor=conn.cursor()
            cursor.execute('SELECT * FROM aplicaciones_notas WHERE numero_nota=%s ORDER BY fecha_aplicacion DESC',(numero_nota,))
            r=[dict(row) for row in cursor.fetchall()]; conn.close(); return r
        except Exception as e: logger.error(f"Error: {e}"); return []

    def obtener_resumen_rechazos(self, dias=7):
        try:
            conn=self._get_conn(); cursor=conn.cursor()
            fl=(datetime.now()-timedelta(days=dias)).strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*),SUM(valor_total) FROM facturas_rechazadas WHERE fecha_registro>=%s',(fl,))
            tr,vt=cursor.fetchone()
            cursor.execute('SELECT razon_rechazo,COUNT(*),SUM(valor_total) FROM facturas_rechazadas WHERE fecha_registro>=%s GROUP BY razon_rechazo ORDER BY COUNT(*) DESC',(fl,))
            pr=[{'razon':r[0],'cantidad':r[1],'valor':r[2]} for r in cursor.fetchall()]; conn.close()
            return {'total_rechazos':tr or 0,'valor_total_rechazado':vt or 0.0,'por_razon':pr}
        except Exception as e: logger.error(f"Error: {e}"); return {}

    def actualizar_factura_con_nota(self, nf, cp, nn, va, ca):
        try:
            conn=self._get_conn(); cursor=conn.cursor()
            cursor.execute('UPDATE facturas SET cantidad_restante=cantidad_restante-%s,valor_restante=valor_restante-%s WHERE numero_factura=%s AND codigo_producto=%s',
                (abs(ca),abs(va),nf,cp))
            conn.commit(); conn.close(); return True
        except Exception as e: logger.error(f"Error: {e}"); return False