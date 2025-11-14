#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos históricos
Este script ejecuta el proceso diario para fechas específicas del pasado
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import logging

# Agregar el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core.api_client import SiesaAPIClient
from core.business_rules import BusinessRulesValidator
from core.notas_credito_manager import NotasCreditoManager
from core.excel_processor import ExcelProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def procesar_fecha(fecha, api_client, notas_manager, validator, excel_processor):
    """
    Procesa las facturas de una fecha específica

    Args:
        fecha: fecha a procesar
        api_client: cliente de la API
        notas_manager: gestor de notas de crédito
        validator: validador de reglas de negocio
        excel_processor: procesador de Excel

    Returns:
        dict con estadísticas del procesamiento
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Procesando fecha: {fecha.strftime('%Y-%m-%d')}")
    logger.info(f"{'='*60}")

    # 1. Obtener facturas de la API
    facturas_raw = api_client.obtener_facturas(fecha)

    if not facturas_raw:
        logger.warning("No se encontraron facturas para esta fecha")
        return {
            'fecha': fecha.strftime('%Y-%m-%d'),
            'total': 0,
            'validas': 0,
            'notas': 0,
            'rechazadas': 0,
            'aplicaciones': 0
        }

    logger.info(f"Total de documentos obtenidos: {len(facturas_raw)}")

    # 2. Aplicar reglas de negocio
    facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(facturas_raw)

    logger.info(f"Facturas válidas: {len(facturas_validas)}")
    logger.info(f"Notas crédito: {len(notas_credito)}")
    logger.info(f"Facturas rechazadas: {len(facturas_rechazadas)}")

    # 3. Registrar facturas rechazadas
    for item in facturas_rechazadas:
        factura = item['factura']
        notas_manager.registrar_factura_rechazada(factura, item['razon_rechazo'])

    # 4. Registrar tipos de inventario
    tipos_registrados = set()
    for factura in facturas_validas:
        tipo_inv = str(factura.get('f_cod_tipo_inv', '')).strip()
        if tipo_inv and tipo_inv not in tipos_registrados:
            notas_manager.registrar_tipo_inventario(
                tipo_inv,
                factura.get('f_desc_tipo_inv', ''),
                es_excluido=False
            )
            tipos_registrados.add(tipo_inv)

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

    # 5. Registrar notas crédito
    notas_nuevas = 0
    if notas_credito:
        logger.info(f"Registrando {len(notas_credito)} notas crédito...")
        for nota in notas_credito:
            if notas_manager.registrar_nota_credito(nota):
                notas_nuevas += 1
        logger.info(f"Notas crédito nuevas registradas: {notas_nuevas}")

    # 6. Transformar facturas válidas
    aplicaciones = []
    facturas_registradas = 0
    if facturas_validas:
        facturas_transformadas = [
            excel_processor.transformar_factura(factura)
            for factura in facturas_validas
        ]

        # 7. REGISTRAR FACTURAS VÁLIDAS EN BASE DE DATOS
        logger.info(f"Registrando {len(facturas_transformadas)} facturas válidas en BD...")
        for factura in facturas_transformadas:
            if notas_manager.registrar_factura_valida(factura):
                facturas_registradas += 1
        logger.info(f"Facturas válidas registradas: {facturas_registradas}/{len(facturas_transformadas)}")

        # 8. Aplicar notas crédito
        logger.info("Procesando aplicación de notas crédito...")
        aplicaciones = notas_manager.procesar_notas_para_facturas(facturas_transformadas)

        if aplicaciones:
            logger.info(f"Total de aplicaciones realizadas: {len(aplicaciones)}")
            for app in aplicaciones[:5]:  # Mostrar solo las primeras 5
                logger.info(f"  - Nota {app['numero_nota']} -> Factura {app['numero_factura']} "
                           f"(${app['valor_aplicado']:,.2f})")
            if len(aplicaciones) > 5:
                logger.info(f"  ... y {len(aplicaciones) - 5} más")

    # 9. Resumen
    resumen = notas_manager.obtener_resumen_notas()
    logger.info(f"\nResumen de notas crédito:")
    logger.info(f"  Notas pendientes: {resumen.get('notas_pendientes', 0)}")
    logger.info(f"  Saldo pendiente: ${resumen.get('saldo_pendiente_total', 0):,.2f}")

    return {
        'fecha': fecha.strftime('%Y-%m-%d'),
        'total': len(facturas_raw),
        'validas': len(facturas_validas),
        'facturas_registradas': facturas_registradas,
        'notas': notas_nuevas,
        'rechazadas': len(facturas_rechazadas),
        'aplicaciones': len(aplicaciones)
    }

def main():
    """Función principal para poblar datos históricos"""
    try:
        # Detectar directorio raíz del proyecto (el padre de scripts/)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent

        # Cambiar al directorio del proyecto
        os.chdir(project_root)
        logger.info(f"Directorio de trabajo: {project_root}")

        # Cargar variables de entorno
        load_dotenv()

        # Configuración
        CONNI_KEY = os.getenv('CONNI_KEY')
        CONNI_TOKEN = os.getenv('CONNI_TOKEN')
        TEMPLATE_PATH = os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')
        DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')

        # Validar configuración
        if not all([CONNI_KEY, CONNI_TOKEN]):
            raise ValueError("Faltan variables de entorno requeridas (CONNI_KEY, CONNI_TOKEN)")

        # Inicializar componentes
        api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
        notas_manager = NotasCreditoManager(DB_PATH)
        validator = BusinessRulesValidator()
        excel_processor = ExcelProcessor(TEMPLATE_PATH)

        # Definir fechas a procesar: 10, 11, 12 de noviembre 2025
        fechas = [
            datetime(2025, 11, 10),
            datetime(2025, 11, 11),
            datetime(2025, 11, 12)
        ]

        logger.info(f"\n{'#'*60}")
        logger.info(f"POBLACIÓN DE DATOS HISTÓRICOS")
        logger.info(f"Fechas a procesar: {', '.join([f.strftime('%Y-%m-%d') for f in fechas])}")
        logger.info(f"{'#'*60}\n")

        # Procesar cada fecha
        resultados = []
        for fecha in fechas:
            try:
                resultado = procesar_fecha(fecha, api_client, notas_manager, validator, excel_processor)
                resultados.append(resultado)
            except Exception as e:
                logger.error(f"Error procesando {fecha.strftime('%Y-%m-%d')}: {e}")
                import traceback
                traceback.print_exc()

        # Resumen final
        logger.info(f"\n{'#'*60}")
        logger.info("RESUMEN FINAL")
        logger.info(f"{'#'*60}\n")

        logger.info(f"{'Fecha':<12} {'Total':<8} {'Válidas':<10} {'Reg.BD':<10} {'Notas':<8} {'Rechaz.':<10} {'Aplic.':<10}")
        logger.info(f"{'-'*80}")

        totales = {
            'total': 0,
            'validas': 0,
            'facturas_registradas': 0,
            'notas': 0,
            'rechazadas': 0,
            'aplicaciones': 0
        }

        for r in resultados:
            logger.info(f"{r['fecha']:<12} {r['total']:<8} {r['validas']:<10} "
                       f"{r['facturas_registradas']:<10} {r['notas']:<8} {r['rechazadas']:<10} {r['aplicaciones']:<10}")
            for key in totales:
                if key in r:
                    totales[key] += r[key]

        logger.info(f"{'-'*80}")
        logger.info(f"{'TOTALES':<12} {totales['total']:<8} {totales['validas']:<10} "
                   f"{totales['facturas_registradas']:<10} {totales['notas']:<8} {totales['rechazadas']:<10} {totales['aplicaciones']:<10}")

        # Resumen final de notas
        resumen_final = notas_manager.obtener_resumen_notas()
        logger.info(f"\n{'='*60}")
        logger.info("ESTADO FINAL DE NOTAS CRÉDITO")
        logger.info(f"{'='*60}")
        logger.info(f"  Notas pendientes: {resumen_final.get('notas_pendientes', 0)}")
        logger.info(f"  Saldo pendiente total: ${resumen_final.get('saldo_pendiente_total', 0):,.2f}")
        logger.info(f"  Notas aplicadas: {resumen_final.get('notas_aplicadas', 0)}")
        logger.info(f"  Total aplicaciones: {resumen_final.get('total_aplicaciones', 0)}")
        logger.info(f"  Monto total aplicado: ${resumen_final.get('monto_total_aplicado', 0):,.2f}")
        logger.info(f"{'='*60}\n")

        # Resumen de facturas en BD
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM facturas")
        total_facturas_bd = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facturas WHERE tiene_nota_credito = 1")
        facturas_con_notas = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(valor_total) FROM facturas")
        valor_total_bd = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM facturas_rechazadas")
        total_rechazadas_bd = cursor.fetchone()[0]

        conn.close()

        logger.info(f"{'='*60}")
        logger.info("ESTADO FINAL DE BASE DE DATOS")
        logger.info(f"{'='*60}")
        logger.info(f"  Facturas válidas registradas: {total_facturas_bd:,}")
        logger.info(f"  Facturas con notas aplicadas: {facturas_con_notas:,}")
        logger.info(f"  Valor total facturado: ${valor_total_bd:,.2f}")
        logger.info(f"  Facturas rechazadas: {total_rechazadas_bd:,}")
        logger.info(f"{'='*60}\n")

        logger.info("✅ Proceso completado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error en el proceso: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
