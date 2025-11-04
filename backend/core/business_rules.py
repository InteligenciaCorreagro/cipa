# src/business_rules.py

"""
Módulo de Reglas de Negocio para Filtrado de Facturas
Contiene la lógica de validación y filtrado según criterios de negocio
"""
import logging
from typing import List, Dict, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class BusinessRulesValidator:
    """Valida y filtra facturas según reglas de negocio establecidas"""
    
    # Tipos de inventario que NO deben registrarse
    TIPOS_INVENTARIO_EXCLUIDOS = {
        'VSMENORCC',
        'VS4205101',
        'INVMEDICAD',
        'INV1430051',
        'VS42100501',
        'VS420515',
        'VS42051003',
        'VS420510',
        'VSMENOR',
        'INVFLETEPT',
        'VSMENOR5%',
        'VS42505090',
        'INVFLETGEN',
        'INV144542',
        'INV144554',
        'VSMAY-MECC',
        'VSMAY-MECP',
        'VSMAY-GEN',
        'DESCESPEC',
        'DESCUENTO',
        'INV144562',
        'VS425050',
        'VS41200822',
        'INV1460',
        'VS41200819'
    }
    
    # Monto mínimo para procesar una factura COMPLETA (en pesos colombianos)
    MONTO_MINIMO = 498000.0
    
    def __init__(self):
        """Inicializa el validador de reglas de negocio"""
        logger.info(f"BusinessRulesValidator inicializado con {len(self.TIPOS_INVENTARIO_EXCLUIDOS)} tipos excluidos")
        logger.info(f"Monto mínimo por factura completa: ${self.MONTO_MINIMO:,.2f}")
    
    def obtener_numero_factura_completo(self, factura: Dict) -> str:
        """
        Obtiene el número completo de la factura (prefijo + número)
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            Número completo de la factura
        """
        prefijo = str(factura.get('f_prefijo', '')).strip()
        numero = str(factura.get('f_nrodocto', '')).strip()
        return f"{prefijo}{numero}"
    
    def es_nota_credito(self, factura: Dict) -> bool:
        """
        Determina si una factura es una nota crédito basándose en el prefijo 'N'
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            True si es nota crédito, False en caso contrario
        """
        prefijo = str(factura.get('f_prefijo', '')).strip().upper()
        return prefijo.startswith('N')
    
    def _obtener_tipo_inventario_normalizado(self, factura: Dict) -> str:
        """
        Obtiene el tipo de inventario normalizado de una factura.
        
        CRÍTICO: Maneja múltiples nombres de campo y normaliza espacios en blanco.
        La API puede enviar el tipo de inventario en diferentes campos:
        - f_cod_tipo_inv
        - f_tipo_inv
        
        Además, la API puede enviar valores con espacios en blanco que deben ser
        normalizados antes de comparar con la lista de excluidos.
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            Tipo de inventario normalizado (sin espacios, mayúsculas) o cadena vacía
        """
        # Intentar obtener de múltiples campos posibles
        tipo_inventario_raw = (
            factura.get('f_cod_tipo_inv') or 
            factura.get('f_tipo_inv') or 
            ''
        )
        
        # Normalizar: convertir a string, quitar espacios, mayúsculas
        tipo_inventario = str(tipo_inventario_raw).strip().upper()
        
        # Log de auditoría si se detectan espacios (problema común de la API)
        if tipo_inventario_raw and str(tipo_inventario_raw) != str(tipo_inventario_raw).strip():
            logger.warning(
                f"⚠️ Tipo de inventario con espacios detectado: '{tipo_inventario_raw}' "
                f"→ normalizado a: '{tipo_inventario}' "
                f"(Factura: {self.obtener_numero_factura_completo(factura)})"
            )
        
        return tipo_inventario
    
    def tipo_inventario_permitido(self, factura: Dict) -> bool:
        """
        Valida si el tipo de inventario de la factura está permitido
        
        IMPORTANTE: Normaliza el tipo de inventario removiendo espacios y convirtiendo a mayúsculas
        antes de comparar con la lista de excluidos.
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            True si el tipo está permitido, False si está excluido
        """
        tipo_inventario = self._obtener_tipo_inventario_normalizado(factura)
        
        if not tipo_inventario:
            logger.warning(f"Factura sin tipo de inventario: {self.obtener_numero_factura_completo(factura)}")
            return True  # Permitir si no tiene tipo definido
        
        # Comparar con lista de excluidos (ya normalizada en el conjunto)
        es_permitido = tipo_inventario not in self.TIPOS_INVENTARIO_EXCLUIDOS
        
        if not es_permitido:
            logger.debug(f"Tipo de inventario excluido detectado: '{tipo_inventario}' "
                        f"(Factura: {self.obtener_numero_factura_completo(factura)})")
        
        return es_permitido
    
    def agrupar_por_factura(self, facturas: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Agrupa las líneas por número de factura completo
        
        Args:
            facturas: Lista de líneas de facturas desde la API
            
        Returns:
            Diccionario donde la clave es el número de factura y el valor es la lista de líneas
        """
        facturas_agrupadas = defaultdict(list)
        
        for factura in facturas:
            numero_completo = self.obtener_numero_factura_completo(factura)
            facturas_agrupadas[numero_completo].append(factura)
        
        return facturas_agrupadas
    
    def calcular_total_factura(self, lineas: List[Dict]) -> float:
        """
        Calcula el valor total de una factura sumando todas sus líneas
        
        Args:
            lineas: Lista de líneas que pertenecen a la misma factura
            
        Returns:
            Valor total de la factura
        """
        total = 0.0
        for linea in lineas:
            valor = linea.get('f_valor_subtotal_local', 0.0)
            if valor is None:
                valor = 0.0
            total += float(valor)
        
        return total
    
    def filtrar_facturas(self, facturas: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Filtra facturas según reglas de negocio y separa notas crédito
        
        IMPORTANTE: La validación de monto mínimo se aplica a la FACTURA COMPLETA,
        no a cada línea individual. Si una factura tiene múltiples líneas, se suman
        todas y se valida el total.
        
        Args:
            facturas: Lista de facturas desde la API
            
        Returns:
            Tupla con tres listas:
            - facturas_validas: Facturas que cumplen todas las reglas
            - notas_credito: Notas crédito identificadas
            - facturas_rechazadas: Facturas rechazadas con razón
        """
        facturas_validas = []
        notas_credito = []
        facturas_rechazadas = []
        
        # Separar notas crédito primero y validar tipo de inventario
        facturas_regulares = []
        for factura in facturas:
            if self.es_nota_credito(factura):
                # Validar tipo de inventario en notas de crédito
                if not self.tipo_inventario_permitido(factura):
                    tipo_inv = self._obtener_tipo_inventario_normalizado(factura)
                    razon = f"Nota crédito con tipo de inventario excluido: {tipo_inv}"
                    facturas_rechazadas.append({
                        'factura': factura,
                        'razon_rechazo': razon
                    })
                    logger.info(f"Nota crédito rechazada por tipo inventario: {factura.get('f_prefijo', '')}{factura.get('f_nrodocto', '')} - Tipo: {tipo_inv}")
                else:
                    notas_credito.append(factura)
            else:
                facturas_regulares.append(factura)

        logger.info(f"Total documentos: {len(facturas)} ({len(facturas_regulares)} facturas, {len(notas_credito)} notas crédito válidas, {len(facturas_rechazadas)} documentos rechazados)")
        
        # Agrupar facturas regulares por número completo
        facturas_agrupadas = self.agrupar_por_factura(facturas_regulares)
        
        logger.info(f"Facturas únicas a validar: {len(facturas_agrupadas)}")
        
        # Procesar cada factura completa
        for numero_factura, lineas in facturas_agrupadas.items():
            # Calcular total de la factura
            total_factura = self.calcular_total_factura(lineas)
            
            # Validar monto mínimo a nivel de factura completa
            if total_factura < self.MONTO_MINIMO:
                # Rechazar TODAS las líneas de esta factura
                razon = f"Valor total de factura ${total_factura:,.2f} no cumple monto mínimo ${self.MONTO_MINIMO:,.2f}"
                
                for linea in lineas:
                    facturas_rechazadas.append({
                        'factura': linea,
                        'razon_rechazo': razon
                    })
                
                logger.info(f"Factura rechazada por monto: {numero_factura} - Total: ${total_factura:,.2f} ({len(lineas)} líneas)")
                continue
            
            # Si cumple el monto mínimo, validar cada línea por tipo de inventario
            lineas_validas_factura = []
            lineas_rechazadas_factura = []
            
            for linea in lineas:
                if not self.tipo_inventario_permitido(linea):
                    tipo_inv = self._obtener_tipo_inventario_normalizado(linea)
                    razon = f"Tipo de inventario excluido: {tipo_inv}"
                    lineas_rechazadas_factura.append({
                        'factura': linea,
                        'razon_rechazo': razon
                    })
                else:
                    lineas_validas_factura.append(linea)
            
            # Si TODAS las líneas de la factura fueron rechazadas por tipo de inventario,
            # registrar como rechazo
            if len(lineas_validas_factura) == 0 and len(lineas_rechazadas_factura) > 0:
                facturas_rechazadas.extend(lineas_rechazadas_factura)
                logger.info(f"Factura rechazada por tipo inventario: {numero_factura} - {len(lineas)} líneas")
            
            # Si al menos una línea es válida, procesar toda la factura
            # (esto incluye líneas mixtas: algunas válidas, algunas no)
            elif len(lineas_validas_factura) > 0:
                # DECISIÓN DE DISEÑO: Si una factura tiene líneas mixtas (algunas válidas, algunas excluidas),
                # hay dos opciones:
                # 
                # OPCIÓN A: Procesar solo las líneas válidas
                facturas_validas.extend(lineas_validas_factura)
                
                # OPCIÓN B: Rechazar toda la factura si tiene al menos una línea excluida
                # if len(lineas_rechazadas_factura) > 0:
                #     razon = "Factura contiene líneas con tipos de inventario excluidos"
                #     for linea in lineas:
                #         facturas_rechazadas.append({
                #             'factura': linea,
                #             'razon_rechazo': razon
                #         })
                #     logger.info(f"Factura rechazada por líneas mixtas: {numero_factura}")
                # else:
                #     facturas_validas.extend(lineas_validas_factura)
                
                # Actualmente implementado: OPCIÓN A (procesar líneas válidas)
                if len(lineas_rechazadas_factura) > 0:
                    facturas_rechazadas.extend(lineas_rechazadas_factura)
                    logger.info(f"Factura {numero_factura}: {len(lineas_validas_factura)} líneas válidas, "
                              f"{len(lineas_rechazadas_factura)} líneas rechazadas por tipo inventario")
                else:
                    logger.info(f"Factura válida: {numero_factura} - Total: ${total_factura:,.2f} ({len(lineas)} líneas)")
        
        logger.info(f"\nRESUMEN FILTRADO:")
        logger.info(f"  - Líneas válidas: {len(facturas_validas)}")
        logger.info(f"  - Notas crédito: {len(notas_credito)}")
        logger.info(f"  - Líneas rechazadas: {len(facturas_rechazadas)}")
        
        return facturas_validas, notas_credito, facturas_rechazadas