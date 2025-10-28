"""
Módulo de Reglas de Negocio para Filtrado de Facturas
Contiene la lógica de validación y filtrado según criterios de negocio
"""
import logging
from typing import List, Dict, Tuple

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
    
    # Monto mínimo para procesar una factura (en pesos colombianos)
    MONTO_MINIMO = 498000.0
    
    def __init__(self):
        """Inicializa el validador de reglas de negocio"""
        logger.info(f"BusinessRulesValidator inicializado con {len(self.TIPOS_INVENTARIO_EXCLUIDOS)} tipos excluidos")
    
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
    
    def tipo_inventario_permitido(self, factura: Dict) -> bool:
        """
        Valida si el tipo de inventario de la factura está permitido
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            True si el tipo está permitido, False si está excluido
        """
        tipo_inventario = str(factura.get('f_cod_tipo_inv', '')).strip().upper()
        
        if not tipo_inventario:
            logger.warning(f"Factura sin tipo de inventario: {factura.get('f_nrodocto')}")
            return True  # Permitir si no tiene tipo definido
        
        return tipo_inventario not in self.TIPOS_INVENTARIO_EXCLUIDOS
    
    def cumple_monto_minimo(self, factura: Dict) -> bool:
        """
        Valida si el valor total de la factura cumple con el monto mínimo
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            True si cumple el monto mínimo, False en caso contrario
        """
        valor_total = factura.get('f_valor_subtotal_local', 0.0)
        if valor_total is None:
            valor_total = 0.0
        
        valor_total = float(valor_total)
        
        return valor_total >= self.MONTO_MINIMO
    
    def validar_factura(self, factura: Dict) -> Tuple[bool, str]:
        """
        Valida si una factura cumple con todas las reglas de negocio
        
        Args:
            factura: Datos de la factura desde la API
            
        Returns:
            Tupla (es_valida, razon_rechazo)
            - es_valida: True si la factura cumple todas las reglas
            - razon_rechazo: Descripción de por qué fue rechazada (vacío si es válida)
        """
        # Las notas crédito se procesan por separado
        if self.es_nota_credito(factura):
            return True, ""
        
        # Validar tipo de inventario
        if not self.tipo_inventario_permitido(factura):
            tipo_inv = factura.get('f_cod_tipo_inv', 'N/A')
            return False, f"Tipo de inventario excluido: {tipo_inv}"
        
        # Validar monto mínimo
        if not self.cumple_monto_minimo(factura):
            valor = factura.get('f_valor_subtotal_local', 0)
            return False, f"Valor total ${valor:,.2f} no cumple monto mínimo ${self.MONTO_MINIMO:,.2f}"
        
        return True, ""
    
    def filtrar_facturas(self, facturas: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Filtra facturas según reglas de negocio y separa notas crédito
        
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
        
        for factura in facturas:
            # Separar notas crédito
            if self.es_nota_credito(factura):
                notas_credito.append(factura)
                continue
            
            # Validar factura
            es_valida, razon = self.validar_factura(factura)
            
            if es_valida:
                facturas_validas.append(factura)
            else:
                factura_info = {
                    'factura': factura,
                    'razon_rechazo': razon
                }
                facturas_rechazadas.append(factura_info)
                
                # Log de rechazo
                numero = f"{factura.get('f_prefijo', '')}{factura.get('f_nrodocto', '')}"
                logger.info(f"Factura rechazada {numero}: {razon}")
        
        logger.info(f"Filtrado completado: {len(facturas_validas)} válidas, "
                   f"{len(notas_credito)} notas crédito, {len(facturas_rechazadas)} rechazadas")
        
        return facturas_validas, notas_credito, facturas_rechazadas
