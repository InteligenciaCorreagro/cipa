#!/usr/bin/env python3
"""
Script para archivar notas de crédito aplicadas

Uso:
    python3 archivar_notas.py [--dry-run] [--dias-min 30] [--stats]

Opciones:
    --dry-run: Solo muestra qué se archivaría sin hacer cambios
    --dias-min: Días mínimos desde aplicación completa (default: 30)
    --stats: Mostrar estadísticas del archivo
"""

import argparse
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from archivador_notas import ArchivadorNotas


def mostrar_stats(archivador):
    """Muestra estadísticas del archivo"""
    stats = archivador.obtener_estadisticas_archivo()

    print("\n" + "="*80)
    print("ESTADÍSTICAS DEL ARCHIVO")
    print("="*80)
    print(f"Total notas archivadas: {stats.get('total_notas_archivadas', 0):,}")
    print(f"Total aplicaciones archivadas: {stats.get('total_aplicaciones_archivadas', 0):,}")
    print(f"Último archivado: {stats.get('ultimo_archivado', 'Nunca')}")
    print(f"Total operaciones: {stats.get('total_operaciones_archivado', 0):,}")

    if 'tamano_archivo_mb' in stats:
        print(f"Tamaño del archivo: {stats['tamano_archivo_mb']:.2f} MB")


def main():
    parser = argparse.ArgumentParser(
        description='Archiva notas de crédito aplicadas para controlar tamaño de BD'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo muestra qué se archivaría sin hacer cambios'
    )
    parser.add_argument(
        '--dias-min',
        type=int,
        default=30,
        help='Días mínimos desde aplicación completa (default: 30)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostrar estadísticas del archivo y salir'
    )

    args = parser.parse_args()

    print("="*80)
    print("ARCHIVADO DE NOTAS DE CRÉDITO APLICADAS")
    print("="*80)

    archivador = ArchivadorNotas()

    if args.stats:
        mostrar_stats(archivador)
        return 0

    print(f"Modo: {'DRY-RUN (sin cambios)' if args.dry_run else 'EJECUCIÓN REAL'}")
    print(f"Días mínimos: {args.dias_min}")

    try:
        # Obtener candidatas
        notas_candidatas = archivador.obtener_notas_para_archivar(args.dias_min)

        print(f"\n→ Notas candidatas para archivo: {len(notas_candidatas)}")

        if len(notas_candidatas) == 0:
            print("\n✓ No hay notas para archivar")
            return 0

        # Mostrar algunas
        print("\nPrimeras 10 notas:")
        for i, nota in enumerate(notas_candidatas[:10], 1):
            print(f"  {i:2}. Nota: {nota['numero_nota']:12} | "
                  f"Aplicada: {nota['fecha_aplicacion_completa']} | "
                  f"Valor: ${nota['valor_total']:,.2f}")

        if len(notas_candidatas) > 10:
            print(f"\n  ... y {len(notas_candidatas) - 10} notas más")

        # Archivar
        print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Iniciando archivado...")

        stats = archivador.archivar_notas(dias_minimos=args.dias_min, dry_run=args.dry_run)

        print(f"\n" + "="*80)
        print("RESULTADOS DEL ARCHIVADO")
        print("="*80)
        print(f"Notas archivadas: {stats['notas_archivadas']}")
        print(f"Aplicaciones archivadas: {stats['aplicaciones_archivadas']}")
        print(f"Notas restantes en BD principal: {stats['notas_restantes']}")

        if not args.dry_run and stats['espacio_liberado_bytes'] > 0:
            mb_liberados = stats['espacio_liberado_bytes'] / (1024 * 1024)
            print(f"Espacio liberado: {mb_liberados:.2f} MB")

        print(f"\n✓ Archivado completado exitosamente")

        # Mostrar stats finales
        if not args.dry_run:
            mostrar_stats(archivador)

        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
