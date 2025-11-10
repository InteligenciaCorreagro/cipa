#!/usr/bin/env python3
"""
Script para generar facturas diarias con descripción de notas aplicadas
Período: 1-9 de noviembre 2025

Este script:
1. Obtiene facturas válidas de la API SIESA para cada día
2. Filtra según reglas de negocio (tipos de inventario permitidos, monto mínimo)
3. Aplica notas de crédito pendientes
4. Agrega en la descripción qué nota se aplicó a cada factura
5. Genera un Excel por día con las facturas procesadas
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from collections import defaultdict

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


def generar_facturas_con_notas(fecha_inicio, fecha_fin, output_dir='./output'):
    """
    Genera facturas diarias con descripción de notas aplicadas

    Args:
        fecha_inicio: Fecha inicial del período (datetime)
        fecha_fin: Fecha final del período (datetime)
        output_dir: Directorio de salida para los archivos Excel
    """
    # Cargar variables de entorno
    load_dotenv()

    CONNI_KEY = os.getenv('CONNI_KEY')
    CONNI_TOKEN = os.getenv('CONNI_TOKEN')
    DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')
    TEMPLATE_PATH = os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')

    if not all([CONNI_KEY, CONNI_TOKEN]):
        raise ValueError("Faltan variables de entorno: CONNI_KEY y/o CONNI_TOKEN")

    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("GENERACIÓN DE FACTURAS DIARIAS CON NOTAS APLICADAS")
    print("=" * 80)
    print(f"\nFecha inicio: {fecha_inicio.strftime('%Y-%m-%d')}")
    print(f"Fecha fin: {fecha_fin.strftime('%Y-%m-%d')}")
    print(f"Directorio de salida: {output_dir}")

    # Inicializar componentes
    api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
    validator = BusinessRulesValidator()
    notas_manager = NotasCreditoManager(DB_PATH)
    excel_processor = ExcelProcessor(TEMPLATE_PATH)

    # Estadísticas generales
    total_dias = (fecha_fin - fecha_inicio).days + 1
    estadisticas_totales = {
        'dias_procesados': 0,
        'dias_con_facturas': 0,
        'total_facturas_validas': 0,
        'total_notas_aplicadas': 0,
        'total_aplicaciones': 0,
        'valor_total_facturas': 0.0,
        'valor_total_aplicado': 0.0,
        'archivos_generados': []
    }

    # Procesar cada día del período
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        print("\n" + "=" * 80)
        print(f"PROCESANDO DÍA: {fecha_str}")
        print("=" * 80)

        estadisticas_totales['dias_procesados'] += 1

        try:
            # ====================================================================
            # 1. OBTENER FACTURAS DE LA API
            # ====================================================================
            logger.info(f"Obteniendo facturas para {fecha_str}...")
            documentos = api_client.obtener_facturas(fecha_actual)

            if not documentos:
                logger.info(f"No se encontraron documentos para {fecha_str}")
                fecha_actual += timedelta(days=1)
                continue

            logger.info(f"Total de documentos obtenidos: {len(documentos)}")

            # ====================================================================
            # 2. FILTRAR FACTURAS SEGÚN REGLAS DE NEGOCIO
            # ====================================================================
            logger.info("Aplicando reglas de negocio...")
            facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(documentos)

            logger.info(f"Resultados del filtrado:")
            logger.info(f"  - Facturas válidas: {len(facturas_validas)}")
            logger.info(f"  - Notas crédito: {len(notas_credito)}")
            logger.info(f"  - Facturas rechazadas: {len(facturas_rechazadas)}")

            # Registrar notas crédito del día (si es necesario)
            if notas_credito:
                logger.info(f"Registrando {len(notas_credito)} notas crédito del día...")
                notas_nuevas = 0
                for nota in notas_credito:
                    if notas_manager.registrar_nota_credito(nota):
                        notas_nuevas += 1
                logger.info(f"Notas crédito nuevas registradas: {notas_nuevas}")

            # Si no hay facturas válidas, continuar con el siguiente día
            if not facturas_validas:
                logger.info("No hay facturas válidas para procesar")
                fecha_actual += timedelta(days=1)
                continue

            estadisticas_totales['dias_con_facturas'] += 1

            # ====================================================================
            # 3. TRANSFORMAR FACTURAS AL FORMATO EXCEL
            # ====================================================================
            logger.info("Transformando facturas...")
            facturas_transformadas = [
                excel_processor.transformar_factura(factura)
                for factura in facturas_validas
            ]

            logger.info(f"Facturas transformadas: {len(facturas_transformadas)}")

            # ====================================================================
            # 4. APLICAR NOTAS CRÉDITO PENDIENTES
            # ====================================================================
            logger.info("Procesando aplicación de notas crédito pendientes...")
            aplicaciones = notas_manager.procesar_notas_para_facturas(facturas_transformadas)

            logger.info(f"Total de aplicaciones realizadas: {len(aplicaciones)}")

            # Crear un diccionario de aplicaciones por factura para agregar a descripción
            # Formato: {numero_factura: [lista de números de notas aplicadas]}
            notas_por_factura = defaultdict(list)
            for app in aplicaciones:
                numero_factura = app['numero_factura']
                numero_nota = app['numero_nota']
                if numero_nota not in notas_por_factura[numero_factura]:
                    notas_por_factura[numero_factura].append(numero_nota)

            # Log detallado de aplicaciones
            if aplicaciones:
                logger.info("\nDetalle de aplicaciones:")
                notas_unicas = set()
                valor_total_aplicado_dia = 0.0

                for app in aplicaciones:
                    logger.info(f"  Nota {app['numero_nota']} -> Factura {app['numero_factura']}")
                    logger.info(f"    Valor aplicado: ${app['valor_aplicado']:,.2f}")
                    logger.info(f"    Cantidad aplicada: {app['cantidad_aplicada']:.5f}")
                    logger.info(f"    Estado: {app['estado']}")
                    notas_unicas.add(app['numero_nota'])
                    valor_total_aplicado_dia += app['valor_aplicado']

                logger.info(f"\nResumen del día:")
                logger.info(f"  Notas únicas aplicadas: {len(notas_unicas)}")
                logger.info(f"  Valor total aplicado: ${valor_total_aplicado_dia:,.2f}")

                estadisticas_totales['total_notas_aplicadas'] += len(notas_unicas)
                estadisticas_totales['total_aplicaciones'] += len(aplicaciones)
                estadisticas_totales['valor_total_aplicado'] += valor_total_aplicado_dia

            # ====================================================================
            # 5. AGREGAR DESCRIPCIÓN DE NOTAS APLICADAS
            # ====================================================================
            logger.info("Agregando descripción de notas aplicadas...")
            facturas_con_descripcion_notas = 0

            for factura in facturas_transformadas:
                numero_factura = factura['numero_factura']

                # Si esta factura tiene notas aplicadas, agregar a la descripción
                if numero_factura in notas_por_factura:
                    notas_aplicadas = notas_por_factura[numero_factura]
                    descripcion_original = factura.get('descripcion', '')

                    # Crear descripción de notas aplicadas
                    if len(notas_aplicadas) == 1:
                        nota_desc = f"Nota aplicada: {notas_aplicadas[0]}"
                    else:
                        nota_desc = f"Notas aplicadas: {', '.join(notas_aplicadas)}"

                    # Agregar a la descripción
                    if descripcion_original:
                        factura['descripcion'] = f"{descripcion_original} - {nota_desc}"
                    else:
                        factura['descripcion'] = nota_desc

                    facturas_con_descripcion_notas += 1
                    logger.debug(f"Factura {numero_factura}: {nota_desc}")

            if facturas_con_descripcion_notas > 0:
                logger.info(f"Facturas con descripción de notas: {facturas_con_descripcion_notas}")

            # ====================================================================
            # 6. CALCULAR ESTADÍSTICAS DEL DÍA
            # ====================================================================
            valor_total_facturas_dia = sum(f.get('valor_total', 0.0) for f in facturas_transformadas)
            estadisticas_totales['total_facturas_validas'] += len(facturas_transformadas)
            estadisticas_totales['valor_total_facturas'] += valor_total_facturas_dia

            logger.info(f"\nEstadísticas del día:")
            logger.info(f"  Facturas válidas: {len(facturas_transformadas)}")
            logger.info(f"  Valor total: ${valor_total_facturas_dia:,.2f}")

            # ====================================================================
            # 7. GENERAR EXCEL CON FACTURAS PROCESADAS
            # ====================================================================
            output_filename = f"facturas_con_notas_{fecha_actual.strftime('%Y%m%d')}.xlsx"
            output_path = os.path.join(output_dir, output_filename)

            logger.info(f"Generando archivo Excel: {output_filename}")
            excel_processor.generar_excel(facturas_transformadas, output_path)

            logger.info(f"✅ Archivo generado: {output_path}")
            estadisticas_totales['archivos_generados'].append({
                'fecha': fecha_str,
                'archivo': output_filename,
                'num_facturas': len(facturas_transformadas),
                'num_aplicaciones': len(aplicaciones),
                'valor_facturas': valor_total_facturas_dia
            })

        except Exception as e:
            logger.error(f"❌ Error procesando fecha {fecha_str}: {e}", exc_info=True)
            # Continuar con el siguiente día en caso de error
            fecha_actual += timedelta(days=1)
            continue

        fecha_actual += timedelta(days=1)

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n" + "=" * 80)
    print("RESUMEN FINAL DEL PROCESAMIENTO")
    print("=" * 80)
    print(f"\nPeríodo procesado: {fecha_inicio.strftime('%Y-%m-%d')} a {fecha_fin.strftime('%Y-%m-%d')}")
    print(f"Días procesados: {estadisticas_totales['dias_procesados']} / {total_dias}")
    print(f"Días con facturas: {estadisticas_totales['dias_con_facturas']}")
    print(f"\nFacturas:")
    print(f"  Total facturas válidas: {estadisticas_totales['total_facturas_validas']}")
    print(f"  Valor total: ${estadisticas_totales['valor_total_facturas']:,.2f}")
    print(f"\nNotas de crédito:")
    print(f"  Notas únicas aplicadas: {estadisticas_totales['total_notas_aplicadas']}")
    print(f"  Total de aplicaciones: {estadisticas_totales['total_aplicaciones']}")
    print(f"  Valor total aplicado: ${estadisticas_totales['valor_total_aplicado']:,.2f}")

    if estadisticas_totales['archivos_generados']:
        print(f"\nArchivos generados ({len(estadisticas_totales['archivos_generados'])}):")
        for info in estadisticas_totales['archivos_generados']:
            print(f"\n  {info['fecha']}:")
            print(f"    Archivo: {info['archivo']}")
            print(f"    Facturas: {info['num_facturas']}")
            print(f"    Aplicaciones: {info['num_aplicaciones']}")
            print(f"    Valor: ${info['valor_facturas']:,.2f}")

    # Estadísticas finales de BD
    resumen_bd = notas_manager.obtener_resumen_notas()
    print("\n" + "=" * 80)
    print("ESTADO ACTUAL DE NOTAS DE CRÉDITO EN BD")
    print("=" * 80)
    print(f"Notas pendientes: {resumen_bd.get('notas_pendientes', 0)}")
    print(f"Saldo pendiente total: ${resumen_bd.get('saldo_pendiente_total', 0):,.2f}")
    print(f"Notas aplicadas (histórico): {resumen_bd.get('notas_aplicadas', 0)}")
    print(f"Total aplicaciones (histórico): {resumen_bd.get('total_aplicaciones', 0)}")
    print(f"Monto total aplicado (histórico): ${resumen_bd.get('monto_total_aplicado', 0):,.2f}")

    print("\n" + "=" * 80)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Genera facturas diarias con descripción de notas aplicadas (1-9 noviembre 2025)'
    )
    parser.add_argument(
        '--fecha-inicio',
        type=str,
        default='2025-11-01',
        help='Fecha de inicio (YYYY-MM-DD). Default: 2025-11-01'
    )
    parser.add_argument(
        '--fecha-fin',
        type=str,
        default='2025-11-09',
        help='Fecha de fin (YYYY-MM-DD). Default: 2025-11-09'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./output',
        help='Directorio de salida. Default: ./output'
    )

    args = parser.parse_args()

    # Parsear fechas
    try:
        fecha_inicio = datetime.strptime(args.fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(args.fecha_fin, '%Y-%m-%d')

        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")

    except ValueError as e:
        print(f"❌ Error en las fechas: {e}")
        print("Formato esperado: YYYY-MM-DD")
        sys.exit(1)

    # Ejecutar generación
    generar_facturas_con_notas(fecha_inicio, fecha_fin, args.output_dir)
