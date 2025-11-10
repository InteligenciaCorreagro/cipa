#!/usr/bin/env python3
"""
Script para limpiar notas de crédito con tipos de inventario excluidos

Este script:
1. Elimina notas de crédito que tienen tipos de inventario excluidos
2. Elimina las aplicaciones relacionadas con esas notas
3. Muestra estadísticas de limpieza
"""

import sys
import os
import sqlite3
from datetime import datetime

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.business_rules import BusinessRulesValidator

# Configuración de base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'notas_credito.db')


def obtener_estadisticas_pre_limpieza(conn):
    """Obtiene estadísticas antes de la limpieza"""
    cursor = conn.cursor()

    # Total de notas
    cursor.execute("SELECT COUNT(*) FROM notas_credito")
    total_notas = cursor.fetchone()[0]

    # Total de aplicaciones
    cursor.execute("SELECT COUNT(*) FROM aplicaciones_notas")
    total_aplicaciones = cursor.fetchone()[0]

    # Notas por tipo de inventario
    cursor.execute("""
        SELECT tipo_inventario, COUNT(*)
        FROM notas_credito
        WHERE tipo_inventario IS NOT NULL AND tipo_inventario != ''
        GROUP BY tipo_inventario
        ORDER BY COUNT(*) DESC
    """)
    notas_por_tipo = cursor.fetchall()

    return {
        'total_notas': total_notas,
        'total_aplicaciones': total_aplicaciones,
        'notas_por_tipo': notas_por_tipo
    }


def limpiar_notas_excluidas(dry_run=False):
    """
    Limpia notas de crédito con tipos de inventario excluidos

    Args:
        dry_run: Si es True, solo muestra qué se eliminaría sin hacer cambios
    """
    validator = BusinessRulesValidator()
    tipos_excluidos = validator.TIPOS_INVENTARIO_EXCLUIDOS

    print("=" * 80)
    print("LIMPIEZA DE NOTAS DE CRÉDITO CON TIPOS EXCLUIDOS")
    print("=" * 80)
    print(f"\nBase de datos: {DB_PATH}")
    print(f"Modo: {'DRY RUN (sin cambios)' if dry_run else 'PRODUCCIÓN (se harán cambios)'}")
    print(f"\nTipos de inventario excluidos ({len(tipos_excluidos)}):")
    for i, tipo in enumerate(sorted(tipos_excluidos), 1):
        print(f"  {i:2d}. {tipo}")

    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Estadísticas pre-limpieza
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS PRE-LIMPIEZA")
        print("=" * 80)
        stats_pre = obtener_estadisticas_pre_limpieza(conn)
        print(f"\nTotal de notas en BD: {stats_pre['total_notas']}")
        print(f"Total de aplicaciones: {stats_pre['total_aplicaciones']}")

        if stats_pre['notas_por_tipo']:
            print(f"\nNotas por tipo de inventario (top 10):")
            for tipo, count in stats_pre['notas_por_tipo'][:10]:
                excluido = "❌ EXCLUIDO" if tipo in tipos_excluidos else "✅ Válido"
                print(f"  {tipo:20s} : {count:5d} notas - {excluido}")

        # Encontrar notas con tipos excluidos
        placeholders = ','.join(['?' for _ in tipos_excluidos])
        query_notas = f"""
            SELECT id, numero_nota, tipo_inventario, valor_total, saldo_pendiente, estado
            FROM notas_credito
            WHERE tipo_inventario IN ({placeholders})
        """
        cursor.execute(query_notas, list(tipos_excluidos))
        notas_a_eliminar = cursor.fetchall()

        if not notas_a_eliminar:
            print("\n✅ No se encontraron notas con tipos excluidos. La BD está limpia.")
            return

        print("\n" + "=" * 80)
        print(f"NOTAS A ELIMINAR: {len(notas_a_eliminar)}")
        print("=" * 80)

        # Agrupar por tipo para mostrar resumen
        notas_por_tipo_excluido = {}
        ids_notas_a_eliminar = []
        valor_total_eliminar = 0

        for nota in notas_a_eliminar:
            tipo = nota['tipo_inventario']
            if tipo not in notas_por_tipo_excluido:
                notas_por_tipo_excluido[tipo] = []
            notas_por_tipo_excluido[tipo].append(nota)
            ids_notas_a_eliminar.append(nota['id'])
            valor_total_eliminar += nota['valor_total']

        print(f"\nResumen por tipo de inventario excluido:")
        for tipo, notas in sorted(notas_por_tipo_excluido.items()):
            print(f"\n  {tipo}:")
            print(f"    Cantidad de notas: {len(notas)}")
            valor_tipo = sum(n['valor_total'] for n in notas)
            print(f"    Valor total: ${valor_tipo:,.2f}")

            # Mostrar primeras 5 notas como ejemplo
            print(f"    Ejemplos:")
            for nota in notas[:5]:
                print(f"      - {nota['numero_nota']} | ${nota['valor_total']:,.2f} | "
                      f"Saldo: ${nota['saldo_pendiente']:,.2f} | Estado: {nota['estado']}")

            if len(notas) > 5:
                print(f"      ... y {len(notas) - 5} notas más")

        print(f"\n{'='*80}")
        print(f"TOTAL A ELIMINAR:")
        print(f"  Notas: {len(notas_a_eliminar)}")
        print(f"  Valor total: ${valor_total_eliminar:,.2f}")

        # Buscar aplicaciones relacionadas
        if ids_notas_a_eliminar:
            placeholders_ids = ','.join(['?' for _ in ids_notas_a_eliminar])
            query_aplicaciones = f"""
                SELECT COUNT(*) as total, SUM(valor_aplicado) as valor_total
                FROM aplicaciones_notas
                WHERE id_nota IN ({placeholders_ids})
            """
            cursor.execute(query_aplicaciones, ids_notas_a_eliminar)
            stats_aplicaciones = cursor.fetchone()

            print(f"\nAPLICACIONES RELACIONADAS A ELIMINAR:")
            print(f"  Cantidad: {stats_aplicaciones['total']}")
            print(f"  Valor total aplicado: ${stats_aplicaciones['valor_total'] or 0:,.2f}")

        # Realizar limpieza si no es dry run
        if not dry_run:
            print("\n" + "=" * 80)
            print("EJECUTANDO LIMPIEZA...")
            print("=" * 80)

            # Eliminar aplicaciones primero (por foreign key)
            if ids_notas_a_eliminar:
                query_delete_aplicaciones = f"""
                    DELETE FROM aplicaciones_notas
                    WHERE id_nota IN ({placeholders_ids})
                """
                cursor.execute(query_delete_aplicaciones, ids_notas_a_eliminar)
                aplicaciones_eliminadas = cursor.rowcount
                print(f"\n✅ Aplicaciones eliminadas: {aplicaciones_eliminadas}")

            # Eliminar notas
            query_delete_notas = f"""
                DELETE FROM notas_credito
                WHERE tipo_inventario IN ({placeholders})
            """
            cursor.execute(query_delete_notas, list(tipos_excluidos))
            notas_eliminadas = cursor.rowcount
            print(f"✅ Notas eliminadas: {notas_eliminadas}")

            # Commit
            conn.commit()
            print("\n✅ Limpieza completada exitosamente")

            # Estadísticas post-limpieza
            print("\n" + "=" * 80)
            print("ESTADÍSTICAS POST-LIMPIEZA")
            print("=" * 80)
            stats_post = obtener_estadisticas_pre_limpieza(conn)
            print(f"\nTotal de notas en BD: {stats_post['total_notas']} "
                  f"(antes: {stats_pre['total_notas']}, eliminadas: {stats_pre['total_notas'] - stats_post['total_notas']})")
            print(f"Total de aplicaciones: {stats_post['total_aplicaciones']} "
                  f"(antes: {stats_pre['total_aplicaciones']}, eliminadas: {stats_pre['total_aplicaciones'] - stats_post['total_aplicaciones']})")

            if stats_post['notas_por_tipo']:
                print(f"\nNotas restantes por tipo de inventario (top 10):")
                for tipo, count in stats_post['notas_por_tipo'][:10]:
                    print(f"  {tipo:20s} : {count:5d} notas")
        else:
            print("\n" + "=" * 80)
            print("DRY RUN - No se realizaron cambios")
            print("=" * 80)
            print("\nPara ejecutar la limpieza real, ejecute:")
            print(f"  python3 {os.path.basename(__file__)} --execute")

    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Limpia notas de crédito con tipos de inventario excluidos'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Ejecutar limpieza (por defecto es dry-run)'
    )

    args = parser.parse_args()

    limpiar_notas_excluidas(dry_run=not args.execute)
