#!/usr/bin/env python3
"""
Script para crear la tabla de facturas válidas en la base de datos
"""
import sqlite3
import sys
from pathlib import Path

def main():
    """Crear tabla facturas si no existe"""

    # Ruta de la base de datos
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data' / 'notas_credito.db'

    print(f"\n{'='*60}")
    print(f"📊 CREANDO TABLA DE FACTURAS VÁLIDAS")
    print(f"{'='*60}\n")
    print(f"Base de datos: {db_path}\n")

    if not db_path.exists():
        print(f"❌ La base de datos no existe en: {db_path}")
        print(f"   Se creará automáticamente al ejecutar el proceso.")
        return 1

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar si la tabla ya existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='facturas'")
        if cursor.fetchone():
            print(f"⚠️  La tabla 'facturas' ya existe. No se creará de nuevo.")

            # Mostrar cuántas facturas hay
            cursor.execute("SELECT COUNT(*) FROM facturas")
            count = cursor.fetchone()[0]
            print(f"   Facturas registradas: {count}")
        else:
            print(f"✅ Creando tabla 'facturas'...")

            # Crear tabla de facturas válidas
            cursor.execute('''
                CREATE TABLE facturas (
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
                    valor_nota_aplicada REAL DEFAULT 0,
                    cantidad_nota_aplicada REAL DEFAULT 0,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(numero_factura, codigo_producto)
                )
            ''')

            # Crear índices para mejorar el rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_factura)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(nit_cliente)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_notas ON facturas(tiene_nota_credito)')

            conn.commit()
            print(f"✅ Tabla 'facturas' creada exitosamente")
            print(f"✅ Índices creados")

        # Mostrar todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tablas = [t[0] for t in cursor.fetchall()]

        print(f"\n{'='*60}")
        print(f"📋 TABLAS EN LA BASE DE DATOS ({len(tablas)})")
        print(f"{'='*60}\n")

        for tabla in tablas:
            if tabla == 'sqlite_sequence':
                continue

            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"  - {tabla:<30} {count:>10,} registros")

        conn.close()

        print(f"\n{'='*60}")
        print(f"✅ PROCESO COMPLETADO")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
