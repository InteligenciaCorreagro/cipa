import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import time
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


def procesar_fecha(fecha, config, enviar_email=True):
    """
    Procesa las facturas de una fecha específica

    Args:
        fecha: datetime - Fecha a procesar
        config: dict - Configuración con claves API, SMTP, etc.
        enviar_email: bool - Si debe enviar email o solo generar archivo

    Returns:
        dict - Resultado del procesamiento con rutas de archivos y estadísticas
    """
    try:
        logger.info(f"={'='*60}")
        logger.info(f"Procesando fecha: {fecha.strftime('%Y-%m-%d')}")
        logger.info(f"={'='*60}")

        # 1. OBTENER FACTURAS DE LA API
        api_client = SiesaAPIClient(config['CONNI_KEY'], config['CONNI_TOKEN'])
        facturas_raw = api_client.obtener_facturas(fecha)

        if not facturas_raw:
            logger.warning("No se encontraron facturas para la fecha especificada")
            return {
                'exito': True,
                'mensaje': 'No se encontraron facturas',
                'facturas_procesadas': 0
            }

        logger.info(f"Total de documentos obtenidos de la API: {len(facturas_raw)}")

        # 2. INICIALIZAR GESTOR
        notas_manager = NotasCreditoManager(config.get('DB_PATH', './data/notas_credito.db'))

        # 3. APLICAR REGLAS DE NEGOCIO
        validator = BusinessRulesValidator()
        facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(facturas_raw)

        logger.info(f"\nRESULTADOS DEL FILTRADO:")
        logger.info(f"  - Facturas válidas: {len(facturas_validas)}")
        logger.info(f"  - Notas crédito: {len(notas_credito)}")
        logger.info(f"  - Facturas rechazadas: {len(facturas_rechazadas)}")

        # 4. REGISTRAR RECHAZADAS (BATCH)
        if facturas_rechazadas:
            notas_manager.registrar_rechazadas_batch(facturas_rechazadas)

        # 5. REGISTRAR NOTAS CRÉDITO (BATCH)
        notas_nuevas = 0
        notas_filtradas = 0
        if notas_credito:
            notas_nuevas, notas_filtradas = notas_manager.registrar_notas_batch(notas_credito)

        # 6. REGISTRAR FACTURAS (BATCH) y APLICAR NOTAS
        if not facturas_validas:
            logger.warning("No hay facturas válidas para procesar")
            return {
                'exito': True,
                'mensaje': 'No hay facturas válidas',
                'facturas_procesadas': 0,
                'notas_credito': len(notas_credito),
                'facturas_rechazadas': len(facturas_rechazadas)
            }

        t0 = time.time()
        facturas_registradas = notas_manager.registrar_facturas_batch(facturas_validas)
        logger.info(f"Facturas registradas en BD: {facturas_registradas} ({time.time()-t0:.1f}s)")

        # 7. APLICAR NOTAS (OPTIMIZADO)
        t0 = time.time()
        aplicaciones = notas_manager.procesar_notas_para_facturas_optimizado(facturas_validas)
        logger.info(f"Aplicaciones de notas: {len(aplicaciones)} ({time.time()-t0:.1f}s)")

        # 8. TRANSFORMAR Y GENERAR EXCEL
        excel_processor = ExcelProcessor(config.get('TEMPLATE_PATH', './templates/plantilla.xlsx'))
        facturas_transformadas = [
            excel_processor.transformar_factura(factura)
            for factura in facturas_validas
        ]

        output_filename = f"facturas_{fecha.strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join('./output', output_filename)
        os.makedirs('./output', exist_ok=True)
        excel_processor.generar_excel(facturas_transformadas, output_path)

        # 9. GENERAR REPORTE
        resumen_path = os.path.join('./output', f"resumen_{fecha.strftime('%Y%m%d')}.txt")
        resumen_notas = notas_manager.obtener_resumen_notas()
        with open(resumen_path, 'w', encoding='utf-8') as f:
            f.write(f"REPORTE DE PROCESAMIENTO - {fecha.strftime('%Y-%m-%d')}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Facturas válidas: {len(facturas_transformadas)}\n")
            f.write(f"Facturas registradas en BD: {facturas_registradas}\n")
            f.write(f"Facturas rechazadas: {len(facturas_rechazadas)}\n")
            f.write(f"Notas detectadas: {len(notas_credito)}\n")
            f.write(f"Notas nuevas: {notas_nuevas}\n")
            f.write(f"Aplicaciones: {len(aplicaciones)}\n")
            f.write(f"Notas pendientes: {resumen_notas.get('notas_pendientes', 0)}\n")
            f.write(f"Saldo pendiente: ${resumen_notas.get('saldo_pendiente_total', 0):,.2f}\n")

        # 10. ENVIAR EMAIL
        if enviar_email and config.get('EMAIL_USERNAME') and config.get('DESTINATARIOS'):
            email_sender = EmailSender(
                config.get('SMTP_SERVER', 'smtp.gmail.com'),
                int(config.get('SMTP_PORT', 587)),
                config['EMAIL_USERNAME'],
                config['EMAIL_PASSWORD']
            )
            exito_email = email_sender.enviar_reporte(
                config.get('DESTINATARIOS', []),
                output_path,
                fecha
            )
            if exito_email:
                logger.info("Email enviado exitosamente")
            else:
                logger.warning("Error al enviar email")

        logger.info(f"\nPROCESO COMPLETADO: {len(facturas_transformadas)} facturas, "
                    f"{notas_nuevas} notas, {len(aplicaciones)} aplicaciones")

        return {
            'exito': True,
            'mensaje': 'Proceso completado exitosamente',
            'fecha': fecha.strftime('%Y-%m-%d'),
            'facturas_procesadas': len(facturas_transformadas),
            'facturas_registradas': facturas_registradas,
            'notas_credito': len(notas_credito),
            'notas_nuevas': notas_nuevas,
            'notas_filtradas': notas_filtradas,
            'facturas_rechazadas': len(facturas_rechazadas),
            'aplicaciones': len(aplicaciones),
            'archivo_generado': output_path,
            'resumen_generado': resumen_path
        }

    except Exception as e:
        logger.error(f"Error procesando fecha {fecha}: {e}", exc_info=True)
        raise


def procesar_rango_fechas(fecha_desde, fecha_hasta, config):
    """
    Procesa un rango de fechas - VERSIÓN OPTIMIZADA

    OPTIMIZACIONES:
    - Una sola llamada API por día (ya existente)
    - Batch INSERT para facturas, rechazadas y notas
    - Aplicación de notas con pre-carga en memoria
    - Transformación y Excel consolidados al final

    Args:
        fecha_desde: datetime - Fecha inicial
        fecha_hasta: datetime - Fecha final
        config: dict - Configuración

    Returns:
        dict - Resultado consolidado
    """
    try:
        t_inicio = time.time()
        logger.info(f"={'='*60}")
        logger.info(f"Procesando rango: {fecha_desde.strftime('%Y-%m-%d')} a {fecha_hasta.strftime('%Y-%m-%d')}")
        logger.info(f"={'='*60}")

        # Inicializar componentes una sola vez
        notas_manager = NotasCreditoManager(config.get('DB_PATH', './data/notas_credito.db'))
        excel_processor = ExcelProcessor(config.get('TEMPLATE_PATH', './templates/plantilla.xlsx'))
        api_client = SiesaAPIClient(config['CONNI_KEY'], config['CONNI_TOKEN'])
        validator = BusinessRulesValidator()

        # Acumuladores
        todas_facturas_validas = []
        todas_notas_credito = []
        todas_rechazadas = []
        total_facturas_procesadas = 0

        # ================================================================
        # FASE 1: Obtener datos de API y filtrar (por día)
        # ================================================================
        fecha_actual = fecha_desde
        while fecha_actual <= fecha_hasta:
            fecha_str = fecha_actual.strftime('%Y-%m-%d')
            logger.info(f"\n--- Consultando API para {fecha_str} ---")

            t0 = time.time()
            facturas_raw = api_client.obtener_facturas(fecha_actual)
            logger.info(f"API respondió en {time.time()-t0:.1f}s: {len(facturas_raw) if facturas_raw else 0} documentos")

            if facturas_raw:
                t0 = time.time()
                facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(facturas_raw)
                logger.info(f"Filtrado en {time.time()-t0:.1f}s: {len(facturas_validas)} válidas, "
                           f"{len(notas_credito)} notas, {len(facturas_rechazadas)} rechazadas")

                todas_facturas_validas.extend(facturas_validas)
                todas_notas_credito.extend(notas_credito)
                todas_rechazadas.extend(facturas_rechazadas)

            fecha_actual += timedelta(days=1)

        logger.info(f"\n{'='*60}")
        logger.info(f"TOTALES ACUMULADOS:")
        logger.info(f"  Facturas válidas: {len(todas_facturas_validas)}")
        logger.info(f"  Notas crédito: {len(todas_notas_credito)}")
        logger.info(f"  Rechazadas: {len(todas_rechazadas)}")
        logger.info(f"{'='*60}")

        # ================================================================
        # FASE 2: Registrar todo en BD con operaciones batch
        # ================================================================

        # 2a. Registrar rechazadas (batch)
        t0 = time.time()
        if todas_rechazadas:
            notas_manager.registrar_rechazadas_batch(todas_rechazadas)
        logger.info(f"Rechazadas registradas en {time.time()-t0:.1f}s")

        # 2b. Registrar notas crédito (batch)
        t0 = time.time()
        notas_nuevas = 0
        notas_filtradas = 0
        if todas_notas_credito:
            notas_nuevas, notas_filtradas = notas_manager.registrar_notas_batch(todas_notas_credito)
        logger.info(f"Notas registradas en {time.time()-t0:.1f}s: {notas_nuevas} nuevas, {notas_filtradas} filtradas")

        # 2c. Registrar facturas válidas (batch)
        t0 = time.time()
        facturas_registradas = 0
        if todas_facturas_validas:
            facturas_registradas = notas_manager.registrar_facturas_batch(todas_facturas_validas)
        logger.info(f"Facturas registradas en {time.time()-t0:.1f}s: {facturas_registradas}")

        # 2d. Aplicar notas a facturas (optimizado)
        t0 = time.time()
        total_aplicaciones = 0
        if todas_facturas_validas:
            aplicaciones = notas_manager.procesar_notas_para_facturas_optimizado(todas_facturas_validas)
            total_aplicaciones = len(aplicaciones)
        logger.info(f"Notas aplicadas en {time.time()-t0:.1f}s: {total_aplicaciones} aplicaciones")

        # ================================================================
        # FASE 3: Generar Excel consolidado
        # ================================================================
        t0 = time.time()
        output_filename = f"facturas_rango_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join('./output', output_filename)
        os.makedirs('./output', exist_ok=True)

        if todas_facturas_validas:
            facturas_transformadas = [
                excel_processor.transformar_factura(factura)
                for factura in todas_facturas_validas
            ]
            total_facturas_procesadas = len(facturas_transformadas)
            excel_processor.generar_excel(facturas_transformadas, output_path)
            logger.info(f"Excel generado en {time.time()-t0:.1f}s: {output_path}")
        else:
            logger.warning("No se generaron facturas, no se crea Excel")

        # Resumen
        resumen_notas = notas_manager.obtener_resumen_notas()

        t_total = time.time() - t_inicio
        logger.info(f"\n{'='*60}")
        logger.info(f"RANGO COMPLETADO en {t_total:.1f}s ({t_total/60:.1f} min)")
        logger.info(f"  Facturas procesadas: {total_facturas_procesadas}")
        logger.info(f"  Facturas en BD: {facturas_registradas}")
        logger.info(f"  Notas nuevas: {notas_nuevas}")
        logger.info(f"  Aplicaciones: {total_aplicaciones}")
        logger.info(f"  Rechazadas: {len(todas_rechazadas)}")
        logger.info(f"{'='*60}")

        return {
            'exito': True,
            'mensaje': 'Rango procesado exitosamente',
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
            'total_dias': (fecha_hasta - fecha_desde).days + 1,
            'total_facturas_procesadas': total_facturas_procesadas,
            'total_notas_credito': len(todas_notas_credito),
            'total_facturas_rechazadas': len(todas_rechazadas),
            'total_aplicaciones': total_aplicaciones,
            'notas_pendientes': resumen_notas.get('notas_pendientes', 0),
            'notas_aplicadas': resumen_notas.get('notas_aplicadas', 0),
            'saldo_pendiente_total': resumen_notas.get('saldo_pendiente_total', 0.0),
            'archivo_generado': output_filename,
            'tiempo_total_segundos': round(t_total, 1)
        }

    except Exception as e:
        logger.error(f"Error procesando rango de fechas: {e}", exc_info=True)
        raise


def main():
    """Función principal del proceso"""
    try:
        load_dotenv()

        config = {
            'CONNI_KEY': os.getenv('CONNI_KEY'),
            'CONNI_TOKEN': os.getenv('CONNI_TOKEN'),
            'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
            'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
            'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
            'DESTINATARIOS': os.getenv('DESTINATARIOS', '').split(',') if os.getenv('DESTINATARIOS') else [],
            'TEMPLATE_PATH': os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx'),
            'DB_PATH': os.getenv('DB_PATH', './data/notas_credito.db')
        }

        if not all([config['CONNI_KEY'], config['CONNI_TOKEN']]):
            raise ValueError("Faltan variables de entorno: CONNI_KEY y CONNI_TOKEN son requeridas")

        fecha_reporte = datetime.now() - timedelta(days=1)

        resultado = procesar_fecha(fecha_reporte, config, enviar_email=True)

        if resultado['exito']:
            logger.info(f"\nPROCESO COMPLETADO EXITOSAMENTE")
            logger.info(f"  - Facturas: {resultado.get('facturas_procesadas', 0)}")
            logger.info(f"  - Notas: {resultado.get('notas_credito', 0)}")
            logger.info(f"  - Aplicaciones: {resultado.get('aplicaciones', 0)}")

    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()