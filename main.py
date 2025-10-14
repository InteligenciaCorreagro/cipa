import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from src.api_client import SiesaAPIClient
from src.excel_processor import ExcelProcessor
from src.email_sender import EmailSender

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal del proceso"""
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
        
        # Validar configuración
        if not all([CONNI_KEY, CONNI_TOKEN, EMAIL_USERNAME, EMAIL_PASSWORD]):
            raise ValueError("Faltan variables de entorno requeridas")
        
        # Calcular fecha del día anterior
        fecha_reporte = datetime.now() - timedelta(days=1)
        logger.info(f"Generando reporte para: {fecha_reporte.strftime('%Y-%m-%d')}")
        
        # 1. Obtener facturas de la API
        api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
        facturas_raw = api_client.obtener_facturas(fecha_reporte)
        
        if not facturas_raw:
            logger.warning("No se encontraron facturas para la fecha especificada")
            return
        
        # 2. Transformar facturas
        excel_processor = ExcelProcessor(TEMPLATE_PATH)
        facturas_transformadas = [
            excel_processor.transformar_factura(factura)
            for factura in facturas_raw
        ]
        
        # 3. Generar Excel
        output_filename = f"facturas_{fecha_reporte.strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join('./output', output_filename)
        
        # Crear directorio output si no existe
        os.makedirs('./output', exist_ok=True)
        
        excel_processor.generar_excel(facturas_transformadas, output_path)
        
        # 4. Enviar correo
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
            logger.info("Proceso completado exitosamente")
        else:
            logger.error("El proceso completó con errores en el envío de correo")
            
    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()