#!/usr/bin/env python3
"""
Script para arreglar la tabla facturas agregando columnas faltantes
"""
import sqlite3
import sys
from pathlib import Path

def main():
    db_path = Path(__file__).parent.parent / 'data' / 'notas_credito.db'

    print(f"\n{'='*60}")
    print(f"🔧 ARREGLANDO TABLA FACTURAS")
    print(f"{'='*60}\n")
    print(f"Base de datos: {db_path}\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ver esquema actual
        cursor.execute("PRAGMA table_info(facturas)")
        columnas_actuales = [col[1] for col in cursor.fetchall()]

        print(f"Columnas actuales ({len(columnas_actuales)}):")
        for col in columnas_actuales:
            print(f"  - {col}")

        # Verificar qué columnas faltan
        columnas_requeridas = [
            'id', 'numero_factura', 'fecha_factura', 'nit_cliente', 'nombre_cliente',
            'codigo_producto', 'nombre_producto', 'tipo_inventario', 'valor_total',
            'cantidad', 'valor_unitario', 'estado', 'tiene_nota_credito',
            'valor_nota_aplicada', 'cantidad_nota_aplicada', 'fecha_registro'
        ]

        columnas_faltantes = [col for col in columnas_requeridas if col not in columnas_actuales]

        if columnas_faltantes:
            print(f"\n⚠️  Columnas faltantes ({len(columnas_faltantes)}):")
            for col in columnas_faltantes:
                print(f"  - {col}")

            print(f"\n{'='*60}")
            print("SOLUCIÓN: Recrear tabla con esquema completo")
            print(f"{'='*60}\n")

            # Guardar datos existentes si los hay
            cursor.execute("SELECT COUNT(*) FROM facturas")
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"⚠️  La tabla tiene {count} registros. Se harán backup.")
                cursor.execute("CREATE TABLE facturas_backup AS SELECT * FROM facturas")
                print(f"✅ Backup creado en tabla facturas_backup")

            # Eliminar tabla actual
            cursor.execute("DROP TABLE facturas")
            print(f"✅ Tabla anterior eliminada")

            # Eliminar índices antiguos si existen
            cursor.execute("DROP INDEX IF EXISTS idx_facturas_fecha")
            cursor.execute("DROP INDEX IF EXISTS idx_facturas_cliente")
            cursor.execute("DROP INDEX IF EXISTS idx_facturas_numero")
            cursor.execute("DROP INDEX IF EXISTS idx_facturas_notas")

            # Crear tabla con esquema completo
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
            print(f"✅ Tabla recreada con esquema completo")

            # Crear índices
            cursor.execute('CREATE INDEX idx_facturas_fecha ON facturas(fecha_factura)')
            cursor.execute('CREATE INDEX idx_facturas_cliente ON facturas(nit_cliente)')
            cursor.execute('CREATE INDEX idx_facturas_numero ON facturas(numero_factura)')
            cursor.execute('CREATE INDEX idx_facturas_notas ON facturas(tiene_nota_credito)')
            print(f"✅ Índices creados")

            # Restaurar datos si había backup
            if count > 0:
                print(f"\nRestaurando datos desde backup...")
                # Aquí podrías migrar datos si fuera necesario
                # Por ahora dejamos la tabla limpia
                print(f"⚠️  Tabla limpia. Los datos están en facturas_backup si los necesitas.")

            conn.commit()

            print(f"\n{'='*60}")
            print("✅ TABLA ARREGLADA EXITOSAMENTE")
            print(f"{'='*60}")

            # Verificar esquema final
            cursor.execute("PRAGMA table_info(facturas)")
            columnas_finales = cursor.fetchall()

            print(f"\nEsquema final ({len(columnas_finales)} columnas):")
            for col in columnas_finales:
                tipo = col[2]
                notnull = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                pk = " PRIMARY KEY" if col[5] else ""
                print(f"  {col[1]:<25} {tipo}{notnull}{default}{pk}")

        else:
            print(f"\n✅ La tabla ya tiene todas las columnas necesarias")

        conn.close()

        print(f"\n{'='*60}\n")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
