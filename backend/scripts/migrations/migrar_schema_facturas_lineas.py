#!/usr/bin/env python3
"""
Migración: Corregir schema de tabla facturas para soportar líneas individuales

PROBLEMA IDENTIFICADO:
- La tabla actual tiene constraint: UNIQUE(numero_factura, codigo_producto)
- Faltan columnas necesarias para el procesamiento correcto
- El promedio de líneas por factura es 1.0 (AGRUPACIÓN INCORRECTA)

SOLUCIÓN:
1. Crear nueva tabla con schema correcto
2. Migrar datos existentes
3. Reemplazar tabla antigua con nueva

Schema correcto:
- UNIQUE(numero_factura, codigo_producto, fecha_proceso)
- Columnas: valor_transado, cantidad_transada, descripcion_nota_aplicada
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Usar la BD del proyecto raíz
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'notas_credito.db'

def verificar_schema_actual():
    """Verificar el schema actual de la tabla"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='facturas'")
    result = cursor.fetchone()

    if not result:
        print("❌ La tabla 'facturas' no existe")
        conn.close()
        return None

    schema = result[0]
    conn.close()
    return schema


def crear_backup():
    """Crear backup de la tabla actual"""
    print("\n" + "=" * 80)
    print("1. CREANDO BACKUP DE LA TABLA ACTUAL")
    print("=" * 80)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_table = f'facturas_backup_{timestamp}'

    try:
        # Verificar que la tabla original existe
        cursor.execute("SELECT COUNT(*) FROM facturas")
        count = cursor.fetchone()[0]

        # Crear tabla de backup
        cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM facturas")

        conn.commit()

        # Verificar backup
        cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
        backup_count = cursor.fetchone()[0]

        print(f"✅ Backup creado: {backup_table}")
        print(f"   Registros originales: {count}")
        print(f"   Registros en backup: {backup_count}")

        conn.close()
        return backup_table

    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        conn.close()
        return None


def migrar_datos():
    """Migrar la tabla al schema correcto"""
    print("\n" + "=" * 80)
    print("2. MIGRANDO DATOS AL NUEVO SCHEMA")
    print("=" * 80)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Verificar cuántos registros hay
        cursor.execute("SELECT COUNT(*) FROM facturas")
        count_original = cursor.fetchone()[0]
        print(f"\nRegistros en tabla original: {count_original}")

        # Crear tabla nueva con schema correcto
        print("\nCreando tabla con schema correcto...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas_new (
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
                valor_transado REAL DEFAULT 0,
                cantidad_transada REAL DEFAULT 0,
                descripcion_nota_aplicada TEXT,
                estado TEXT DEFAULT 'VALIDA',
                tiene_nota_credito INTEGER DEFAULT 0,
                es_valida INTEGER DEFAULT 1,
                razon_invalidez TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_proceso DATE NOT NULL,
                UNIQUE(numero_factura, codigo_producto, fecha_proceso)
            )
        ''')

        print("✅ Tabla nueva creada con schema correcto")
        print("   - Constraint: UNIQUE(numero_factura, codigo_producto, fecha_proceso)")
        print("   - Columnas: valor_transado, cantidad_transada, descripcion_nota_aplicada")

        # Migrar datos (mapear columnas antiguas a nuevas)
        print("\nMigrando datos...")
        cursor.execute('''
            INSERT INTO facturas_new (
                numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                codigo_producto, nombre_producto, tipo_inventario,
                valor_total, cantidad,
                valor_transado, cantidad_transada,
                descripcion_nota_aplicada,
                estado, tiene_nota_credito,
                fecha_registro, fecha_proceso
            )
            SELECT
                numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                codigo_producto, nombre_producto, tipo_inventario,
                valor_total, cantidad,
                COALESCE(valor_nota_aplicada, 0) as valor_transado,
                COALESCE(cantidad_nota_aplicada, 0) as cantidad_transada,
                CASE
                    WHEN tiene_nota_credito = 1 THEN 'Nota aplicada'
                    ELSE NULL
                END as descripcion_nota_aplicada,
                COALESCE(estado, 'VALIDA') as estado,
                COALESCE(tiene_nota_credito, 0) as tiene_nota_credito,
                COALESCE(fecha_registro, CURRENT_TIMESTAMP) as fecha_registro,
                COALESCE(fecha_proceso, fecha_factura) as fecha_proceso
            FROM facturas
        ''')

        migrados = cursor.rowcount
        print(f"✅ Registros migrados: {migrados}")

        # Verificar datos migrados
        cursor.execute("SELECT COUNT(*) FROM facturas_new")
        count_new = cursor.fetchone()[0]

        if count_new == count_original:
            print(f"✅ Verificación exitosa: {count_new} registros en tabla nueva")
        else:
            print(f"⚠️  ADVERTENCIA: {count_original} registros originales, {count_new} migrados")

        # Eliminar tabla antigua y renombrar
        print("\nReemplazando tabla antigua...")
        cursor.execute("DROP TABLE facturas")
        cursor.execute("ALTER TABLE facturas_new RENAME TO facturas")

        # Crear índices
        print("\nCreando índices...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_numero ON facturas(numero_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_cliente ON facturas(nit_cliente)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha ON facturas(fecha_factura)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_fecha_proceso ON facturas(fecha_proceso)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_estado ON facturas(estado)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facturas_nota_aplicada ON facturas(tiene_nota_credito)')

        print("✅ Índices creados")

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error en migración: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False


def verificar_migracion():
    """Verificar que la migración fue exitosa"""
    print("\n" + "=" * 80)
    print("3. VERIFICANDO MIGRACIÓN")
    print("=" * 80)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Verificar schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='facturas'")
    schema = cursor.fetchone()[0]

    print("\nSchema de la tabla migrada:")
    print("-" * 80)
    print(schema)
    print("-" * 80)

    # Verificar constraint
    if "UNIQUE(numero_factura, codigo_producto, fecha_proceso)" in schema:
        print("\n✅ Constraint correcto: UNIQUE(numero_factura, codigo_producto, fecha_proceso)")
    else:
        print("\n❌ Constraint incorrecto")

    # Verificar columnas
    cursor.execute("PRAGMA table_info(facturas)")
    columnas = cursor.fetchall()

    print("\nColumnas de la tabla:")
    columnas_necesarias = ['valor_transado', 'cantidad_transada', 'descripcion_nota_aplicada', 'fecha_proceso']
    columnas_encontradas = [col[1] for col in columnas]

    for col_necesaria in columnas_necesarias:
        if col_necesaria in columnas_encontradas:
            print(f"  ✅ {col_necesaria}")
        else:
            print(f"  ❌ {col_necesaria} - NO ENCONTRADA")

    # Estadísticas
    cursor.execute('''
        SELECT
            COUNT(DISTINCT numero_factura) as num_facturas_unicas,
            COUNT(*) as total_lineas,
            CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT numero_factura) as promedio_lineas
        FROM facturas
    ''')

    stats = cursor.fetchone()

    print("\n" + "=" * 80)
    print("ESTADÍSTICAS POST-MIGRACIÓN")
    print("=" * 80)
    print(f"Facturas únicas: {stats[0]:,}")
    print(f"Total de líneas: {stats[1]:,}")
    print(f"Promedio de líneas por factura: {stats[2]:.2f}")

    # Verificar si hay facturas con múltiples líneas
    cursor.execute('''
        SELECT COUNT(*)
        FROM (
            SELECT numero_factura, fecha_proceso
            FROM facturas
            GROUP BY numero_factura, fecha_proceso
            HAVING COUNT(*) > 1
        )
    ''')

    facturas_multiples = cursor.fetchone()[0]

    if facturas_multiples > 0:
        print(f"\n✅ Se encontraron {facturas_multiples} facturas con múltiples líneas")
    else:
        print(f"\n⚠️  No se encontraron facturas con múltiples líneas (esperado si solo hay datos antiguos agrupados)")

    conn.close()


def main(auto_confirm=False):
    """Ejecutar migración completa"""
    print("\n" + "=" * 80)
    print("MIGRACIÓN: CORREGIR SCHEMA DE TABLA FACTURAS")
    print("=" * 80)
    print(f"\nBase de datos: {DB_PATH}")
    print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not DB_PATH.exists():
        print(f"\n❌ La base de datos no existe: {DB_PATH}")
        return 1

    # Verificar schema actual
    schema_actual = verificar_schema_actual()
    if not schema_actual:
        print("❌ No se pudo verificar el schema actual")
        return 1

    print("\nSchema actual:")
    print("-" * 80)
    print(schema_actual)
    print("-" * 80)

    # Verificar si ya tiene el schema correcto
    if "UNIQUE(numero_factura, codigo_producto, fecha_proceso)" in schema_actual:
        print("\n✅ La tabla YA tiene el schema correcto")
        print("   No es necesario migrar")
        return 0

    # Confirmar migración
    print("\n⚠️  ADVERTENCIA: Esta migración modificará la estructura de la tabla 'facturas'")
    print("   Se creará un backup automático antes de proceder")

    if not auto_confirm:
        print("\n¿Desea continuar? (s/n): ", end="")
        respuesta = input().strip().lower()
        if respuesta != 's':
            print("\n❌ Migración cancelada por el usuario")
            return 1
    else:
        print("\n✅ Modo automático: Procediendo con la migración...")

    # Crear backup
    backup_table = crear_backup()
    if not backup_table:
        print("\n❌ No se pudo crear el backup. Migración cancelada.")
        return 1

    # Ejecutar migración
    if not migrar_datos():
        print("\n❌ Migración fallida")
        print(f"   Los datos originales están en la tabla: {backup_table}")
        return 1

    # Verificar migración
    verificar_migracion()

    print("\n" + "=" * 80)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    print(f"\n🔧 La tabla 'facturas' ahora soporta líneas individuales")
    print(f"📦 Backup disponible en: {backup_table}")
    print(f"\n⚠️  IMPORTANTE: A partir de ahora, cuando proceses facturas,")
    print(f"   cada línea se guardará como un registro individual en la BD")

    return 0


if __name__ == "__main__":
    # Permitir modo automático con argumento --yes
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    exit(main(auto_confirm=auto_confirm))
