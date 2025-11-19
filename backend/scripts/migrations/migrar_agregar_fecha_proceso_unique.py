#!/usr/bin/env python3
"""
Migración: Agregar fecha_proceso al UNIQUE constraint de la tabla facturas

Problema: El constraint actual UNIQUE(numero_factura, codigo_producto) causa que
facturas procesadas en días diferentes sobrescriban registros anteriores.

Solución: Cambiar el constraint a UNIQUE(numero_factura, codigo_producto, fecha_proceso)
para que cada procesamiento diario guarde sus propias líneas.
"""
import sqlite3
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrar_tabla_facturas(db_path: str):
    """
    Migra la tabla facturas para incluir fecha_proceso en el UNIQUE constraint
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        logger.info("Iniciando migración de tabla facturas...")

        # 1. Verificar que la tabla existe
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='facturas'
        """)
        if not cursor.fetchone():
            logger.error("La tabla 'facturas' no existe")
            return False

        # 2. Verificar si ya tiene fecha_proceso como columna
        cursor.execute("PRAGMA table_info(facturas)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        tiene_fecha_proceso = 'fecha_proceso' in columns

        # 3. Crear tabla temporal con la nueva estructura
        logger.info("Creando tabla temporal con nueva estructura...")
        cursor.execute('''
            CREATE TABLE facturas_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT NOT NULL,
                fecha_factura DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT,
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,
                valor_unitario REAL,
                estado TEXT DEFAULT 'PROCESADA',
                tiene_nota_credito INTEGER DEFAULT 0,
                numero_nota_aplicada TEXT,
                valor_nota_aplicada REAL DEFAULT 0,
                cantidad_nota_aplicada REAL DEFAULT 0,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_proceso DATE,
                UNIQUE(numero_factura, codigo_producto, fecha_proceso)
            )
        ''')

        # 4. Copiar datos existentes
        logger.info("Copiando datos existentes...")
        # Obtener columnas de la tabla original
        cursor.execute("PRAGMA table_info(facturas)")
        columnas_originales = {col[1] for col in cursor.fetchall()}

        tiene_numero_nota = 'numero_nota_aplicada' in columnas_originales

        if tiene_fecha_proceso:
            # La tabla ya tiene fecha_proceso, copiar todo
            cursor.execute('''
                INSERT INTO facturas_new
                SELECT * FROM facturas
            ''')
        else:
            # No tiene fecha_proceso, usar fecha_factura como fecha_proceso
            if tiene_numero_nota:
                # Tiene columna numero_nota_aplicada
                cursor.execute('''
                    INSERT INTO facturas_new
                    (id, numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                     codigo_producto, nombre_producto, tipo_inventario,
                     valor_total, cantidad, valor_unitario, estado,
                     tiene_nota_credito, numero_nota_aplicada, valor_nota_aplicada,
                     cantidad_nota_aplicada, fecha_registro, fecha_proceso)
                    SELECT
                        id, numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                        codigo_producto, nombre_producto, tipo_inventario,
                        valor_total, cantidad, valor_unitario, estado,
                        tiene_nota_credito, numero_nota_aplicada, valor_nota_aplicada,
                        cantidad_nota_aplicada, fecha_registro, fecha_factura as fecha_proceso
                    FROM facturas
                ''')
            else:
                # No tiene numero_nota_aplicada, usar NULL
                cursor.execute('''
                    INSERT INTO facturas_new
                    (id, numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                     codigo_producto, nombre_producto, tipo_inventario,
                     valor_total, cantidad, valor_unitario, estado,
                     tiene_nota_credito, numero_nota_aplicada, valor_nota_aplicada,
                     cantidad_nota_aplicada, fecha_registro, fecha_proceso)
                    SELECT
                        id, numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                        codigo_producto, nombre_producto, tipo_inventario,
                        valor_total, cantidad, valor_unitario, estado,
                        tiene_nota_credito, NULL, valor_nota_aplicada,
                        cantidad_nota_aplicada, fecha_registro, fecha_factura as fecha_proceso
                    FROM facturas
                ''')

        registros_copiados = cursor.rowcount
        logger.info(f"Registros copiados: {registros_copiados}")

        # 5. Eliminar tabla vieja
        logger.info("Eliminando tabla antigua...")
        cursor.execute('DROP TABLE facturas')

        # 6. Renombrar tabla nueva
        logger.info("Renombrando tabla nueva...")
        cursor.execute('ALTER TABLE facturas_new RENAME TO facturas')

        # 7. Recrear índices
        logger.info("Recreando índices...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(nit_cliente)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_notas ON facturas(tiene_nota_credito)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha_proceso ON facturas(fecha_proceso)')

        conn.commit()
        logger.info("✅ Migración completada exitosamente")

        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM facturas")
        total = cursor.fetchone()[0]
        logger.info(f"Total de registros en tabla migrada: {total}")

        return True

    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    # Detectar ruta de la BD
    project_root = Path(__file__).parent.parent.parent.parent
    db_path = project_root / 'data' / 'notas_credito.db'

    logger.info(f"Base de datos: {db_path}")

    if not db_path.exists():
        logger.error(f"La base de datos no existe: {db_path}")
        sys.exit(1)

    # Hacer backup
    import shutil
    from datetime import datetime
    backup_path = db_path.with_suffix(f'.db.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    logger.info(f"Creando backup: {backup_path}")
    shutil.copy(db_path, backup_path)

    # Ejecutar migración
    if migrar_tabla_facturas(str(db_path)):
        logger.info("\n✅ Migración exitosa")
        logger.info(f"📦 Backup disponible en: {backup_path}")
        sys.exit(0)
    else:
        logger.error("\n❌ Migración fallida")
        logger.info(f"📦 Puedes restaurar desde: {backup_path}")
        sys.exit(1)
