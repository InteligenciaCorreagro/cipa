#!/usr/bin/env python3
"""
Script para limpiar notas inválidas de la base de datos

Elimina:
1. Notas con tipos de inventario excluidos
2. Notas sin tipo que tengan "DESCUENTO" o "DESCESPEC" en el nombre
"""
import sqlite3
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.business_rules import BusinessRulesValidator


def limpiar_notas_invalidas(dry_run=False):
    """
    Elimina notas inválidas de la base de datos

    Args:
        dry_run: Si es True, solo muestra lo que se eliminaría sin hacer cambios
    """
    db_path = backend_path / 'data' / 'notas_credito.db'

    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Obtener tipos excluidos
    validator = BusinessRulesValidator()
    tipos_excluidos = validator.TIPOS_INVENTARIO_EXCLUIDOS

    print("="*80)
    print("LIMPIEZA DE NOTAS INVÁLIDAS")
    print("="*80)
    print(f"Modo: {'DRY-RUN (sin cambios)' if dry_run else 'EJECUCIÓN REAL'}")
    print()

    # 1. Buscar notas con tipos excluidos
    placeholders = ','.join(['?'] * len(tipos_excluidos))
    cursor.execute(f"""
        SELECT id, numero_nota, nombre_producto, tipo_inventario, valor_total, estado
        FROM notas_credito
        WHERE tipo_inventario IN ({placeholders})
    """, list(tipos_excluidos))

    notas_tipo_excluido = cursor.fetchall()

    # 2. Buscar notas sin tipo con "DESCUENTO" en el nombre
    cursor.execute("""
        SELECT id, numero_nota, nombre_producto, tipo_inventario, valor_total, estado
        FROM notas_credito
        WHERE (tipo_inventario IS NULL OR tipo_inventario = '')
          AND (UPPER(nombre_producto) LIKE '%DESCUENTO%' OR UPPER(nombre_producto) LIKE '%DESCESPEC%')
    """)

    notas_descuento_sin_tipo = cursor.fetchall()

    # Mostrar resumen
    print("NOTAS A ELIMINAR:")
    print("-"*80)
    print(f"1. Notas con tipos excluidos: {len(notas_tipo_excluido)}")
    print(f"2. Notas sin tipo con DESCUENTO: {len(notas_descuento_sin_tipo)}")
    print(f"\nTotal a eliminar: {len(notas_tipo_excluido) + len(notas_descuento_sin_tipo)} notas")
    print()

    # Mostrar ejemplos
    if notas_tipo_excluido:
        print("\n📋 Notas con tipos excluidos:")
        for i, nota in enumerate(notas_tipo_excluido[:10], 1):
            id_nota, numero, nombre, tipo_inv, valor, estado = nota
            print(f"  {i:2}. {numero:15} | Tipo: {tipo_inv:20} | ${valor:12,.2f} | {estado}")
            print(f"      {nombre[:70]}")

        if len(notas_tipo_excluido) > 10:
            print(f"      ... y {len(notas_tipo_excluido) - 10} más")

    if notas_descuento_sin_tipo:
        print("\n📋 Notas sin tipo con DESCUENTO:")
        for i, nota in enumerate(notas_descuento_sin_tipo[:10], 1):
            id_nota, numero, nombre, tipo_inv, valor, estado = nota
            print(f"  {i:2}. {numero:15} | Tipo: {tipo_inv or 'NULL':20} | ${valor:12,.2f} | {estado}")
            print(f"      {nombre[:70]}")

        if len(notas_descuento_sin_tipo) > 10:
            print(f"      ... y {len(notas_descuento_sin_tipo) - 10} más")

    # Calcular totales
    total_eliminar = len(notas_tipo_excluido) + len(notas_descuento_sin_tipo)
    valor_total = sum(nota[4] for nota in notas_tipo_excluido + notas_descuento_sin_tipo)

    print("\n" + "="*80)
    print(f"RESUMEN: {total_eliminar} notas | Valor total: ${valor_total:,.2f}")
    print("="*80)

    if total_eliminar == 0:
        print("\n✅ No hay notas para eliminar")
        conn.close()
        return 0

    # Eliminar si no es dry-run
    if not dry_run:
        print("\n🗑️  Eliminando notas...")

        # Obtener IDs a eliminar
        ids_eliminar = [nota[0] for nota in notas_tipo_excluido + notas_descuento_sin_tipo]

        # Eliminar aplicaciones relacionadas primero
        placeholders_ids = ','.join(['?'] * len(ids_eliminar))
        cursor.execute(f"""
            DELETE FROM aplicaciones_notas
            WHERE id_nota IN ({placeholders_ids})
        """, ids_eliminar)

        aplicaciones_eliminadas = cursor.rowcount
        print(f"   - Aplicaciones eliminadas: {aplicaciones_eliminadas}")

        # Eliminar notas
        cursor.execute(f"""
            DELETE FROM notas_credito
            WHERE id IN ({placeholders_ids})
        """, ids_eliminar)

        notas_eliminadas = cursor.rowcount
        print(f"   - Notas eliminadas: {notas_eliminadas}")

        # Commit
        conn.commit()
        print("\n✅ Cambios guardados en la base de datos")

        # Mostrar estadísticas finales
        cursor.execute("SELECT COUNT(*) FROM notas_credito")
        total_restante = cursor.fetchone()[0]
        print(f"\n📊 Notas restantes en la BD: {total_restante}")

    else:
        print("\n[DRY-RUN] No se realizaron cambios")
        print(f"Para ejecutar la limpieza real, ejecute sin --dry-run")

    conn.close()
    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Limpia notas inválidas de la base de datos'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo muestra lo que se eliminaría sin hacer cambios'
    )

    args = parser.parse_args()

    return limpiar_notas_invalidas(dry_run=args.dry_run)


if __name__ == '__main__':
    exit(main())
