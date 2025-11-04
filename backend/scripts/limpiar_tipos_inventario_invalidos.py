#!/usr/bin/env python3
"""
Script de limpieza de tipos de inventario inválidos
Elimina registros con tipos DESCESPEC y DESCUENTO de la base de datos

Uso:
    python3 limpiar_tipos_inventario_invalidos.py [--dry-run] [--tipos TIPO1,TIPO2,...]

Opciones:
    --dry-run: Solo muestra qué registros se eliminarían sin borrarlos
    --tipos: Lista de tipos a eliminar separados por coma (por defecto: DESCESPEC,DESCUENTO)
"""

import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Tipos de inventario inválidos por defecto
TIPOS_INVALIDOS_DEFAULT = ['DESCESPEC', 'DESCUENTO']

def conectar_bd():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / 'data' / 'notas_credito.db'
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(str(db_path))


def buscar_registros_invalidos(conn, tipos_invalidos):
    """Busca registros con tipos de inventario inválidos"""
    cursor = conn.cursor()
    resultados = {}

    # Buscar en facturas_rechazadas
    print("\n" + "="*70)
    print("BUSCANDO EN TABLA: facturas_rechazadas")
    print("="*70)

    for tipo in tipos_invalidos:
        cursor.execute(
            'SELECT id, numero_factura, tipo_inventario, razon_rechazo, fecha_registro '
            'FROM facturas_rechazadas WHERE tipo_inventario = ?',
            (tipo,)
        )
        registros = cursor.fetchall()
        if registros:
            resultados.setdefault('facturas_rechazadas', {})[tipo] = registros
            print(f"\n✗ Encontrados {len(registros)} registros con tipo '{tipo}':")
            for i, row in enumerate(registros[:5], 1):
                print(f"  {i}. ID: {row[0]}, Factura: {row[1]}, Razón: {row[3]}, Fecha: {row[4]}")
            if len(registros) > 5:
                print(f"  ... y {len(registros) - 5} más")
        else:
            print(f"✓ No se encontraron registros con tipo '{tipo}'")

    # Buscar en tipos_inventario_detectados
    print("\n" + "="*70)
    print("BUSCANDO EN TABLA: tipos_inventario_detectados")
    print("="*70)

    for tipo in tipos_invalidos:
        cursor.execute(
            'SELECT id, codigo_tipo, descripcion, primera_deteccion, ultima_deteccion, '
            'total_facturas, es_excluido FROM tipos_inventario_detectados WHERE codigo_tipo = ?',
            (tipo,)
        )
        registro = cursor.fetchone()
        if registro:
            resultados.setdefault('tipos_inventario_detectados', {})[tipo] = [registro]
            print(f"\n✗ Encontrado tipo '{tipo}':")
            print(f"  ID: {registro[0]}")
            print(f"  Descripción: {registro[2]}")
            print(f"  Primera detección: {registro[3]}")
            print(f"  Última detección: {registro[4]}")
            print(f"  Total facturas: {registro[5]}")
            print(f"  Es excluido: {registro[6]}")
        else:
            print(f"✓ No se encontró tipo '{tipo}'")

    return resultados


def eliminar_registros(conn, resultados, dry_run=False):
    """Elimina los registros inválidos encontrados"""
    if not resultados:
        print("\n" + "="*70)
        print("✓ NO HAY REGISTROS PARA ELIMINAR")
        print("="*70)
        return

    cursor = conn.cursor()
    total_eliminados = 0

    print("\n" + "="*70)
    if dry_run:
        print("MODO DRY-RUN: Los siguientes registros SERÍAN eliminados:")
    else:
        print("ELIMINANDO REGISTROS:")
    print("="*70)

    # Eliminar de facturas_rechazadas
    if 'facturas_rechazadas' in resultados:
        for tipo, registros in resultados['facturas_rechazadas'].items():
            count = len(registros)
            if not dry_run:
                cursor.execute('DELETE FROM facturas_rechazadas WHERE tipo_inventario = ?', (tipo,))
                total_eliminados += cursor.rowcount
            print(f"{'[DRY-RUN] ' if dry_run else ''}Eliminados {count} registros de facturas_rechazadas con tipo '{tipo}'")

    # Eliminar de tipos_inventario_detectados
    if 'tipos_inventario_detectados' in resultados:
        for tipo, registros in resultados['tipos_inventario_detectados'].items():
            if not dry_run:
                cursor.execute('DELETE FROM tipos_inventario_detectados WHERE codigo_tipo = ?', (tipo,))
                total_eliminados += cursor.rowcount
            print(f"{'[DRY-RUN] ' if dry_run else ''}Eliminado registro de tipos_inventario_detectados con tipo '{tipo}'")

    if not dry_run:
        conn.commit()
        print(f"\n✓ Total de registros eliminados: {total_eliminados}")
        print(f"✓ Cambios guardados en la base de datos")
    else:
        print(f"\n[DRY-RUN] Se eliminarían aproximadamente {sum(len(r) for tabla in resultados.values() for r in tabla.values())} registros")


def generar_reporte(resultados, tipos_invalidos):
    """Genera un reporte de la limpieza"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_path = Path(__file__).parent / f'reporte_limpieza_{timestamp}.txt'

    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("REPORTE DE LIMPIEZA DE TIPOS DE INVENTARIO INVÁLIDOS\n")
        f.write("="*70 + "\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tipos buscados: {', '.join(tipos_invalidos)}\n\n")

        if not resultados:
            f.write("✓ NO SE ENCONTRARON REGISTROS INVÁLIDOS\n")
        else:
            f.write("RESUMEN DE REGISTROS ENCONTRADOS:\n")
            f.write("-"*70 + "\n\n")

            for tabla, tipos_dict in resultados.items():
                f.write(f"Tabla: {tabla}\n")
                for tipo, registros in tipos_dict.items():
                    f.write(f"  - Tipo '{tipo}': {len(registros)} registros\n")
                f.write("\n")

    print(f"\n✓ Reporte guardado en: {reporte_path}")
    return reporte_path


def main():
    parser = argparse.ArgumentParser(
        description='Limpia tipos de inventario inválidos de la base de datos'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo muestra qué registros se eliminarían sin borrarlos'
    )
    parser.add_argument(
        '--tipos',
        type=str,
        default=','.join(TIPOS_INVALIDOS_DEFAULT),
        help=f'Lista de tipos a eliminar separados por coma (default: {",".join(TIPOS_INVALIDOS_DEFAULT)})'
    )

    args = parser.parse_args()
    tipos_invalidos = [t.strip().upper() for t in args.tipos.split(',')]

    print("="*70)
    print("SCRIPT DE LIMPIEZA DE TIPOS DE INVENTARIO INVÁLIDOS")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {'DRY-RUN (sin cambios)' if args.dry_run else 'EJECUCIÓN REAL'}")
    print(f"Tipos a eliminar: {', '.join(tipos_invalidos)}")

    try:
        # Conectar a la base de datos
        conn = conectar_bd()

        # Buscar registros inválidos
        resultados = buscar_registros_invalidos(conn, tipos_invalidos)

        # Eliminar registros (o mostrar qué se eliminaría)
        eliminar_registros(conn, resultados, dry_run=args.dry_run)

        # Generar reporte
        generar_reporte(resultados, tipos_invalidos)

        # Cerrar conexión
        conn.close()

        print("\n" + "="*70)
        print("✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
