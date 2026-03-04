import os
from pathlib import Path
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
OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'output'


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

        # ============================================================
        # 1. OBTENER FACTURAS DE LA API
        # ============================================================
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

        # ============================================================
        # 2. INICIALIZAR GESTOR DE NOTAS CRÉDITO
        # ============================================================
        notas_manager = NotasCreditoManager()

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

        # Registrar facturas rechazadas
        if facturas_rechazadas:
            logger.info("Registrando facturas rechazadas...")
            for item in facturas_rechazadas:
                notas_manager.registrar_factura_rechazada(item['factura'], item['razon_rechazo'])

        # ============================================================
        # 4. GESTIONAR NOTAS CRÉDITO
        # ============================================================
        notas_nuevas = 0

        if notas_credito:
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESANDO NOTAS CRÉDITO")
            logger.info(f"{'='*60}")

            for nota in notas_credito:
                if notas_manager.registrar_nota_credito(nota):
                    notas_nuevas += 1

            logger.info(f"Notas crédito nuevas registradas: {notas_nuevas}")

        # ============================================================
        # 5. REGISTRAR FACTURAS CRUDAS Y APLICAR NOTAS EN CRUDO
        # ============================================================
        if not facturas_validas:
            logger.warning("No hay facturas válidas para procesar")
            return {
                'exito': True,
                'mensaje': 'No hay facturas válidas',
                'facturas_procesadas': 0,
                'notas_credito': len(notas_credito),
                'facturas_rechazadas': len(facturas_rechazadas)
            }

        logger.info(f"\n{'='*60}")
        logger.info(f"REGISTRANDO FACTURAS CRUDAS EN BASE DE DATOS")
        logger.info(f"{'='*60}")

        facturas_registradas = 0
        for factura in facturas_validas:
            if notas_manager.registrar_factura(factura):
                facturas_registradas += 1

        logger.info(f"Facturas registradas en BD: {facturas_registradas} de {len(facturas_validas)}")

        # ============================================================
        # 6. APLICAR NOTAS CRÉDITO A FACTURAS CRUDAS
        # ============================================================
        logger.info(f"\n{'='*60}")
        logger.info(f"APLICANDO NOTAS CRÉDITO A FACTURAS CRUDAS")
        logger.info(f"{'='*60}")

        aplicaciones = notas_manager.procesar_notas_para_facturas(facturas_validas)

        logger.info(f"Aplicaciones de notas realizadas: {len(aplicaciones)}")

        if aplicaciones:
            logger.info("\nResumen de aplicaciones:")
            for app in aplicaciones[:5]:
                logger.info(f"  Nota {app['numero_nota']} -> Factura {app['numero_factura']}: ${app['valor_aplicado']:,.2f}")
            if len(aplicaciones) > 5:
                logger.info(f"  ... y {len(aplicaciones) - 5} aplicaciones más")

        # ============================================================
        # 7. TRANSFORMAR FACTURAS VÁLIDAS PARA EXCEL
        # ============================================================
        logger.info(f"\n{'='*60}")
        logger.info(f"TRANSFORMANDO FACTURAS PARA EXCEL")
        logger.info(f"{'='*60}")

        excel_processor = ExcelProcessor(config.get('TEMPLATE_PATH', './templates/plantilla.xlsx'))
        facturas_transformadas = [
            excel_processor.transformar_factura(factura)
            for factura in facturas_validas
        ]

        logger.info(f"Facturas transformadas: {len(facturas_transformadas)}")

        # ============================================================
        # 8. GENERAR ARCHIVOS
        # ============================================================
        logger.info(f"\n{'='*60}")
        logger.info(f"GENERANDO ARCHIVOS DE SALIDA")
        logger.info(f"{'='*60}")

        output_filename = f"facturas_{fecha.strftime('%Y%m%d')}.xlsx"
        OUTPUT_DIR.mkdir(exist_ok=True)
        output_path = str(OUTPUT_DIR / output_filename)

        excel_processor.generar_excel(facturas_transformadas, output_path)
        logger.info(f"Excel generado: {output_path}")

        # ============================================================
        # 9. GENERAR REPORTE DE RESUMEN
        # ============================================================
        resumen_path = os.path.join('./output', f"resumen_{fecha.strftime('%Y%m%d')}.txt")
        with open(resumen_path, 'w', encoding='utf-8') as f:
            f.write(f"REPORTE DE PROCESAMIENTO - {fecha.strftime('%Y-%m-%d')}\n")
            f.write(f"{'='*80}\n\n")

            f.write(f"FACTURAS PROCESADAS:\n")
            f.write(f"  - Facturas válidas: {len(facturas_transformadas)}\n")
            f.write(f"  - Facturas registradas en BD: {facturas_registradas}\n")
            f.write(f"  - Facturas rechazadas: {len(facturas_rechazadas)}\n\n")

            f.write(f"NOTAS DE CRÉDITO:\n")
            f.write(f"  - Notas detectadas: {len(notas_credito)}\n")
            f.write(f"  - Notas nuevas registradas: {notas_nuevas}\n")
            f.write(f"  - Aplicaciones realizadas: {len(aplicaciones)}\n\n")

            resumen_notas = notas_manager.obtener_resumen_notas()
            f.write(f"ESTADO ACTUAL DE NOTAS:\n")
            f.write(f"  - Notas pendientes: {resumen_notas.get('notas_pendientes', 0)}\n")
            f.write(f"  - Saldo pendiente: ${resumen_notas.get('saldo_pendiente_total', 0):,.2f}\n")
            f.write(f"  - Notas aplicadas (histórico): {resumen_notas.get('notas_aplicadas', 0)}\n")
            f.write(f"  - Total aplicaciones (histórico): {resumen_notas.get('total_aplicaciones', 0)}\n\n")

        logger.info(f"Reporte de resumen generado: {resumen_path}")

        # ============================================================
        # 10. ENVIAR EMAIL (OPCIONAL)
        # ============================================================
        if enviar_email and config.get('EMAIL_USERNAME') and config.get('DESTINATARIOS'):
            logger.info(f"\n{'='*60}")
            logger.info(f"ENVIANDO EMAIL A OPERATIVA")
            logger.info(f"{'='*60}")

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
                logger.warning("Error al enviar email (ver logs anteriores)")
        else:
            logger.info("\nEnvío de email omitido (configuración no disponible o deshabilitado)")

        # ============================================================
        # 11. RESULTADO FINAL
        # ============================================================
        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESO COMPLETADO EXITOSAMENTE")
        logger.info(f"{'='*60}")
        logger.info(f"  Facturas procesadas: {len(facturas_transformadas)}")
        logger.info(f"  Facturas en BD: {facturas_registradas}")
        logger.info(f"  Notas crédito nuevas: {notas_nuevas}")
        logger.info(f"  Aplicaciones: {len(aplicaciones)}")
        logger.info(f"  Rechazadas: {len(facturas_rechazadas)}")
        logger.info(f"  Archivo: {output_filename}")
        logger.info(f"{'='*60}\n")

        return {
            'exito': True,
            'mensaje': 'Proceso completado exitosamente',
            'fecha': fecha.strftime('%Y-%m-%d'),
            'facturas_procesadas': len(facturas_transformadas),
            'facturas_registradas': facturas_registradas,
            'notas_credito': len(notas_credito),
            'notas_nuevas': notas_nuevas,
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
    Procesa un rango de fechas y genera un Excel consolidado

    Args:
        fecha_desde: datetime - Fecha inicial
        fecha_hasta: datetime - Fecha final
        config: dict - Configuración con claves API, SMTP, etc.

    Returns:
        dict - Resultado del procesamiento consolidado
    """
    try:
        logger.info(f"={'='*60}")
        logger.info(f"Procesando rango: {fecha_desde.strftime('%Y-%m-%d')} a {fecha_hasta.strftime('%Y-%m-%d')}")
        logger.info(f"={'='*60}")

        todas_facturas_transformadas = []
        total_notas = 0
        total_rechazadas = 0
        total_aplicaciones = 0
        aplicaciones_all = []
        total_facturas_procesadas = 0

        # Inicializar managers y processors
        notas_manager = NotasCreditoManager()
        excel_processor = ExcelProcessor(config.get('TEMPLATE_PATH', './templates/plantilla.xlsx'))
        api_client = SiesaAPIClient(config['CONNI_KEY'], config['CONNI_TOKEN'])
        validator = BusinessRulesValidator()

        def factura_completa(factura):
            es_cruda = any(k in factura for k in ('f_prefijo', 'f_nrodocto', 'f_cod_item'))
            if es_cruda:
                codigo = factura.get('f_cod_item') or factura.get('f_rowid_movto') or factura.get('f_rowid') or factura.get('f_desc_item')
                return bool(str(factura.get('f_prefijo', '')).strip()) and bool(str(factura.get('f_nrodocto', '')).strip()) and bool(str(codigo or '').strip()) and bool(str(factura.get('f_cliente_desp', '')).strip())
            codigo = factura.get('codigo_producto') or factura.get('codigo_producto_api') or factura.get('rowid_movto') or factura.get('rowid') or factura.get('nombre_producto')
            return bool(str(factura.get('numero_factura', '')).strip()) and bool(str(codigo or '').strip()) and bool(str(factura.get('nit_cliente', factura.get('nit_comprador', ''))).strip())

        usar_consulta_rango = os.getenv('SIESA_RANGO_UNICO', '1') == '1'

        if usar_consulta_rango:
            logger.info("Consultando API en una sola llamada por rango")
            facturas_raw = api_client.obtener_facturas(fecha_desde, fecha_hasta)

            if facturas_raw:
                facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(facturas_raw)

                total_notas += len(notas_credito)
                total_rechazadas += len(facturas_rechazadas)

                for nota in notas_credito:
                    notas_manager.registrar_nota_credito(nota)

                ok, error_detalle = notas_manager.registrar_facturas_y_rechazos(
                    facturas_validas,
                    facturas_rechazadas
                )
                if not ok:
                    logger.error(f"Error en registro de facturas: {error_detalle}")
                    return {
                        'exito': False,
                        'mensaje': f"Error en registro de facturas: {error_detalle}"
                    }

                facturas_procesables = [f for f in facturas_validas if factura_completa(f)]
                if facturas_procesables:
                    aplicaciones = notas_manager.procesar_notas_para_facturas(facturas_procesables)
                    total_aplicaciones += len(aplicaciones)
                    aplicaciones_all.extend(aplicaciones)
            else:
                logger.warning("No se encontraron facturas para el rango especificado")
        else:
            fecha_actual = fecha_desde
            while fecha_actual <= fecha_hasta:
                logger.info(f"Procesando día: {fecha_actual.strftime('%Y-%m-%d')}")

                facturas_raw = api_client.obtener_facturas(fecha_actual)

                if facturas_raw:
                    facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(facturas_raw)

                    total_notas += len(notas_credito)
                    total_rechazadas += len(facturas_rechazadas)

                    for nota in notas_credito:
                        notas_manager.registrar_nota_credito(nota)

                    ok, error_detalle = notas_manager.registrar_facturas_y_rechazos(
                        facturas_validas,
                        facturas_rechazadas
                    )
                    if not ok:
                        logger.error(f"Error en registro de facturas: {error_detalle}")
                        return {
                            'exito': False,
                            'mensaje': f"Error en registro de facturas: {error_detalle}"
                        }

                    facturas_procesables = [f for f in facturas_validas if factura_completa(f)]
                    if facturas_procesables:
                        aplicaciones = notas_manager.procesar_notas_para_facturas(facturas_procesables)
                        total_aplicaciones += len(aplicaciones)
                        aplicaciones_all.extend(aplicaciones)

                fecha_actual += timedelta(days=1)

        aplicaciones_map = {}
        for app in aplicaciones_all:
            key = (
                app.get('numero_factura', ''),
                app.get('codigo_producto', ''),
                int(app.get('indice_linea', 0) or 0)
            )
            entry = aplicaciones_map.get(key)
            if not entry:
                aplicaciones_map[key] = {'valor': 0.0, 'cantidad': 0.0, 'notas': []}
                entry = aplicaciones_map[key]
            entry['valor'] += float(app.get('valor_aplicado', 0) or 0)
            entry['cantidad'] += float(app.get('cantidad_aplicada', 0) or 0)
            nota_num = app.get('numero_nota')
            if nota_num and nota_num not in entry['notas']:
                entry['notas'].append(nota_num)

        facturas_db = notas_manager.obtener_facturas_rango(
            fecha_desde.strftime('%Y-%m-%d'),
            fecha_hasta.strftime('%Y-%m-%d')
        )
        todas_facturas_transformadas = []
        for row in facturas_db:
            payload = row.get('raw_payload')
            if not payload:
                continue
            try:
                factura = json.loads(payload)
            except Exception:
                continue
            factura['_indice_linea'] = row.get('indice_linea', 0)
            key = (
                row.get('numero_factura', ''),
                row.get('codigo_producto', ''),
                int(row.get('indice_linea', 0) or 0)
            )
            entry = aplicaciones_map.get(key)
            if entry:
                factura['descuento_valor'] = entry['valor']
                factura['descuento_cantidad'] = entry['cantidad']
                factura['nota_aplicada'] = ','.join(entry['notas'])
            todas_facturas_transformadas.append(excel_processor.transformar_factura(factura))

        total_facturas_procesadas = len(todas_facturas_transformadas)

        output_filename = f"facturas_rango_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"
        OUTPUT_DIR.mkdir(exist_ok=True)
        output_path = str(OUTPUT_DIR / output_filename)

        if todas_facturas_transformadas:
            excel_processor.generar_excel(todas_facturas_transformadas, output_path)
            logger.info(f"Excel consolidado generado: {output_path}")
        else:
            logger.warning("No se generaron facturas, no se crea Excel")

        resumen_notas = notas_manager.obtener_resumen_notas()

        return {
            'exito': True,
            'mensaje': 'Rango procesado exitosamente',
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
            'total_dias': (fecha_hasta - fecha_desde).days + 1,
            'total_facturas_procesadas': total_facturas_procesadas,
            'total_notas_credito': total_notas,
            'total_facturas_rechazadas': total_rechazadas,
            'total_aplicaciones': total_aplicaciones,
            'notas_pendientes': resumen_notas.get('notas_pendientes', 0),
            'notas_aplicadas': resumen_notas.get('notas_aplicadas', 0),
            'saldo_pendiente_total': resumen_notas.get('saldo_pendiente_total', 0.0),
            'archivo_generado': output_filename
        }

    except Exception as e:
        logger.error(f"Error procesando rango de fechas: {e}", exc_info=True)
        raise


def main():
    """Función principal del proceso con reglas de negocio y gestión de notas crédito"""
    try:
        # Cargar variables de entorno
        load_dotenv()

        # Preparar configuración
        config = {
            'CONNI_KEY': os.getenv('CONNI_KEY'),
            'CONNI_TOKEN': os.getenv('CONNI_TOKEN'),
            'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'SMTP_PORT': int(os.getenv('SMTP_PORT', '587')),
            'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
            'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
            'DESTINATARIOS': os.getenv('DESTINATARIOS', '').split(',') if os.getenv('DESTINATARIOS') else [],
            'TEMPLATE_PATH': os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')
        }

        # Validar configuración mínima
        if not all([config['CONNI_KEY'], config['CONNI_TOKEN']]):
            raise ValueError("Faltan variables de entorno: CONNI_KEY y CONNI_TOKEN son requeridas")

        # Calcular fecha del día anterior
        fecha_reporte = datetime.now() - timedelta(days=1)

        # Procesar la fecha
        resultado = procesar_fecha(fecha_reporte, config, enviar_email=True)

        if resultado['exito']:
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESO COMPLETADO EXITOSAMENTE")
            logger.info(f"  - Facturas procesadas: {resultado.get('facturas_procesadas', 0)}")
            logger.info(f"  - Notas crédito: {resultado.get('notas_credito', 0)}")
            logger.info(f"  - Aplicaciones: {resultado.get('aplicaciones', 0)}")
            logger.info(f"{'='*60}")
        else:
            logger.error(f"El proceso completó con errores: {resultado.get('mensaje')}")

    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
