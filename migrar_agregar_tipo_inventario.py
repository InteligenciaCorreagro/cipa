#!/usr/bin/env python3
"""
Script de migración para agregar campo tipo_inventario a tabla notas_credito

Uso:
    python3 migrar_agregar_tipo_inventario.py [--backup]

Opciones:
    --backup: Crear backup antes de la migración
"""

import sqlite3
import argparse
import shutil
from datetime import datetime
from pathlib import Path


def crear_backup(db_path):
    """Crea un backup de la base de datos"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(__file__).parent / 'backups'
    backup_dir.mkdir(exist_ok=True)

    backup_path = backup_dir / f'notas_credito_backup_{timestamp}.db'
    shutil.copy2(db_path, backup_path)

    print(f"✓ Backup creado en: {backup_path}")
    return backup_path


def verificar_columna_existe(cursor, tabla, columna):
    """Verifica si una columna ya existe en una tabla"""
    cursor.execute(f'PRAGMA table_info({tabla})')
    columnas = [row[1] for row in cursor.fetchall()]
    return columna in columnas


def migrar_base_datos(db_path, crear_backup_flag=True):
    """Realiza la migración de la base de datos"""

    print("="*70)
    print("MIGRACIÓN: Agregar campo tipo_inventario a notas_credito")
    print("="*70)

    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")

    # Backup
    if crear_backup_flag:
        crear_backup(db_path)

    # Conectar a la BD
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Verificar si la columna ya existe
        if verificar_columna_existe(cursor, 'notas_credito', 'tipo_inventario'):
            print("\n✓ La columna 'tipo_inventario' ya existe en la tabla notas_credito")
            return

        print("\n→ Agregando columna 'tipo_inventario' a tabla notas_credito...")

        # Agregar la columna
        cursor.execute('''
            ALTER TABLE notas_credito
            ADD COLUMN tipo_inventario TEXT
        ''')

        # Crear índice para mejorar búsquedas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notas_tipo_inventario
            ON notas_credito(tipo_inventario)
        ''')

        conn.commit()

        print("✓ Columna agregada exitosamente")

        # Estadísticas
        cursor.execute('SELECT COUNT(*) FROM notas_credito')
        total_notas = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM notas_credito WHERE tipo_inventario IS NULL')
        notas_sin_tipo = cursor.fetchone()[0]

        print(f"\n=== ESTADÍSTICAS ===")
        print(f"Total de notas: {total_notas}")
        print(f"Notas sin tipo de inventario: {notas_sin_tipo}")

        if notas_sin_tipo > 0:
            print(f"\n⚠️  Hay {notas_sin_tipo} notas sin tipo de inventario.")
            print("   Estas notas se actualizarán automáticamente en la próxima ejecución del sistema.")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    print("\n✓ Migración completada exitosamente")


def main():
    parser = argparse.ArgumentParser(
        description='Migración: Agregar campo tipo_inventario a tabla notas_credito'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Crear backup antes de migrar (default: True)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='NO crear backup (usar con precaución)'
    )

    args = parser.parse_args()

    db_path = Path(__file__).parent / 'data' / 'notas_credito.db'

    try:
        migrar_base_datos(db_path, crear_backup_flag=not args.no_backup)

        print("\n" + "="*70)
        print("✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        return 0

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
