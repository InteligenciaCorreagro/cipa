#!/usr/bin/env python3
"""
Script para exportar archivo de operativa con rango de fechas personalizado
Uso: python backend/export_operativa_custom.py --fecha-inicio YYYY-MM-DD --fecha-fin YYYY-MM-DD [--enviar-correo]
"""

import os
import sys
import argparse
from datetime import datetime
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

def obtener_facturas_rango(api_client: SiesaAPIClient, fecha_inicio: datetime, fecha_fin: datetime):
    """
    Obtiene facturas para un rango de fechas

    Args:
        api_client: Cliente de la API SIESA
        fecha_inicio: Fecha de inicio del rango
        fecha_fin: Fecha de fin del rango

    Returns:
        Lista de facturas obtenidas
    """
    import requests

    fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
    fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')

    params = {
        "idCompania": "37",
        "descripcion": "Api_Consulta_Fac_Correagro",
        "parametros": f"FECHA_INI='{fecha_inicio_str}'|FECHA_FIN='{fecha_fin_str}'"
    }

    try:
        logger.info(f"Consultando facturas desde {fecha_inicio_str} hasta {fecha_fin_str}")
        response = requests.get(
            api_client.BASE_URL,
            params=params,
            headers=api_client.headers,
            timeout=30
        )
        response.raise_for_status()

        # Parsear respuesta JSON
        data = response.json()

        # Verificar estructura de respuesta SIESA
        if isinstance(data, dict):
            # Verificar si hay error en la respuesta
            if 'codigo' in data and data['codigo'] != 0:
                logger.error(f"Error en API: {data.get('mensaje', 'Error desconocido')}")
                raise ValueError(f"Error en API: {data.get('mensaje', 'Error desconocido')}")

            # Extraer facturas de la estructura SIESA
            if 'detalle' in data and isinstance(data['detalle'], dict):
                detalle = data['detalle']

                # Buscar en Table (estructura SIESA común)
                if 'Table' in detalle and isinstance(detalle['Table'], list):
                    facturas = detalle['Table']
                    logger.info(f"Se obtuvieron {len(facturas)} facturas")
                    return facturas

                # Buscar en table (lowercase)
                if 'table' in detalle and isinstance(detalle['table'], list):
                    facturas = detalle['table']
                    logger.info(f"Se obtuvieron {len(facturas)} facturas")
                    return facturas

                # Si detalle tiene una lista directa
                for key in detalle.keys():
                    if isinstance(detalle[key], list):
                        facturas = detalle[key]
                        logger.info(f"Se obtuvieron {len(facturas)} facturas desde clave '{key}'")
                        return facturas

            # Buscar directamente en las claves principales
            for key in ['data', 'facturas', 'result', 'rows', 'Table', 'table']:
                if key in data and isinstance(data[key], list):
                    facturas = data[key]
                    logger.info(f"Se obtuvieron {len(facturas)} facturas desde clave '{key}'")
                    return facturas

            logger.error(f"Estructura de respuesta no reconocida")
            raise ValueError("No se encontraron facturas en la estructura de respuesta")

        # Si la respuesta es una lista directamente
        elif isinstance(data, list):
            logger.info(f"Se obtuvieron {len(data)} facturas")
            return data

        else:
            logger.error(f"Tipo de respuesta no esperado: {type(data)}")
            raise ValueError(f"Tipo de respuesta no esperado: {type(data)}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error al consultar la API: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al procesar respuesta: {e}")
        raise

def main():
    """Función principal del script"""
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Exportar archivo de operativa con rango de fechas personalizado'
    )
    parser.add_argument(
        '--fecha-inicio',
        required=True,
        help='Fecha de inicio (formato: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--fecha-fin',
        required=True,
        help='Fecha de fin (formato: YYYY-MM-DD)'
    )
    parser.add_argument(
        '--enviar-correo',
        action='store_true',
        help='Enviar el archivo por correo a los destinatarios configurados'
    )
    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Directorio de salida para los archivos generados (default: ./output)'
    )

    args = parser.parse_args()

    try:
        # Validar y parsear fechas
        try:
            fecha_inicio = datetime.strptime(args.fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(args.fecha_fin, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Error al parsear fechas: {e}")
            logger.error("El formato debe ser YYYY-MM-DD (ejemplo: 2025-11-01)")
            sys.exit(1)

        # Validar que fecha_inicio <= fecha_fin
        if fecha_inicio > fecha_fin:
            logger.error("La fecha de inicio debe ser anterior o igual a la fecha de fin")
            sys.exit(1)

        # Cargar variables de entorno
        load_dotenv()

        # Configuración
        CONNI_KEY = os.getenv('CONNI_KEY')
        CONNI_TOKEN = os.getenv('CONNI_TOKEN')
        TEMPLATE_PATH = os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')
        DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')

        # Validar configuración mínima
        if not all([CONNI_KEY, CONNI_TOKEN]):
            raise ValueError("Faltan variables de entorno requeridas (CONNI_KEY, CONNI_TOKEN)")

        # Si se solicita enviar correo, validar configuración SMTP
        if args.enviar_correo:
            SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
            EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
            EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
            DESTINATARIOS = os.getenv('DESTINATARIOS', '').split(',')

            if not all([EMAIL_USERNAME, EMAIL_PASSWORD, DESTINATARIOS[0]]):
                raise ValueError("Faltan variables de entorno para envío de correo")

        logger.info(f"{'='*60}")
        logger.info(f"EXPORTACIÓN PERSONALIZADA DE ARCHIVO OPERATIVO")
        logger.info(f"Rango de fechas: {args.fecha_inicio} hasta {args.fecha_fin}")
        logger.info(f"Enviar correo: {'SÍ' if args.enviar_correo else 'NO'}")
        logger.info(f"{'='*60}\n")

        # ============================================================
        # 1. OBTENER FACTURAS DE LA API
        # ============================================================
        api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
        facturas_raw = obtener_facturas_rango(api_client, fecha_inicio, fecha_fin)

        if not facturas_raw:
            logger.warning("No se encontraron facturas para el rango de fechas especificado")
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

        # Log de facturas rechazadas
        if facturas_rechazadas:
            logger.info("Detalle de facturas rechazadas:")
            for item in facturas_rechazadas:
                factura = item['factura']
                numero = f"{factura.get('f_prefijo', '')}{factura.get('f_nrodocto', '')}"
                valor = factura.get('f_valor_subtotal_local', 0)
                logger.info(f"  - {numero}: {item['razon_rechazo']} (Valor: ${valor:,.2f})")

        # ============================================================
        # 4. MOSTRAR INFORMACIÓN DE NOTAS CRÉDITO (SIN REGISTRAR)
        # ============================================================
        if notas_credito:
            logger.info(f"\nNotas crédito detectadas: {len(notas_credito)}")
            logger.info("NOTA: Las notas crédito NO se registrarán en este modo de exportación")

        # ============================================================
        # 5. TRANSFORMAR FACTURAS VÁLIDAS
        # ============================================================
        if not facturas_validas:
            logger.warning("No hay facturas válidas para procesar después del filtrado")
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
        # 6. OBTENER RESUMEN DE NOTAS CRÉDITO (SOLO LECTURA)
        # ============================================================
        resumen = notas_manager.obtener_resumen_notas()
        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMEN DE NOTAS CRÉDITO (Base de datos actual):")
        logger.info(f"  - Notas pendientes: {resumen.get('notas_pendientes', 0)}")
        logger.info(f"  - Saldo pendiente total: ${resumen.get('saldo_pendiente_total', 0):,.2f}")
        logger.info(f"{'='*60}\n")

        # ============================================================
        # 7. GENERAR EXCEL CON FACTURAS PROCESADAS
        # ============================================================
        output_filename = f"facturas_custom_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.xlsx"
        output_path = os.path.join(args.output_dir, output_filename)

        # Crear directorio output si no existe
        os.makedirs(args.output_dir, exist_ok=True)

        excel_processor.generar_excel(facturas_transformadas, output_path)
        logger.info(f"\n✓ Archivo generado exitosamente: {output_path}")

        # ============================================================
        # 8. GENERAR REPORTE DE FACTURAS RECHAZADAS
        # ============================================================
        if facturas_rechazadas:
            reporte_rechazadas_path = os.path.join(
                args.output_dir,
                f"facturas_rechazadas_custom_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.txt"
            )

            with open(reporte_rechazadas_path, 'w', encoding='utf-8') as f:
                f.write(f"REPORTE DE FACTURAS RECHAZADAS (EXPORTACIÓN PERSONALIZADA)\n")
                f.write(f"Rango: {args.fecha_inicio} hasta {args.fecha_fin}\n")
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

            logger.info(f"✓ Reporte de facturas rechazadas generado: {reporte_rechazadas_path}")

        # ============================================================
        # 9. ENVIAR CORREO (OPCIONAL)
        # ============================================================
        if args.enviar_correo:
            logger.info("\nEnviando correo electrónico...")
            email_sender = EmailSender(
                SMTP_SERVER,
                SMTP_PORT,
                EMAIL_USERNAME,
                EMAIL_PASSWORD
            )

            # Usar fecha_inicio como fecha de referencia para el correo
            exito = email_sender.enviar_reporte(
                DESTINATARIOS,
                output_path,
                fecha_inicio
            )

            if exito:
                logger.info("✓ Correo enviado exitosamente")
            else:
                logger.error("✗ Error al enviar el correo")

        logger.info(f"\n{'='*60}")
        logger.info(f"EXPORTACIÓN COMPLETADA EXITOSAMENTE")
        logger.info(f"Archivo: {output_path}")
        logger.info(f"{'='*60}")

    except Exception as e:
        logger.error(f"Error en el proceso: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
