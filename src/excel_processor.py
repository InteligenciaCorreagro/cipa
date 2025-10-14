from openpyxl import Workbook
from openpyxl.styles import numbers, Font, PatternFill, Alignment
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Procesa y genera archivos Excel con datos de facturas"""
    
    def __init__(self, template_path: str = None):
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
        if 'IVA 5%' in grupo_impositivo or '5%' in grupo_impositivo:
            return '5'
        elif 'IVA 19%' in grupo_impositivo or '19%' in grupo_impositivo:
            return '19'
        elif 'IVA 0%' in grupo_impositivo or 'EXCLUIDO' in grupo_impositivo:
            return '0'
        return '0'
    
    def _extraer_ciudad(self, ciudad_raw: str) -> str:
        """Extrae el nombre de la ciudad del formato '088-Bello'"""
        if '-' in ciudad_raw:
            return ciudad_raw.split('-')[1].strip()
        return ciudad_raw.strip()
    
    def _crear_encabezados(self, ws):
        """Crea los encabezados del Excel con formato"""
        encabezados = [
            'N° Factura', 'Nombre Producto', 'Codigo Subyacente', 'Unidad Medida en Kg,Un,Lt',
            'Cantidad (5 decimales - separdor coma)', 'Precio Unitario (5 decimales - separdor coma)',
            'Fecha Factura Año-Mes-Dia', 'Fecha Pago Año-Mes-Dia', 'Nit Comprador (Existente)',
            'Nombre Comprador', 'Nit Vendedor (Existente)', 'Nombre Vendedor', 'Principal V,C',
            'Municipio (Nombre Exacto de la Ciudad)', 'Iva (N°%)', 'Descripción', 'Activa Factura',
            'Activa Bodega', 'Incentivo', 'Cantidad Original (5 decimales - separdor coma)', 'Moneda (1,2,3)'
        ]
        
        # Estilo de encabezado
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        for col_num, header in enumerate(encabezados, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        # Ajustar ancho de columnas
        column_widths = [15, 40, 15, 20, 20, 20, 18, 18, 20, 35, 20, 35, 12, 30, 10, 30, 15, 15, 15, 25, 12]
        for col_num, width in enumerate(column_widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=col_num).column_letter].width = width
    
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
            # Crear nuevo workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Facturas"
            
            # Crear encabezados
            self._crear_encabezados(ws)
            
            logger.info(f"Procesando {len(facturas)} facturas")
            
            # Agregar datos
            for idx, factura in enumerate(facturas, start=2):
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