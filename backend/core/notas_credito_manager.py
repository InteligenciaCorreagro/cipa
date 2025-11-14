"""
Módulo de Gestión de Notas Crédito
Maneja la aplicación de notas crédito a facturas con persistencia en SQLite
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

        # Tabla de notas crédito pendientes
        # IMPORTANTE: Una nota puede tener múltiples líneas (productos)
        # El constraint UNIQUE es (numero_nota, codigo_producto)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_nota TEXT NOT NULL,
                fecha_nota DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT,
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,
                saldo_pendiente REAL NOT NULL,
                cantidad_pendiente REAL NOT NULL,
                causal_devolucion TEXT,
                estado TEXT DEFAULT 'PENDIENTE',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aplicacion_completa TIMESTAMP NULL,
                UNIQUE(numero_nota, codigo_producto)
            )
        ''')
        
        # Tabla de aplicaciones de notas crédito
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aplicaciones_notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_nota INTEGER NOT NULL,
                numero_nota TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                fecha_factura DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                valor_aplicado REAL NOT NULL,
                cantidad_aplicada REAL NOT NULL,
                fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_nota) REFERENCES notas_credito(id)
            )
        ''')
        
        # Tabla de facturas válidas (las que pasan las reglas de negocio)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT NOT NULL,
                fecha_factura DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT,
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,
                valor_unitario REAL,
                estado TEXT DEFAULT 'PROCESADA',
                tiene_nota_credito INTEGER DEFAULT 0,
                valor_nota_aplicada REAL DEFAULT 0,
                cantidad_nota_aplicada REAL DEFAULT 0,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(numero_factura, codigo_producto)
            )
        ''')

        # Índices para mejorar rendimiento en tabla facturas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(nit_cliente)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_notas ON facturas(tiene_nota_credito)')

        # Tabla de facturas rechazadas (para auditoría y detección de nuevos tipos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas_rechazadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT NOT NULL,
                fecha_factura DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT NOT NULL,
                valor_total REAL NOT NULL,
                razon_rechazo TEXT NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # NUEVA: Tabla de tipos de inventario detectados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tipos_inventario_detectados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_tipo TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                primera_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_facturas INTEGER DEFAULT 1,
                es_excluido INTEGER DEFAULT 0
            )
        ''')
        
        # Índices para mejorar rendimiento
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notas_cliente_producto 
            ON notas_credito(nit_cliente, codigo_producto, estado)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_aplicaciones_nota 
            ON aplicaciones_notas(numero_nota)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rechazadas_fecha 
            ON facturas_rechazadas(fecha_factura)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rechazadas_tipo 
            ON facturas_rechazadas(tipo_inventario)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tipos_codigo 
            ON tipos_inventario_detectados(codigo_tipo)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Base de datos inicializada correctamente con todas las tablas")
    
    def registrar_nota_credito(self, nota: Dict) -> bool:
        """
        Registra una nueva nota crédito en la base de datos

        Args:
            nota: Datos de la nota crédito desde la API

        Returns:
            True si se registró correctamente, False si ya existía
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

            # IMPORTANTE: f_cod_item no siempre está disponible en la API
            # Usar f_cod_item si existe, sino usar f_desc_item como identificador
            codigo_producto_raw = nota.get('f_cod_item') or nota.get('f_desc_item', '')
            codigo_producto = str(codigo_producto_raw).strip()

            nombre_producto = str(nota.get('f_desc_item', '')).strip()
            valor_total = float(nota.get('f_valor_subtotal_local', 0.0) or 0.0)
            cantidad = float(nota.get('f_cant_base', 0.0) or 0.0)

            # Extraer tipo de inventario (puede venir en f_cod_tipo_inv o f_tipo_inv)
            tipo_inventario_raw = nota.get('f_cod_tipo_inv') or nota.get('f_tipo_inv') or ''
            tipo_inventario = str(tipo_inventario_raw).strip().upper()

            # Extraer causal de devolución
            causal_devolucion = str(nota.get('f_notas_causal_dev', '') or '').strip() or None

            # Validación: código de producto no puede estar vacío
            if not codigo_producto:
                logger.error(f"⚠️ Nota crédito {numero_nota} sin código de producto - Rechazada")
                logger.error(f"   Tipo inventario: {tipo_inventario}")
                logger.error(f"   f_cod_item: {nota.get('f_cod_item')}")
                logger.error(f"   f_desc_item: {nota.get('f_desc_item')}")
                conn.close()
                return False

            # Verificar si ya existe (por número de nota Y código de producto)
            cursor.execute(
                'SELECT id FROM notas_credito WHERE numero_nota = ? AND codigo_producto = ?',
                (numero_nota, codigo_producto)
            )

            if cursor.fetchone():
                logger.info(f"Nota crédito {numero_nota} - Producto {codigo_producto[:30]}... ya existe en la BD")
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

            logger.info(f"Nota crédito registrada: {numero_nota} - Cliente: {nit_cliente} - "
                       f"Producto: {codigo_producto[:30]}... - Valor: ${valor_total:,.2f} - Tipo: {tipo_inventario}")

            return True

        except Exception as e:
            logger.error(f"Error al registrar nota crédito: {e}")
            return False
    
    def obtener_notas_pendientes(self, nit_cliente: str, codigo_producto: str) -> List[Dict]:
        """
        Obtiene todas las notas crédito pendientes para un cliente y producto específico
        
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
        Aplica una nota crédito a una factura si cumple las condiciones
        
        Args:
            nota: Datos de la nota crédito (desde BD)
            factura: Datos de la factura (transformada)
            
        Returns:
            Diccionario con información de la aplicación o None si no se pudo aplicar
        """
        try:
            # Validar que cliente y producto coincidan
            if nota['nit_cliente'] != factura['nit_comprador']:
                return None
            
            if nota['codigo_producto'] != factura.get('codigo_producto_api', ''):
                return None
            
            # Calcular cuánto se puede aplicar
            valor_factura = factura['valor_total']
            cantidad_factura = factura['cantidad_original']
            
            saldo_nota = nota['saldo_pendiente']
            cantidad_nota = nota['cantidad_pendiente']
            
            # Determinar el monto a aplicar (el menor entre saldo nota y valor factura)
            valor_aplicar = min(saldo_nota, valor_factura)
            
            # Calcular proporción de cantidad
            if valor_factura > 0:
                proporcion = valor_aplicar / valor_factura
                cantidad_aplicar = min(cantidad_nota, cantidad_factura * proporcion)
            else:
                cantidad_aplicar = 0
            
            # Validar que no supere los límites
            if valor_aplicar <= 0 or cantidad_aplicar <= 0:
                return None
            
            # Registrar aplicación en la BD
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insertar aplicación
            cursor.execute('''
                INSERT INTO aplicaciones_notas
                (id_nota, numero_nota, numero_factura, fecha_factura,
                 nit_cliente, codigo_producto, valor_aplicado, cantidad_aplicada)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nota['id'], nota['numero_nota'], factura['numero_factura'],
                  factura['fecha_factura'], nota['nit_cliente'], 
                  nota['codigo_producto'], valor_aplicar, cantidad_aplicar))
            
            # Actualizar saldos de la nota
            nuevo_saldo = nota['saldo_pendiente'] - valor_aplicar
            nueva_cantidad = nota['cantidad_pendiente'] - cantidad_aplicar
            
            estado = 'APLICADA' if nuevo_saldo <= 0.01 else 'PENDIENTE'
            
            cursor.execute('''
                UPDATE notas_credito
                SET saldo_pendiente = ?,
                    cantidad_pendiente = ?,
                    estado = ?,
                    fecha_aplicacion_completa = ?
                WHERE id = ?
            ''', (nuevo_saldo, nueva_cantidad, estado, 
                  datetime.now() if estado == 'APLICADA' else None,
                  nota['id']))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Nota {nota['numero_nota']} aplicada a factura {factura['numero_factura']}: "
                       f"${valor_aplicar:,.2f} de ${saldo_nota:,.2f}")
            
            return {
                'numero_nota': nota['numero_nota'],
                'numero_factura': factura['numero_factura'],
                'valor_aplicado': valor_aplicar,
                'cantidad_aplicada': cantidad_aplicar,
                'saldo_restante': nuevo_saldo,
                'estado': estado
            }
            
        except Exception as e:
            logger.error(f"Error al aplicar nota a factura: {e}")
            return None
    
    def procesar_notas_para_facturas(self, facturas: List[Dict]) -> List[Dict]:
        """
        Procesa la aplicación de notas crédito pendientes a un lote de facturas
        
        Args:
            facturas: Lista de facturas transformadas
            
        Returns:
            Lista de aplicaciones realizadas
        """
        aplicaciones = []
        
        for factura in facturas:
            # Obtener notas pendientes para este cliente y producto
            notas_pendientes = self.obtener_notas_pendientes(
                factura['nit_comprador'],
                factura.get('codigo_producto_api', '')
            )
            
            # Intentar aplicar cada nota pendiente
            for nota in notas_pendientes:
                aplicacion = self.aplicar_nota_a_factura(nota, factura)
                
                if aplicacion:
                    aplicaciones.append(aplicacion)
                    
                    # Si la nota se aplicó completamente, pasar a la siguiente nota
                    if aplicacion['estado'] == 'APLICADA':
                        logger.info(f"Nota {aplicacion['numero_nota']} aplicada completamente")
        
        logger.info(f"Se realizaron {len(aplicaciones)} aplicaciones de notas crédito")
        return aplicaciones
    
    def obtener_resumen_notas(self) -> Dict:
        """
        Obtiene un resumen del estado de las notas crédito
        
        Returns:
            Diccionario con estadísticas de notas crédito
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de notas pendientes
            cursor.execute('''
                SELECT COUNT(*), SUM(saldo_pendiente)
                FROM notas_credito
                WHERE estado = 'PENDIENTE'
            ''')
            pendientes, saldo_pendiente = cursor.fetchone()
            
            # Total de notas aplicadas
            cursor.execute('''
                SELECT COUNT(*)
                FROM notas_credito
                WHERE estado = 'APLICADA'
            ''')
            aplicadas = cursor.fetchone()[0]
            
            # Total de aplicaciones realizadas
            cursor.execute('''
                SELECT COUNT(*), SUM(valor_aplicado)
                FROM aplicaciones_notas
            ''')
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
            logger.error(f"Error al obtener resumen de notas: {e}")
            return {}
    
    def obtener_historial_nota(self, numero_nota: str) -> List[Dict]:
        """
        Obtiene el historial de aplicaciones de una nota específica
        
        Args:
            numero_nota: Número de la nota crédito
            
        Returns:
            Lista de aplicaciones realizadas
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
            logger.error(f"Error al obtener historial de nota: {e}")
            return []
    
    def registrar_factura_rechazada(self, factura: Dict, razon_rechazo: str) -> bool:
        """
        Registra una factura rechazada en la base de datos para auditoría
        
        Args:
            factura: Datos de la factura desde la API
            razon_rechazo: Razón por la cual fue rechazada
            
        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extraer datos
            prefijo = str(factura.get('f_prefijo', '')).strip()
            nrodocto = factura.get('f_nrodocto', '')
            numero_factura = f"{prefijo}{nrodocto}"
            
            fecha_str = factura.get('f_fecha', '')
            fecha_factura = None
            if fecha_str:
                try:
                    fecha_factura = datetime.fromisoformat(str(fecha_str).replace('T00:00:00', '')).date()
                except:
                    fecha_factura = datetime.now().date()
            else:
                fecha_factura = datetime.now().date()
            
            nit_cliente = str(factura.get('f_cliente_desp', '')).strip()
            nombre_cliente = str(factura.get('f_cliente_fact_razon_soc', '')).strip()
            codigo_producto = str(factura.get('f_cod_item', '')).strip()
            nombre_producto = str(factura.get('f_desc_item', '')).strip()
            tipo_inventario = str(factura.get('f_cod_tipo_inv', '')).strip()
            valor_total = float(factura.get('f_valor_subtotal_local', 0.0) or 0.0)
            
            # Insertar factura rechazada
            cursor.execute('''
                INSERT INTO facturas_rechazadas
                (numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                 codigo_producto, nombre_producto, tipo_inventario, valor_total, razon_rechazo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                  codigo_producto, nombre_producto, tipo_inventario, valor_total, razon_rechazo))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Factura rechazada registrada: {numero_factura} - {razon_rechazo}")
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar factura rechazada: {e}")
            return False

    def registrar_factura_valida(self, factura: Dict) -> bool:
        """
        Registra una factura válida en la base de datos

        Args:
            factura: Datos de la factura transformada (ya procesada por ExcelProcessor)

        Returns:
            True si se registró correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Extraer datos de la factura transformada
            numero_factura = str(factura.get('Nro factura', '')).strip()

            # Parsear fecha (puede venir como string o datetime)
            fecha_factura = factura.get('Fecha factura')
            if isinstance(fecha_factura, str):
                try:
                    # Intentar varios formatos de fecha
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            fecha_factura = datetime.strptime(fecha_factura, fmt).date()
                            break
                        except:
                            continue
                except:
                    fecha_factura = datetime.now().date()
            elif hasattr(fecha_factura, 'date'):
                fecha_factura = fecha_factura.date()
            else:
                fecha_factura = datetime.now().date()

            nit_cliente = str(factura.get('NIT Cliente', '')).strip()
            nombre_cliente = str(factura.get('Razón social', '')).strip()
            codigo_producto = str(factura.get('Código producto', '')).strip()
            nombre_producto = str(factura.get('Nombre producto', '')).strip()
            tipo_inventario = str(factura.get('Tipo inventario', '')).strip()

            valor_total = float(factura.get('Vr subtotal', 0.0) or 0.0)
            cantidad = float(factura.get('Cantidad', 0.0) or 0.0)
            valor_unitario = float(factura.get('Vr unitario', 0.0) or 0.0)

            # Insertar o actualizar factura válida
            cursor.execute('''
                INSERT INTO facturas
                (numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                 codigo_producto, nombre_producto, tipo_inventario,
                 valor_total, cantidad, valor_unitario, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PROCESADA')
                ON CONFLICT(numero_factura, codigo_producto) DO UPDATE SET
                    fecha_factura = excluded.fecha_factura,
                    valor_total = excluded.valor_total,
                    cantidad = excluded.cantidad,
                    valor_unitario = excluded.valor_unitario
            ''', (numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                  codigo_producto, nombre_producto, tipo_inventario,
                  valor_total, cantidad, valor_unitario))

            conn.commit()
            conn.close()

            logger.debug(f"Factura válida registrada: {numero_factura}")
            return True

        except Exception as e:
            logger.error(f"Error al registrar factura válida: {e}")
            import traceback
            traceback.print_exc()
            return False

    def actualizar_factura_con_nota(self, numero_factura: str, codigo_producto: str,
                                    valor_aplicado: float, cantidad_aplicada: float) -> bool:
        """
        Actualiza una factura marcándola como que tiene nota de crédito aplicada

        Args:
            numero_factura: Número de factura
            codigo_producto: Código del producto
            valor_aplicado: Valor de la nota aplicada
            cantidad_aplicada: Cantidad de la nota aplicada

        Returns:
            True si se actualizó correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE facturas
                SET tiene_nota_credito = 1,
                    valor_nota_aplicada = valor_nota_aplicada + ?,
                    cantidad_nota_aplicada = cantidad_nota_aplicada + ?
                WHERE numero_factura = ? AND codigo_producto = ?
            ''', (valor_aplicado, cantidad_aplicada, numero_factura, codigo_producto))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error al actualizar factura con nota: {e}")
            return False

    def registrar_tipo_inventario(self, codigo_tipo: str, descripcion: str = None, es_excluido: bool = False) -> bool:
        """
        Registra o actualiza un tipo de inventario detectado
        
        Args:
            codigo_tipo: Código del tipo de inventario
            descripcion: Descripción del tipo (opcional)
            es_excluido: Si es un tipo excluido
            
        Returns:
            True si se registró/actualizó correctamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si existe
            cursor.execute(
                'SELECT id, total_facturas FROM tipos_inventario_detectados WHERE codigo_tipo = ?',
                (codigo_tipo,)
            )
            
            resultado = cursor.fetchone()
            
            if resultado:
                # Actualizar existente
                id_tipo, total_actual = resultado
                cursor.execute('''
                    UPDATE tipos_inventario_detectados
                    SET ultima_deteccion = CURRENT_TIMESTAMP,
                        total_facturas = ?,
                        descripcion = COALESCE(?, descripcion)
                    WHERE id = ?
                ''', (total_actual + 1, descripcion, id_tipo))
            else:
                # Insertar nuevo
                cursor.execute('''
                    INSERT INTO tipos_inventario_detectados
                    (codigo_tipo, descripcion, es_excluido)
                    VALUES (?, ?, ?)
                ''', (codigo_tipo, descripcion, 1 if es_excluido else 0))
                
                logger.info(f"Nuevo tipo de inventario detectado: {codigo_tipo}")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error al registrar tipo de inventario: {e}")
            return False
    
    def obtener_tipos_inventario_nuevos(self, dias: int = 30) -> List[Dict]:
        """
        Obtiene tipos de inventario detectados recientemente que no están en la lista de excluidos
        
        Args:
            dias: Número de días hacia atrás para considerar "nuevo"
            
        Returns:
            Lista de tipos de inventario nuevos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT * FROM tipos_inventario_detectados
                WHERE primera_deteccion >= ?
                AND es_excluido = 0
                ORDER BY total_facturas DESC, primera_deteccion DESC
            ''', (fecha_limite,))
            
            tipos = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return tipos
            
        except Exception as e:
            logger.error(f"Error al obtener tipos nuevos: {e}")
            return []
    
    def obtener_resumen_rechazos(self, dias: int = 7) -> Dict:
        """
        Obtiene un resumen de facturas rechazadas en los últimos días
        
        Args:
            dias: Número de días hacia atrás
            
        Returns:
            Diccionario con estadísticas de rechazos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
            
            # Total de rechazos
            cursor.execute('''
                SELECT COUNT(*), SUM(valor_total)
                FROM facturas_rechazadas
                WHERE fecha_registro >= ?
            ''', (fecha_limite,))
            total_rechazos, valor_total = cursor.fetchone()
            
            # Rechazos por razón
            cursor.execute('''
                SELECT razon_rechazo, COUNT(*), SUM(valor_total)
                FROM facturas_rechazadas
                WHERE fecha_registro >= ?
                GROUP BY razon_rechazo
                ORDER BY COUNT(*) DESC
            ''', (fecha_limite,))
            por_razon = [
                {'razon': row[0], 'cantidad': row[1], 'valor': row[2]}
                for row in cursor.fetchall()
            ]
            
            # Tipos más rechazados
            cursor.execute('''
                SELECT tipo_inventario, COUNT(*)
                FROM facturas_rechazadas
                WHERE fecha_registro >= ?
                AND razon_rechazo LIKE '%Tipo de inventario excluido%'
                GROUP BY tipo_inventario
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''', (fecha_limite,))
            tipos_mas_rechazados = [
                {'tipo': row[0], 'cantidad': row[1]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'total_rechazos': total_rechazos or 0,
                'valor_total_rechazado': valor_total or 0.0,
                'por_razon': por_razon,
                'tipos_mas_rechazados': tipos_mas_rechazados
            }
            
        except Exception as e:
            logger.error(f"Error al obtener resumen de rechazos: {e}")
            return {}
