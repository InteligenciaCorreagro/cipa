#!/usr/bin/env python3
"""
Script para procesar facturas y guardarlas en la base de datos
Genera Excel para operativa y guarda todas las líneas en la BD
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import sqlite3
from collections import defaultdict

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.api_client import SiesaAPIClient
from core.business_rules import BusinessRulesValidator
from core.notas_credito_manager import NotasCreditoManager
from core.excel_processor import ExcelProcessor
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def guardar_facturas_en_bd(facturas_transformadas, notas_por_factura, fecha_proceso, db_path):
    """
    Guarda las facturas procesadas en la base de datos (todas las líneas)

    Args:
        facturas_transformadas: Lista de facturas transformadas para Excel
        notas_por_factura: Dict con notas aplicadas por factura {numero_factura: [notas]}
        fecha_proceso: Fecha del proceso
        db_path: Ruta de la base de datos
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    facturas_guardadas = 0
    facturas_actualizadas = 0

    for factura in facturas_transformadas:
        numero_factura = factura['numero_factura']

        # Determinar si tiene nota aplicada
        tiene_nota = numero_factura in notas_por_factura
        descripcion_nota = None

        if tiene_nota:
            notas_aplicadas = notas_por_factura[numero_factura]
            if len(notas_aplicadas) == 1:
                descripcion_nota = f"Nota aplicada: {notas_aplicadas[0]}"
            else:
                descripcion_nota = f"Notas aplicadas: {', '.join(notas_aplicadas)}"

        try:
            # Insertar o actualizar factura (puede existir si se procesa el mismo día múltiples veces)
            cursor.execute('''
                INSERT INTO facturas (
                    numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                    codigo_producto, nombre_producto, tipo_inventario,
                    valor_total, cantidad, valor_transado, cantidad_transada,
                    descripcion_nota_aplicada, tiene_nota_credito, fecha_proceso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(numero_factura, codigo_producto, fecha_proceso) DO UPDATE SET
                    valor_total = excluded.valor_total,
                    cantidad = excluded.cantidad,
                    valor_transado = excluded.valor_transado,
                    cantidad_transada = excluded.cantidad_transada,
                    descripcion_nota_aplicada = excluded.descripcion_nota_aplicada,
                    tiene_nota_credito = excluded.tiene_nota_credito
            ''', (
                numero_factura,
                factura.get('fecha_factura', fecha_proceso),
                factura.get('nit_cliente', ''),
                factura.get('nombre_cliente', ''),
                factura.get('codigo_producto', ''),
                factura.get('descripcion', ''),  # nombre_producto
                factura.get('tipo_inventario', ''),
                factura.get('valor_total', 0.0),
                factura.get('cantidad', 0.0),
                factura.get('valor_transado', 0.0),
                factura.get('cantidad_transada', 0.0),
                descripcion_nota,
                1 if tiene_nota else 0,
                fecha_proceso
            ))

            if cursor.rowcount > 0:
                facturas_guardadas += 1
            else:
                facturas_actualizadas += 1

        except Exception as e:
            logger.error(f"Error guardando factura {numero_factura}: {e}")
            continue

    conn.commit()
    conn.close()

    logger.info(f"✅ Facturas guardadas en BD: {facturas_guardadas} nuevas, {facturas_actualizadas} actualizadas")
    return facturas_guardadas


def procesar_y_guardar_facturas(fecha_inicio, fecha_fin, output_dir='./output'):
    """
    Procesa facturas, aplica notas y guarda TODO en la base de datos

    Args:
        fecha_inicio: Fecha inicial del período (datetime)
        fecha_fin: Fecha final del período (datetime)
        output_dir: Directorio de salida para los archivos Excel
    """
    # Cargar variables de entorno
    load_dotenv()

    CONNI_KEY = os.getenv('CONNI_KEY')
    CONNI_TOKEN = os.getenv('CONNI_TOKEN')

    # Usar la BD del proyecto raíz
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DB_PATH = Path(os.getenv('DB_PATH', str(PROJECT_ROOT / 'data' / 'notas_credito.db')))

    TEMPLATE_PATH = os.getenv('TEMPLATE_PATH', './templates/plantilla.xlsx')

    if not all([CONNI_KEY, CONNI_TOKEN]):
        raise ValueError("Faltan variables de entorno: CONNI_KEY y/o CONNI_TOKEN")

    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("PROCESAMIENTO Y GUARDADO DE FACTURAS EN BD")
    print("=" * 80)
    print(f"\nFecha inicio: {fecha_inicio.strftime('%Y-%m-%d')}")
    print(f"Fecha fin: {fecha_fin.strftime('%Y-%m-%d')}")
    print(f"Base de datos: {DB_PATH}")
    print(f"Directorio de salida: {output_dir}")

    # Inicializar componentes
    api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
    validator = BusinessRulesValidator()
    notas_manager = NotasCreditoManager(str(DB_PATH))
    excel_processor = ExcelProcessor(TEMPLATE_PATH)

    # Estadísticas generales
    total_dias = (fecha_fin - fecha_inicio).days + 1
    estadisticas_totales = {
        'dias_procesados': 0,
        'dias_con_facturas': 0,
        'total_facturas_validas': 0,
        'total_facturas_guardadas': 0,
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

            # Registrar notas crédito del día
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

            # Crear diccionario de aplicaciones por factura
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
                    logger.info(f"    Estado: {app['estado']}")
                    notas_unicas.add(app['numero_nota'])
                    valor_total_aplicado_dia += app['valor_aplicado']

                estadisticas_totales['total_notas_aplicadas'] += len(notas_unicas)
                estadisticas_totales['total_aplicaciones'] += len(aplicaciones)
                estadisticas_totales['valor_total_aplicado'] += valor_total_aplicado_dia

            # ====================================================================
            # 5. AGREGAR DESCRIPCIÓN DE NOTAS APLICADAS AL EXCEL
            # ====================================================================
            logger.info("Agregando descripción de notas aplicadas...")
            facturas_con_descripcion_notas = 0

            for factura in facturas_transformadas:
                numero_factura = factura['numero_factura']

                if numero_factura in notas_por_factura:
                    notas_aplicadas = notas_por_factura[numero_factura]
                    descripcion_original = factura.get('descripcion', '')

                    if len(notas_aplicadas) == 1:
                        nota_desc = f"Nota aplicada: {notas_aplicadas[0]}"
                    else:
                        nota_desc = f"Notas aplicadas: {', '.join(notas_aplicadas)}"

                    if descripcion_original:
                        factura['descripcion'] = f"{descripcion_original} - {nota_desc}"
                    else:
                        factura['descripcion'] = nota_desc

                    facturas_con_descripcion_notas += 1

            if facturas_con_descripcion_notas > 0:
                logger.info(f"Facturas con descripción de notas: {facturas_con_descripcion_notas}")

            # ====================================================================
            # 6. GUARDAR FACTURAS EN LA BASE DE DATOS
            # ====================================================================
            logger.info("Guardando facturas en la base de datos...")
            facturas_guardadas = guardar_facturas_en_bd(
                facturas_transformadas,
                notas_por_factura,
                fecha_actual.date(),
                DB_PATH
            )
            estadisticas_totales['total_facturas_guardadas'] += facturas_guardadas

            # ====================================================================
            # 7. CALCULAR ESTADÍSTICAS
            # ====================================================================
            valor_total_facturas_dia = sum(f.get('valor_total', 0.0) for f in facturas_transformadas)
            estadisticas_totales['total_facturas_validas'] += len(facturas_transformadas)
            estadisticas_totales['valor_total_facturas'] += valor_total_facturas_dia

            logger.info(f"\nEstadísticas del día:")
            logger.info(f"  Facturas procesadas: {len(facturas_transformadas)}")
            logger.info(f"  Facturas guardadas en BD: {facturas_guardadas}")
            logger.info(f"  Valor total: ${valor_total_facturas_dia:,.2f}")

            # ====================================================================
            # 8. GENERAR EXCEL PARA OPERATIVA
            # ====================================================================
            output_filename = f"facturas_{fecha_actual.strftime('%Y%m%d')}.xlsx"
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
    print(f"  Total facturas procesadas: {estadisticas_totales['total_facturas_validas']}")
    print(f"  Total guardadas en BD: {estadisticas_totales['total_facturas_guardadas']}")
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
        description='Procesa facturas, aplica notas y guarda en BD'
    )
    parser.add_argument(
        '--fecha-inicio',
        type=str,
        required=True,
        help='Fecha de inicio (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--fecha-fin',
        type=str,
        required=True,
        help='Fecha de fin (YYYY-MM-DD)'
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

    # Ejecutar procesamiento
    procesar_y_guardar_facturas(fecha_inicio, fecha_fin, args.output_dir)
