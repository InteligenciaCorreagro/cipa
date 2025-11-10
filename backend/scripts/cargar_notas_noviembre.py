#!/usr/bin/env python3
"""
Script para cargar notas de crédito válidas del período 1-9 noviembre 2025

Este script:
1. Obtiene documentos de la API SIESA para cada día del período
2. Filtra notas de crédito (prefijo 'N')
3. Valida que tengan tipo de inventario permitido (NO excluido)
4. Registra las notas válidas en la base de datos
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.api_client import SiesaAPIClient
from core.business_rules import BusinessRulesValidator
from core.notas_credito_manager import NotasCreditoManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cargar_notas_periodo(fecha_inicio, fecha_fin, dry_run=False):
    """
    Carga notas de crédito válidas para un período de fechas

    Args:
        fecha_inicio: Fecha inicial del período (datetime)
        fecha_fin: Fecha final del período (datetime)
        dry_run: Si es True, solo muestra qué se cargaría sin hacer cambios
    """
    # Cargar variables de entorno
    load_dotenv()

    CONNI_KEY = os.getenv('CONNI_KEY')
    CONNI_TOKEN = os.getenv('CONNI_TOKEN')
    DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')

    if not all([CONNI_KEY, CONNI_TOKEN]):
        raise ValueError("Faltan variables de entorno: CONNI_KEY y/o CONNI_TOKEN")

    print("=" * 80)
    print("CARGA DE NOTAS DE CRÉDITO - PERÍODO NOVIEMBRE 2025")
    print("=" * 80)
    print(f"\nFecha inicio: {fecha_inicio.strftime('%Y-%m-%d')}")
    print(f"Fecha fin: {fecha_fin.strftime('%Y-%m-%d')}")
    print(f"Modo: {'DRY RUN (sin cambios)' if dry_run else 'PRODUCCIÓN (se harán cambios)'}")

    # Inicializar componentes
    api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
    validator = BusinessRulesValidator()
    notas_manager = NotasCreditoManager(DB_PATH)

    # Mostrar tipos excluidos
    tipos_excluidos = validator.TIPOS_INVENTARIO_EXCLUIDOS
    print(f"\nTipos de inventario excluidos ({len(tipos_excluidos)}):")
    for i, tipo in enumerate(sorted(tipos_excluidos), 1):
        print(f"  {i:2d}. {tipo}")

    # Estadísticas generales
    total_dias = (fecha_fin - fecha_inicio).days + 1
    total_documentos = 0
    total_notas_encontradas = 0
    total_notas_validas = 0
    total_notas_rechazadas = 0
    notas_nuevas_registradas = 0

    notas_rechazadas_detalle = []
    notas_validas_detalle = []

    # Procesar cada día del período
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        print("\n" + "=" * 80)
        print(f"PROCESANDO: {fecha_str}")
        print("=" * 80)

        try:
            # Obtener documentos de la API
            documentos = api_client.obtener_facturas(fecha_actual)

            if not documentos:
                logger.info(f"No se encontraron documentos para {fecha_str}")
                fecha_actual += timedelta(days=1)
                continue

            total_documentos += len(documentos)
            logger.info(f"Total de documentos obtenidos: {len(documentos)}")

            # Separar notas de crédito y validar
            notas_del_dia = []
            for doc in documentos:
                if validator.es_nota_credito(doc):
                    notas_del_dia.append(doc)

            total_notas_encontradas += len(notas_del_dia)
            logger.info(f"Notas de crédito encontradas: {len(notas_del_dia)}")

            if not notas_del_dia:
                fecha_actual += timedelta(days=1)
                continue

            # Validar cada nota por tipo de inventario
            for nota in notas_del_dia:
                numero_nota = f"{nota.get('f_prefijo', '')}{nota.get('f_nrodocto', '')}"
                tipo_inv = validator._obtener_tipo_inventario_normalizado(nota)
                codigo_producto = nota.get('f_cod_ref', '')

                # Validar que tenga código de producto
                if not codigo_producto:
                    logger.warning(f"❌ Nota {numero_nota} sin código de producto - OMITIDA")
                    total_notas_rechazadas += 1
                    notas_rechazadas_detalle.append({
                        'numero_nota': numero_nota,
                        'fecha': fecha_str,
                        'tipo_inventario': tipo_inv,
                        'razon': 'Sin código de producto'
                    })
                    continue

                # Validar tipo de inventario
                if validator.tipo_inventario_permitido(nota):
                    total_notas_validas += 1
                    notas_validas_detalle.append({
                        'numero_nota': numero_nota,
                        'fecha': fecha_str,
                        'tipo_inventario': tipo_inv,
                        'codigo_producto': codigo_producto,
                        'cliente': nota.get('f_cliente_fact_razon_soc', ''),
                        'producto': nota.get('f_desc_item', ''),
                        'valor': nota.get('f_valor_subtotal_local', 0),
                        'cantidad': nota.get('f_cant', 0)
                    })
                    logger.info(f"✅ Nota válida: {numero_nota} | Tipo: {tipo_inv} | "
                              f"Valor: ${nota.get('f_valor_subtotal_local', 0):,.2f}")
                else:
                    total_notas_rechazadas += 1
                    notas_rechazadas_detalle.append({
                        'numero_nota': numero_nota,
                        'fecha': fecha_str,
                        'tipo_inventario': tipo_inv,
                        'razon': f'Tipo de inventario excluido: {tipo_inv}'
                    })
                    logger.warning(f"❌ Nota rechazada: {numero_nota} | Tipo excluido: {tipo_inv}")

        except Exception as e:
            logger.error(f"Error procesando fecha {fecha_str}: {e}")
            raise

        fecha_actual += timedelta(days=1)

    # Resumen de lo encontrado
    print("\n" + "=" * 80)
    print("RESUMEN DEL ANÁLISIS")
    print("=" * 80)
    print(f"\nDías procesados: {total_dias}")
    print(f"Total documentos obtenidos: {total_documentos}")
    print(f"Total notas de crédito encontradas: {total_notas_encontradas}")
    print(f"  ✅ Notas válidas: {total_notas_validas}")
    print(f"  ❌ Notas rechazadas: {total_notas_rechazadas}")

    # Detalle de notas rechazadas
    if notas_rechazadas_detalle:
        print("\n" + "=" * 80)
        print(f"NOTAS RECHAZADAS ({len(notas_rechazadas_detalle)})")
        print("=" * 80)

        # Agrupar por razón de rechazo
        rechazadas_por_razon = {}
        for nota in notas_rechazadas_detalle:
            razon = nota['razon']
            if razon not in rechazadas_por_razon:
                rechazadas_por_razon[razon] = []
            rechazadas_por_razon[razon].append(nota)

        for razon, notas in rechazadas_por_razon.items():
            print(f"\n{razon}: {len(notas)} notas")
            for nota in notas[:5]:
                print(f"  - {nota['numero_nota']} | {nota['fecha']} | Tipo: {nota['tipo_inventario']}")
            if len(notas) > 5:
                print(f"  ... y {len(notas) - 5} notas más")

    # Detalle de notas válidas
    if notas_validas_detalle:
        print("\n" + "=" * 80)
        print(f"NOTAS VÁLIDAS A REGISTRAR ({len(notas_validas_detalle)})")
        print("=" * 80)

        # Agrupar por tipo de inventario
        validas_por_tipo = {}
        for nota in notas_validas_detalle:
            tipo = nota['tipo_inventario'] or 'SIN TIPO'
            if tipo not in validas_por_tipo:
                validas_por_tipo[tipo] = []
            validas_por_tipo[tipo].append(nota)

        valor_total_validas = sum(n['valor'] for n in notas_validas_detalle)

        for tipo, notas in sorted(validas_por_tipo.items()):
            valor_tipo = sum(n['valor'] for n in notas)
            print(f"\n{tipo}: {len(notas)} notas | Valor total: ${valor_tipo:,.2f}")
            for nota in notas[:3]:
                print(f"  - {nota['numero_nota']} | {nota['fecha']} | "
                      f"${nota['valor']:,.2f} | {nota['producto'][:50]}")
            if len(notas) > 3:
                print(f"  ... y {len(notas) - 3} notas más")

        print(f"\n{'='*80}")
        print(f"VALOR TOTAL DE NOTAS VÁLIDAS: ${valor_total_validas:,.2f}")
        print(f"{'='*80}")

    # Registrar en base de datos si no es dry run
    if not dry_run and notas_validas_detalle:
        print("\n" + "=" * 80)
        print("REGISTRANDO NOTAS EN BASE DE DATOS...")
        print("=" * 80)

        # Volver a obtener las notas de la API para registrarlas
        # (necesitamos los objetos completos, no solo el resumen)
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            try:
                documentos = api_client.obtener_facturas(fecha_actual)
                if documentos:
                    # Filtrar y registrar solo las notas válidas
                    for doc in documentos:
                        if validator.es_nota_credito(doc):
                            if validator.tipo_inventario_permitido(doc):
                                codigo_producto = doc.get('f_cod_ref', '')
                                if codigo_producto:  # Solo si tiene código de producto
                                    if notas_manager.registrar_nota_credito(doc):
                                        notas_nuevas_registradas += 1
                                        logger.info(f"✅ Registrada: {doc.get('f_prefijo', '')}{doc.get('f_nrodocto', '')}")
            except Exception as e:
                logger.error(f"Error registrando notas de {fecha_actual.strftime('%Y-%m-%d')}: {e}")

            fecha_actual += timedelta(days=1)

        print(f"\n✅ Notas nuevas registradas en BD: {notas_nuevas_registradas}")
        print(f"(Algunas pueden ser duplicadas y no se registraron)")

        # Mostrar estadísticas de BD
        resumen = notas_manager.obtener_resumen_notas()
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS DE BASE DE DATOS")
        print("=" * 80)
        print(f"Notas pendientes: {resumen.get('notas_pendientes', 0)}")
        print(f"Saldo pendiente total: ${resumen.get('saldo_pendiente_total', 0):,.2f}")
        print(f"Notas aplicadas: {resumen.get('notas_aplicadas', 0)}")
        print(f"Total aplicaciones: {resumen.get('total_aplicaciones', 0)}")
        print(f"Monto total aplicado: ${resumen.get('monto_total_aplicado', 0):,.2f}")

    elif dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN - No se realizaron cambios en la base de datos")
        print("=" * 80)
        print("\nPara ejecutar el registro real, ejecute:")
        print(f"  python3 {os.path.basename(__file__)} --execute")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Carga notas de crédito válidas del 1-9 de noviembre 2025'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Ejecutar carga (por defecto es dry-run)'
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

    # Ejecutar carga
    cargar_notas_periodo(fecha_inicio, fecha_fin, dry_run=not args.execute)
