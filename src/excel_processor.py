from openpyxl import load_workbook
from openpyxl.styles import numbers
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Procesa y genera archivos Excel con datos de facturas"""
    
    # Mapeo de columnas según tu plantilla
    COLUMN_MAPPING = {
        'A': 'numero_factura',      # N° Factura
        'B': 'nombre_producto',      # Nombre Producto
        'C': 'codigo_subyacente',    # Codigo Subyacente
        'D': 'unidad_medida',        # Unidad Medida
        'E': 'cantidad',             # Cantidad
        'F': 'precio_unitario',      # Precio Unitario
        'G': 'fecha_factura',        # Fecha Factura
        'H': 'fecha_pago',           # Fecha Pago
        'I': 'nit_comprador',        # Nit Comprador
        'J': 'nombre_comprador',     # Nombre Comprador
        'K': 'nit_vendedor',         # Nit Vendedor
        'L': 'nombre_vendedor',      # Nombre Vendedor
        'M': 'principal',            # Principal V,C
        'N': 'municipio',            # Municipio
        'O': 'iva',                  # Iva
        'P': 'descripcion',          # Descripción
        'Q': 'activa_factura',       # Activa Factura
        'R': 'activa_bodega',        # Activa Bodega
        'S': 'incentivo',            # Incentivo
        'T': 'cantidad_original',    # Cantidad Original
        'U': 'moneda'                # Moneda
    }
    
    def __init__(self, template_path: str):
        self.template_path = template_path
    
    def transformar_factura(self, factura: Dict) -> Dict:
        """
        Transforma una factura del formato API al formato Excel
        
        Args:
            factura: Datos de factura en formato JSON de la API
            
        Returns:
            Diccionario con datos transformados
        """
        # Extraer número de factura completo
        numero_factura = f"{factura.get('f_prefijo', '')}{factura.get('f_nrodocto', '')}"
        
        # Procesar fecha
        fecha_str = factura.get('f_fecha', '')
        fecha_factura = datetime.fromisoformat(fecha_str.replace('T00:00:00', '')) if fecha_str else None
        
        # Extraer IVA del grupo impositivo
        grupo_impositivo = factura.get('f_desc_grupo_impositivo', '')
        iva = self._extraer_iva(grupo_impositivo)
        
        # Extraer ciudad del campo que contiene código-nombre
        ciudad = self._extraer_ciudad(factura.get('f_ciudad_punto_envio', ''))
        
        return {
            'numero_factura': numero_factura,
            'nombre_producto': factura.get('f_desc_item', ''),
            'codigo_subyacente': factura.get('f_tipo_inv', '').strip(),
            'unidad_medida': factura.get('f_um_inv_desc', ''),
            'cantidad': factura.get('f_cant_base', 0.0),
            'precio_unitario': factura.get('f_precio_unit_docto', 0.0),
            'fecha_factura': fecha_factura,
            'fecha_pago': None,  # Calcular según condición de pago si es necesario
            'nit_comprador': factura.get('f_cliente_desp', '').strip(),
            'nombre_comprador': factura.get('f_cliente_fact_razon_soc', ''),
            'nit_vendedor': '',  # No está en el JSON proporcionado
            'nombre_vendedor': '',  # No está en el JSON proporcionado
            'principal': 'V',  # Valor por defecto, ajustar según lógica de negocio
            'municipio': ciudad,
            'iva': iva,
            'descripcion': factura.get('f_desc_tipo_inv', ''),
            'activa_factura': 'SI',  # Valor por defecto
            'activa_bodega': 'SI',  # Valor por defecto
            'incentivo': '',
            'cantidad_original': factura.get('f_peso', 0.0),
            'moneda': '1'  # 1=Peso colombiano, ajustar según necesidad
        }
    
    def _extraer_iva(self, grupo_impositivo: str) -> str:
        """Extrae el porcentaje de IVA del grupo impositivo"""
        if 'IVA 5%' in grupo_impositivo:
            return '5'
        elif 'IVA 19%' in grupo_impositivo:
            return '19'
        elif 'IVA 0%' in grupo_impositivo or 'EXCLUIDO' in grupo_impositivo:
            return '0'
        return '0'
    
    def _extraer_ciudad(self, ciudad_raw: str) -> str:
        """Extrae el nombre de la ciudad del formato '088-Bello'"""
        if '-' in ciudad_raw:
            return ciudad_raw.split('-')[1].strip()
        return ciudad_raw.strip()
    
    def generar_excel(self, facturas: List[Dict], output_path: str) -> str:
        """
        Genera archivo Excel con las facturas
        
        Args:
            facturas: Lista de facturas transformadas
            output_path: Ruta donde guardar el archivo
            
        Returns:
            Ruta del archivo generado
        """
        try:
            # Cargar plantilla
            wb = load_workbook(self.template_path)
            ws = wb.active
            
            # Determinar fila inicial (asumiendo que row 1 es encabezado)
            start_row = 2
            
            logger.info(f"Procesando {len(facturas)} facturas")
            
            for idx, factura in enumerate(facturas, start=start_row):
                ws[f'A{idx}'] = factura['numero_factura']
                ws[f'B{idx}'] = factura['nombre_producto']
                ws[f'C{idx}'] = factura['codigo_subyacente']
                ws[f'D{idx}'] = factura['unidad_medida']
                
                # Cantidad con 5 decimales y separador coma
                ws[f'E{idx}'] = factura['cantidad']
                ws[f'E{idx}'].number_format = '#,##0.00000'
                
                # Precio unitario con 5 decimales
                ws[f'F{idx}'] = factura['precio_unitario']
                ws[f'F{idx}'].number_format = '#,##0.00000'
                
                # Fechas
                if factura['fecha_factura']:
                    ws[f'G{idx}'] = factura['fecha_factura']
                    ws[f'G{idx}'].number_format = 'YYYY-MM-DD'
                
                if factura['fecha_pago']:
                    ws[f'H{idx}'] = factura['fecha_pago']
                    ws[f'H{idx}'].number_format = 'YYYY-MM-DD'
                
                ws[f'I{idx}'] = factura['nit_comprador']
                ws[f'J{idx}'] = factura['nombre_comprador']
                ws[f'K{idx}'] = factura['nit_vendedor']
                ws[f'L{idx}'] = factura['nombre_vendedor']
                ws[f'M{idx}'] = factura['principal']
                ws[f'N{idx}'] = factura['municipio']
                ws[f'O{idx}'] = factura['iva']
                ws[f'P{idx}'] = factura['descripcion']
                ws[f'Q{idx}'] = factura['activa_factura']
                ws[f'R{idx}'] = factura['activa_bodega']
                ws[f'S{idx}'] = factura['incentivo']
                
                # Cantidad original
                ws[f'T{idx}'] = factura['cantidad_original']
                ws[f'T{idx}'].number_format = '#,##0.00000'
                
                ws[f'U{idx}'] = factura['moneda']
            
            # Guardar archivo
            wb.save(output_path)
            logger.info(f"Excel generado exitosamente: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error al generar Excel: {e}")
            raise