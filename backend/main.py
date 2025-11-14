import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from core.api_client import SiesaAPIClient
from core.excel_processor import ExcelProcessor
from core.email_sender import EmailSender
from core.business_rules import BusinessRulesValidator
from core.notas_credito_manager import NotasCreditoManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal del proceso con reglas de negocio y gestión de notas crédito"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Configuración
        CONNI_KEY = os.getenv('CONNI_KEY')
        CONNI_TOKEN = os.getenv('CONNI_TOKEN')
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
        EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
        DESTINATARIOS = os.getenv('DESTINATARIOS').split(',')
        TEMPLATE_PATH = os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')
        DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')
        
        # Validar configuración
        if not all([CONNI_KEY, CONNI_TOKEN, EMAIL_USERNAME, EMAIL_PASSWORD]):
            raise ValueError("Faltan variables de entorno requeridas")
        
        # Calcular fecha del día anterior
        fecha_reporte = datetime.now() - timedelta(days=1)
        logger.info(f"={'='*60}")
        logger.info(f"Iniciando proceso para: {fecha_reporte.strftime('%Y-%m-%d')}")
        logger.info(f"={'='*60}")
        
        # ============================================================
        # 1. OBTENER FACTURAS DE LA API
        # ============================================================
        api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
        facturas_raw = api_client.obtener_facturas(fecha_reporte)
        
        if not facturas_raw:
            logger.warning("No se encontraron facturas para la fecha especificada")
            return
        
        logger.info(f"Total de documentos obtenidos de la API: {len(facturas_raw)}")
        
        # ============================================================
        # 2. INICIALIZAR GESTOR DE NOTAS CRÉDITO
        # ============================================================
        notas_manager = NotasCreditoManager(DB_PATH)
        
        # ============================================================
        # 3. APLICAR REGLAS DE NEGOCIO Y SEPARAR NOTAS CRÉDITO
        # ============================================================
        validator = BusinessRulesValidator()
        facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(facturas_raw)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"RESULTADOS DEL FILTRADO:")
        logger.info(f"  - Facturas válidas: {len(facturas_validas)}")
        logger.info(f"  - Notas crédito: {len(notas_credito)}")
        logger.info(f"  - Facturas rechazadas: {len(facturas_rechazadas)}")
        logger.info(f"{'='*60}\n")
        
        # Log de facturas rechazadas para auditoría
        if facturas_rechazadas:
            logger.info("Detalle de facturas rechazadas:")
            for item in facturas_rechazadas:
                factura = item['factura']
                numero = f"{factura.get('f_prefijo', '')}{factura.get('f_nrodocto', '')}"
                valor = factura.get('f_valor_subtotal_local', 0)
                logger.info(f"  - {numero}: {item['razon_rechazo']} (Valor: ${valor:,.2f})")
                
                # Registrar en base de datos
                notas_manager.registrar_factura_rechazada(factura, item['razon_rechazo'])
        
        # Registrar todos los tipos de inventario detectados
        logger.info("\nRegistrando tipos de inventario detectados...")
        tipos_registrados = set()
        
        # Registrar tipos de facturas válidas
        for factura in facturas_validas:
            tipo_inv = str(factura.get('f_cod_tipo_inv', '')).strip()
            if tipo_inv and tipo_inv not in tipos_registrados:
                notas_manager.registrar_tipo_inventario(
                    tipo_inv,
                    factura.get('f_desc_tipo_inv', ''),
                    es_excluido=False
                )
                tipos_registrados.add(tipo_inv)
        
        # Registrar tipos de facturas rechazadas (marcados como excluidos)
        for item in facturas_rechazadas:
            factura = item['factura']
            tipo_inv = str(factura.get('f_cod_tipo_inv', '')).strip()
            if tipo_inv and tipo_inv not in tipos_registrados:
                notas_manager.registrar_tipo_inventario(
                    tipo_inv,
                    factura.get('f_desc_tipo_inv', ''),
                    es_excluido=True
                )
                tipos_registrados.add(tipo_inv)
        
        logger.info(f"Total de tipos de inventario únicos detectados: {len(tipos_registrados)}")
        
        # Detectar tipos de inventario nuevos
        tipos_nuevos = notas_manager.obtener_tipos_inventario_nuevos(dias=30)
        if tipos_nuevos:
            logger.warning(f"\n⚠️  TIPOS DE INVENTARIO NUEVOS DETECTADOS ({len(tipos_nuevos)}):")
            for tipo in tipos_nuevos:
                logger.warning(f"  - {tipo['codigo_tipo']}: {tipo['descripcion']} "
                             f"(Detectado {tipo['total_facturas']} veces)")
            logger.warning("  Considere agregar estos tipos a la lista de excluidos si es necesario")
        
        # ============================================================
        # 4. GESTIONAR NOTAS CRÉDITO
        # ============================================================
        # Registrar nuevas notas crédito en la base de datos
        if notas_credito:
            logger.info(f"\nRegistrando {len(notas_credito)} notas crédito...")
            notas_nuevas = 0
            for nota in notas_credito:
                if notas_manager.registrar_nota_credito(nota):
                    notas_nuevas += 1
            logger.info(f"Notas crédito nuevas registradas: {notas_nuevas}")
        
        # ============================================================
        # 5. TRANSFORMAR FACTURAS VÁLIDAS
        # ============================================================
        if not facturas_validas:
            logger.warning("No hay facturas válidas para procesar después del filtrado")
            
            # Mostrar resumen de notas y salir
            resumen = notas_manager.obtener_resumen_notas()
            logger.info(f"\nResumen de notas crédito:")
            logger.info(f"  - Notas pendientes: {resumen.get('notas_pendientes', 0)}")
            logger.info(f"  - Saldo pendiente: ${resumen.get('saldo_pendiente_total', 0):,.2f}")
            logger.info(f"  - Notas aplicadas: {resumen.get('notas_aplicadas', 0)}")
            return
        
        excel_processor = ExcelProcessor(TEMPLATE_PATH)
        facturas_transformadas = [
            excel_processor.transformar_factura(factura)
            for factura in facturas_validas
        ]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Facturas transformadas: {len(facturas_transformadas)}")
        logger.info(f"{'='*60}")

        # ============================================================
        # 6. REGISTRAR FACTURAS VÁLIDAS EN BASE DE DATOS
        # ============================================================
        logger.info("\nRegistrando facturas válidas en base de datos...")
        facturas_registradas = 0
        for factura in facturas_transformadas:
            if notas_manager.registrar_factura_valida(factura):
                facturas_registradas += 1
        logger.info(f"Facturas válidas registradas: {facturas_registradas}/{len(facturas_transformadas)}")

        # ============================================================
        # 7. APLICAR NOTAS CRÉDITO PENDIENTES A FACTURAS
        # ============================================================
        logger.info("\nProcesando aplicación de notas crédito pendientes...")
        aplicaciones = notas_manager.procesar_notas_para_facturas(facturas_transformadas)
        
        if aplicaciones:
            logger.info(f"\n{'='*60}")
            logger.info(f"APLICACIONES DE NOTAS CRÉDITO:")
            logger.info(f"  Total de aplicaciones realizadas: {len(aplicaciones)}")
            logger.info(f"{'='*60}")
            
            # Log detallado de aplicaciones
            for app in aplicaciones:
                logger.info(f"  - Nota {app['numero_nota']} -> Factura {app['numero_factura']}")
                logger.info(f"    Valor aplicado: ${app['valor_aplicado']:,.2f}")
                logger.info(f"    Cantidad aplicada: {app['cantidad_aplicada']:.5f}")
                logger.info(f"    Saldo restante nota: ${app['saldo_restante']:,.2f}")
                logger.info(f"    Estado: {app['estado']}")
        else:
            logger.info("No se realizaron aplicaciones de notas crédito en este lote")
        
        # ============================================================
        # 8. OBTENER RESUMEN DE NOTAS CRÉDITO
        # ============================================================
        resumen = notas_manager.obtener_resumen_notas()
        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMEN DE NOTAS CRÉDITO:")
        logger.info(f"  - Notas pendientes: {resumen.get('notas_pendientes', 0)}")
        logger.info(f"  - Saldo pendiente total: ${resumen.get('saldo_pendiente_total', 0):,.2f}")
        logger.info(f"  - Notas aplicadas (histórico): {resumen.get('notas_aplicadas', 0)}")
        logger.info(f"  - Total aplicaciones (histórico): {resumen.get('total_aplicaciones', 0)}")
        logger.info(f"  - Monto total aplicado (histórico): ${resumen.get('monto_total_aplicado', 0):,.2f}")
        logger.info(f"{'='*60}\n")
        
        # ============================================================
        # 9. GENERAR EXCEL CON FACTURAS PROCESADAS
        # ============================================================
        output_filename = f"facturas_{fecha_reporte.strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join('./output', output_filename)
        
        # Crear directorio output si no existe
        os.makedirs('./output', exist_ok=True)
        
        excel_processor.generar_excel(facturas_transformadas, output_path)
        
        # ============================================================
        # 10. GENERAR REPORTE DE FACTURAS RECHAZADAS
        # ============================================================
        if facturas_rechazadas:
            reporte_rechazadas_path = os.path.join(
                './output', 
                f"facturas_rechazadas_{fecha_reporte.strftime('%Y%m%d')}.txt"
            )
            
            with open(reporte_rechazadas_path, 'w', encoding='utf-8') as f:
                f.write(f"REPORTE DE FACTURAS RECHAZADAS\n")
                f.write(f"Fecha: {fecha_reporte.strftime('%Y-%m-%d')}\n")
                f.write(f"{'='*80}\n\n")
                
                f.write(f"Total de facturas rechazadas: {len(facturas_rechazadas)}\n\n")
                
                for item in facturas_rechazadas:
                    factura = item['factura']
                    numero = f"{factura.get('f_prefijo', '')}{factura.get('f_nrodocto', '')}"
                    cliente = factura.get('f_cliente_fact_razon_soc', 'N/A')
                    producto = factura.get('f_desc_item', 'N/A')
                    valor = factura.get('f_valor_subtotal_local', 0)
                    tipo_inv = factura.get('f_cod_tipo_inv', 'N/A')
                    
                    f.write(f"Factura: {numero}\n")
                    f.write(f"Cliente: {cliente}\n")
                    f.write(f"Producto: {producto}\n")
                    f.write(f"Tipo Inventario: {tipo_inv}\n")
                    f.write(f"Valor: ${valor:,.2f}\n")
                    f.write(f"Razón de rechazo: {item['razon_rechazo']}\n")
                    f.write(f"-" * 80 + "\n\n")
            
            logger.info(f"Reporte de facturas rechazadas generado: {reporte_rechazadas_path}")
        
        # ============================================================
        # 9. GENERAR REPORTE DE NOTAS CRÉDITO
        # ============================================================
        reporte_notas_path = os.path.join(
            './output',
            f"reporte_notas_credito_{fecha_reporte.strftime('%Y%m%d')}.txt"
        )
        
        with open(reporte_notas_path, 'w', encoding='utf-8') as f:
            f.write(f"REPORTE DE NOTAS CRÉDITO\n")
            f.write(f"Fecha: {fecha_reporte.strftime('%Y-%m-%d')}\n")
            f.write(f"{'='*80}\n\n")
            
            f.write(f"RESUMEN:\n")
            f.write(f"  - Notas pendientes: {resumen.get('notas_pendientes', 0)}\n")
            f.write(f"  - Saldo pendiente total: ${resumen.get('saldo_pendiente_total', 0):,.2f}\n")
            f.write(f"  - Notas aplicadas: {resumen.get('notas_aplicadas', 0)}\n")
            f.write(f"  - Total aplicaciones: {resumen.get('total_aplicaciones', 0)}\n")
            f.write(f"  - Monto total aplicado: ${resumen.get('monto_total_aplicado', 0):,.2f}\n\n")
            
            if aplicaciones:
                f.write(f"APLICACIONES REALIZADAS HOY ({len(aplicaciones)}):\n")
                f.write(f"-" * 80 + "\n")
                for app in aplicaciones:
                    f.write(f"Nota: {app['numero_nota']} -> Factura: {app['numero_factura']}\n")
                    f.write(f"  Valor aplicado: ${app['valor_aplicado']:,.2f}\n")
                    f.write(f"  Cantidad aplicada: {app['cantidad_aplicada']:.5f}\n")
                    f.write(f"  Saldo restante: ${app['saldo_restante']:,.2f}\n")
                    f.write(f"  Estado: {app['estado']}\n\n")
        
        logger.info(f"Reporte de notas crédito generado: {reporte_notas_path}")
        
        # ============================================================
        # 10. ENVIAR CORREO
        # ============================================================
        email_sender = EmailSender(
            SMTP_SERVER,
            SMTP_PORT,
            EMAIL_USERNAME,
            EMAIL_PASSWORD
        )
        
        exito = email_sender.enviar_reporte(
            DESTINATARIOS,
            output_path,
            fecha_reporte
        )
        
        if exito:
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESO COMPLETADO EXITOSAMENTE")
            logger.info(f"{'='*60}")
        else:
            logger.error("El proceso completó con errores en el envío de correo")
            
    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()