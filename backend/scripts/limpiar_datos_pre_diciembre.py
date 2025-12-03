#!/usr/bin/env python3
"""
Script para limpiar datos anteriores a diciembre 2025
Mantiene solo datos desde diciembre 2025 en adelante
"""
import sqlite3
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def limpiar_datos(db_path='./data/notas_credito.db', fecha_limite='2025-12-01', dry_run=False):
    """
    Elimina datos anteriores a la fecha límite

    Args:
        db_path: Ruta de la base de datos
        fecha_limite: Fecha límite (formato: YYYY-MM-DD)
        dry_run: Si es True, solo muestra lo que se haría sin ejecutar
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("="*80)
    logger.info(f"LIMPIEZA DE DATOS PRE-{fecha_limite}")
    logger.info(f"Modo: {'DRY RUN (simulación)' if dry_run else 'EJECUCIÓN REAL'}")
    logger.info("="*80 + "\n")

    try:
        # 1. Limpiar aplicaciones_notas
        logger.info("1️⃣  TABLA: aplicaciones_notas")
        logger.info("-"*80)

        cursor.execute(f"SELECT COUNT(*) FROM aplicaciones_notas WHERE fecha_factura < '{fecha_limite}'")
        count = cursor.fetchone()[0]
        logger.info(f"   Registros a eliminar: {count}")

        if not dry_run and count > 0:
            cursor.execute(f"DELETE FROM aplicaciones_notas WHERE fecha_factura < '{fecha_limite}'")
            logger.info(f"   ✅ Eliminados: {cursor.rowcount} registros")

        cursor.execute("SELECT COUNT(*) FROM aplicaciones_notas")
        total_restante = cursor.fetchone()[0]
        logger.info(f"   Registros restantes: {total_restante}\n")

        # 2. Limpiar facturas
        logger.info("2️⃣  TABLA: facturas")
        logger.info("-"*80)

        cursor.execute(f"SELECT COUNT(*) FROM facturas WHERE fecha_factura < '{fecha_limite}'")
        count = cursor.fetchone()[0]
        logger.info(f"   Registros a eliminar: {count}")

        if not dry_run and count > 0:
            cursor.execute(f"DELETE FROM facturas WHERE fecha_factura < '{fecha_limite}'")
            logger.info(f"   ✅ Eliminados: {cursor.rowcount} registros")

        cursor.execute("SELECT COUNT(*) FROM facturas")
        total_restante = cursor.fetchone()[0]
        logger.info(f"   Registros restantes: {total_restante}\n")

        # 3. Limpiar facturas_rechazadas
        logger.info("3️⃣  TABLA: facturas_rechazadas")
        logger.info("-"*80)

        cursor.execute(f"SELECT COUNT(*) FROM facturas_rechazadas WHERE fecha_factura < '{fecha_limite}'")
        count = cursor.fetchone()[0]
        logger.info(f"   Registros a eliminar: {count}")

        if not dry_run and count > 0:
            cursor.execute(f"DELETE FROM facturas_rechazadas WHERE fecha_factura < '{fecha_limite}'")
            logger.info(f"   ✅ Eliminados: {cursor.rowcount} registros")

        cursor.execute("SELECT COUNT(*) FROM facturas_rechazadas")
        total_restante = cursor.fetchone()[0]
        logger.info(f"   Registros restantes: {total_restante}\n")

        # 4. Limpiar notas_credito
        logger.info("4️⃣  TABLA: notas_credito")
        logger.info("-"*80)

        cursor.execute(f"SELECT COUNT(*) FROM notas_credito WHERE fecha_nota < '{fecha_limite}'")
        count = cursor.fetchone()[0]
        logger.info(f"   Registros a eliminar: {count}")

        if not dry_run and count > 0:
            cursor.execute(f"DELETE FROM notas_credito WHERE fecha_nota < '{fecha_limite}'")
            logger.info(f"   ✅ Eliminados: {cursor.rowcount} registros")

        cursor.execute("SELECT COUNT(*) FROM notas_credito")
        total_restante = cursor.fetchone()[0]
        logger.info(f"   Registros restantes: {total_restante}\n")

        # 5. Opcional: Limpiar tipos_inventario_detectados
        # Esta tabla no tiene fecha_factura, solo fechas de detección
        # Podemos dejarla como está o limpiarla según primera_deteccion
        logger.info("5️⃣  TABLA: tipos_inventario_detectados")
        logger.info("-"*80)
        logger.info("   ℹ️  Esta tabla se mantiene sin cambios (contiene metadatos)\n")

        if not dry_run:
            # Commit de cambios
            conn.commit()
            logger.info("="*80)
            logger.info("✅ LIMPIEZA COMPLETADA Y GUARDADA")
            logger.info("="*80)

            # VACUUM para reducir el tamaño del archivo
            logger.info("\n🔧 Optimizando base de datos (VACUUM)...")
            cursor.execute("VACUUM")
            logger.info("✅ Base de datos optimizada\n")
        else:
            logger.info("="*80)
            logger.info("ℹ️  DRY RUN COMPLETADO - NO SE REALIZARON CAMBIOS")
            logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ Error durante la limpieza: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Función principal"""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description='Limpieza de datos anteriores a diciembre 2025',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Dry run (simulación) - ver qué se eliminaría
  python limpiar_datos_pre_diciembre.py --dry-run

  # Ejecutar limpieza real
  python limpiar_datos_pre_diciembre.py

  # Especificar otra fecha límite
  python limpiar_datos_pre_diciembre.py --fecha-limite 2025-11-01
        """
    )

    parser.add_argument(
        '--db-path',
        default='./data/notas_credito.db',
        help='Ruta de la base de datos (default: ./data/notas_credito.db)'
    )

    parser.add_argument(
        '--fecha-limite',
        default='2025-12-01',
        help='Fecha límite (formato: YYYY-MM-DD). Se eliminarán datos anteriores. (default: 2025-12-01)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo simulación: muestra qué se eliminaría sin hacer cambios'
    )

    args = parser.parse_args()

    try:
        os.chdir('/home/user/cipa')
        limpiar_datos(args.db_path, args.fecha_limite, args.dry_run)
        return 0

    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
