#!/usr/bin/env python3
"""
Script de migración de base de datos - Agregar columnas faltantes
Agrega las columnas tipo_inventario y causal_devolucion a la tabla notas_credito
"""
import sqlite3
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrar_base_datos(db_path: str):
    """
    Migra la base de datos agregando las columnas faltantes

    Args:
        db_path: Ruta a la base de datos SQLite
    """
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada: {db_path}")
        return False

    try:
        logger.info(f"Iniciando migración de base de datos: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar columnas existentes
        cursor.execute("PRAGMA table_info(notas_credito)")
        columnas_existentes = [row[1] for row in cursor.fetchall()]
        logger.info(f"Columnas existentes: {columnas_existentes}")

        # Agregar columna tipo_inventario si no existe
        if 'tipo_inventario' not in columnas_existentes:
            logger.info("Agregando columna 'tipo_inventario'...")
            cursor.execute('ALTER TABLE notas_credito ADD COLUMN tipo_inventario TEXT')
            logger.info("✓ Columna 'tipo_inventario' agregada")
        else:
            logger.info("Columna 'tipo_inventario' ya existe")

        # Agregar columna causal_devolucion si no existe
        if 'causal_devolucion' not in columnas_existentes:
            logger.info("Agregando columna 'causal_devolucion'...")
            cursor.execute('ALTER TABLE notas_credito ADD COLUMN causal_devolucion TEXT')
            logger.info("✓ Columna 'causal_devolucion' agregada")
        else:
            logger.info("Columna 'causal_devolucion' ya existe")

        conn.commit()

        # Verificar cambios
        cursor.execute("PRAGMA table_info(notas_credito)")
        columnas_nuevas = [row[1] for row in cursor.fetchall()]
        logger.info(f"Columnas después de migración: {columnas_nuevas}")

        conn.close()

        logger.info("✅ Migración completada exitosamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    db_path = './data/notas_credito.db'

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    exito = migrar_base_datos(db_path)
    sys.exit(0 if exito else 1)
