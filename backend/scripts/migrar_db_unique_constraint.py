#!/usr/bin/env python3
"""
Script de migración de base de datos - Cambiar UNIQUE constraint
Permite que una nota de crédito tenga múltiples líneas (productos)
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

def migrar_unique_constraint(db_path: str):
    """
    Migra la base de datos cambiando el constraint UNIQUE de numero_nota
    a UNIQUE(numero_nota, codigo_producto) para permitir múltiples líneas por nota

    Args:
        db_path: Ruta a la base de datos SQLite
    """
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada: {db_path}")
        return False

    try:
        logger.info(f"Iniciando migración de constraint UNIQUE: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Obtener datos existentes
        logger.info("Respaldando datos existentes...")
        cursor.execute("SELECT * FROM notas_credito")
        datos_existentes = cursor.fetchall()
        logger.info(f"Total de registros a migrar: {len(datos_existentes)}")

        # Obtener nombres de columnas
        cursor.execute("PRAGMA table_info(notas_credito)")
        columnas_info = cursor.fetchall()
        columnas = [col[1] for col in columnas_info]
        logger.info(f"Columnas: {columnas}")

        # Renombrar tabla antigua
        logger.info("Renombrando tabla antigua...")
        cursor.execute("ALTER TABLE notas_credito RENAME TO notas_credito_old")

        # Crear nueva tabla con constraint correcto
        logger.info("Creando nueva tabla con constraint UNIQUE(numero_nota, codigo_producto)...")
        cursor.execute('''
            CREATE TABLE notas_credito (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_nota TEXT NOT NULL,
                fecha_nota DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT,
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,
                saldo_pendiente REAL NOT NULL,
                cantidad_pendiente REAL NOT NULL,
                causal_devolucion TEXT,
                estado TEXT DEFAULT 'PENDIENTE',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aplicacion_completa TIMESTAMP NULL,
                UNIQUE(numero_nota, codigo_producto)
            )
        ''')

        # Migrar datos
        logger.info("Migrando datos a nueva tabla...")
        cursor.execute('''
            INSERT INTO notas_credito
            (id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
             codigo_producto, nombre_producto, tipo_inventario, valor_total, cantidad,
             saldo_pendiente, cantidad_pendiente, causal_devolucion, estado,
             fecha_registro, fecha_aplicacion_completa)
            SELECT id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                   codigo_producto, nombre_producto, tipo_inventario, valor_total, cantidad,
                   saldo_pendiente, cantidad_pendiente, causal_devolucion, estado,
                   fecha_registro, fecha_aplicacion_completa
            FROM notas_credito_old
        ''')

        migrados = cursor.rowcount
        logger.info(f"Registros migrados: {migrados}")

        # Eliminar tabla antigua
        logger.info("Eliminando tabla antigua...")
        cursor.execute("DROP TABLE notas_credito_old")

        # Recrear índices
        logger.info("Recreando índices...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notas_cliente_producto
            ON notas_credito(nit_cliente, codigo_producto, estado)
        ''')

        conn.commit()

        # Verificar migración
        cursor.execute("SELECT COUNT(*) FROM notas_credito")
        total_final = cursor.fetchone()[0]
        logger.info(f"Total de registros en nueva tabla: {total_final}")

        # Verificar constraint
        cursor.execute("PRAGMA table_info(notas_credito)")
        logger.info("Estructura final de tabla verificada")

        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notas_credito'")
        sql_tabla = cursor.fetchone()[0]
        logger.info(f"SQL de tabla:\n{sql_tabla}")

        conn.close()

        logger.info("✅ Migración completada exitosamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()

        # Intentar rollback
        try:
            if 'cursor' in locals():
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notas_credito_old'")
                if cursor.fetchone():
                    logger.info("Intentando rollback...")
                    cursor.execute("DROP TABLE IF EXISTS notas_credito")
                    cursor.execute("ALTER TABLE notas_credito_old RENAME TO notas_credito")
                    conn.commit()
                    logger.info("Rollback completado")
        except:
            pass

        return False

if __name__ == "__main__":
    db_path = './data/notas_credito.db'

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    exito = migrar_unique_constraint(db_path)
    sys.exit(0 if exito else 1)
