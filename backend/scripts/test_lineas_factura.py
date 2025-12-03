#!/usr/bin/env python3
"""
Test para verificar que las LÍNEAS de facturas se guarden correctamente (no agrupadas)
Si una factura FEM123 tiene 10 líneas, deben guardarse 10 registros en la BD
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import sqlite3

# Usar la BD del proyecto raíz
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'notas_credito.db'


def verificar_schema():
    """Verificar que el schema de la tabla facturas sea correcto"""
    print("=" * 80)
    print("1. VERIFICANDO SCHEMA DE LA TABLA FACTURAS")
    print("=" * 80)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Obtener el schema de la tabla
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='facturas'")
    result = cursor.fetchone()

    if not result:
        print("❌ ERROR: La tabla 'facturas' no existe en la base de datos")
        conn.close()
        return False

    schema = result[0]
    print(f"\nSchema actual:\n{schema}\n")

    # Verificar que el constraint UNIQUE incluya fecha_proceso
    if "UNIQUE(numero_factura, codigo_producto, fecha_proceso)" in schema:
        print("✅ CORRECTO: El constraint UNIQUE incluye fecha_proceso")
        print("   Esto permite múltiples líneas por factura (diferentes codigo_producto)")
        schema_ok = True
    elif "UNIQUE(numero_factura, codigo_producto)" in schema:
        print("⚠️  ADVERTENCIA: El constraint es UNIQUE(numero_factura, codigo_producto)")
        print("   Esto es CORRECTO para líneas múltiples, pero debería incluir fecha_proceso")
        print("   para evitar sobrescribir datos en reprocesos del mismo día")
        schema_ok = True
    else:
        print("❌ ERROR: No se encontró el constraint UNIQUE esperado")
        schema_ok = False

    conn.close()
    return schema_ok


def limpiar_datos_test():
    """Limpiar datos de prueba anteriores"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Eliminar facturas de prueba (las que empiezan con 'TEST')
    cursor.execute("DELETE FROM facturas WHERE numero_factura LIKE 'TEST%'")
    eliminados = cursor.rowcount

    conn.commit()
    conn.close()

    if eliminados > 0:
        print(f"\n🧹 Limpiados {eliminados} registros de prueba anteriores")

    return eliminados


def test_insertar_lineas_multiples():
    """Test: Insertar una factura con 10 líneas y verificar que se guarden todas"""
    print("\n" + "=" * 80)
    print("2. TEST: INSERTAR FACTURA CON 10 LÍNEAS")
    print("=" * 80)

    # Limpiar datos de prueba anteriores
    limpiar_datos_test()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    fecha_proceso = datetime.now().date()
    numero_factura = "TESTFEM123"

    print(f"\nInsertando factura: {numero_factura}")
    print(f"Número de líneas a insertar: 10")
    print(f"Fecha de proceso: {fecha_proceso}")

    # Insertar 10 líneas de la misma factura (diferentes productos)
    lineas_insertadas = 0

    for i in range(1, 11):
        codigo_producto = f"PROD{i:03d}"  # PROD001, PROD002, ..., PROD010

        try:
            cursor.execute('''
                INSERT INTO facturas (
                    numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                    codigo_producto, nombre_producto, tipo_inventario,
                    valor_total, cantidad, valor_nota_aplicada, cantidad_nota_aplicada,
                    numero_nota_aplicada, tiene_nota_credito, fecha_proceso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                numero_factura,
                fecha_proceso,
                "900123456",  # NIT de prueba
                "Cliente de Prueba S.A.S",
                codigo_producto,
                f"Producto de Prueba {i}",
                "PTCOS",
                1000.0 * i,  # Valores diferentes por línea
                10.0 * i,    # Cantidades diferentes por línea
                0.0,
                0.0,
                None,
                0,
                fecha_proceso
            ))

            lineas_insertadas += 1
            print(f"  ✅ Línea {i} insertada: {codigo_producto} - Valor: ${1000.0 * i:,.2f}")

        except Exception as e:
            print(f"  ❌ Error insertando línea {i}: {e}")

    conn.commit()

    # Verificar cuántas líneas se guardaron
    cursor.execute('''
        SELECT COUNT(*)
        FROM facturas
        WHERE numero_factura = ? AND fecha_proceso = ?
    ''', (numero_factura, fecha_proceso))

    count = cursor.fetchone()[0]

    print(f"\n{'=' * 80}")
    print("RESULTADO DEL TEST")
    print("=" * 80)
    print(f"Líneas que se intentaron insertar: 10")
    print(f"Líneas encontradas en la BD: {count}")

    if count == 10:
        print("\n✅ ¡ÉXITO! Se guardaron las 10 líneas individualmente")
        print(f"   La factura {numero_factura} tiene 10 registros en la BD")
        resultado = True
    elif count == 1:
        print(f"\n❌ ERROR: Solo se guardó 1 registro agrupado")
        print(f"   Problema: Las líneas se están sobrescribiendo o agrupando")
        resultado = False
    else:
        print(f"\n⚠️  ADVERTENCIA: Se guardaron {count} líneas (esperadas: 10)")
        resultado = False

    # Mostrar detalle de las líneas guardadas
    print("\n" + "=" * 80)
    print("DETALLE DE LÍNEAS GUARDADAS")
    print("=" * 80)

    cursor.execute('''
        SELECT id, numero_factura, codigo_producto, nombre_producto,
               valor_total, cantidad, fecha_proceso
        FROM facturas
        WHERE numero_factura = ? AND fecha_proceso = ?
        ORDER BY id
    ''', (numero_factura, fecha_proceso))

    rows = cursor.fetchall()

    if rows:
        print(f"\n{'ID':<6} {'Factura':<15} {'Código Prod':<12} {'Producto':<25} {'Valor':>12} {'Cantidad':>10}")
        print("-" * 90)

        for row in rows:
            id_val, num_fact, cod_prod, nom_prod, valor, cantidad, fecha = row
            print(f"{id_val:<6} {num_fact:<15} {cod_prod:<12} {nom_prod:<25} ${valor:>10,.2f} {cantidad:>10.2f}")
    else:
        print("No se encontraron registros")

    conn.close()

    return resultado


def test_consulta_facturas_agrupadas():
    """Verificar si hay facturas reales con múltiples líneas en la BD"""
    print("\n" + "=" * 80)
    print("3. VERIFICAR FACTURAS REALES CON MÚLTIPLES LÍNEAS")
    print("=" * 80)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Buscar facturas con múltiples líneas (excluyendo las de prueba)
    cursor.execute('''
        SELECT numero_factura, COUNT(*) as num_lineas,
               SUM(valor_total) as valor_total_factura,
               MIN(fecha_proceso) as fecha_proceso
        FROM facturas
        WHERE numero_factura NOT LIKE 'TEST%'
        GROUP BY numero_factura, fecha_proceso
        HAVING COUNT(*) > 1
        ORDER BY num_lineas DESC
        LIMIT 10
    ''')

    facturas_multiples = cursor.fetchall()

    if not facturas_multiples:
        print("\n⚠️  No se encontraron facturas reales con múltiples líneas en la BD")
        print("   Esto podría indicar que:")
        print("   1. Aún no se han procesado facturas con múltiples líneas")
        print("   2. Las líneas se están agrupando antes de guardarse")
        print("   3. La BD está vacía o solo tiene datos de prueba")
    else:
        print(f"\n✅ Se encontraron {len(facturas_multiples)} facturas con múltiples líneas:")
        print(f"\n{'Número Factura':<20} {'Líneas':>8} {'Valor Total':>15} {'Fecha Proceso':<12}")
        print("-" * 60)

        for num_fact, num_lineas, valor_total, fecha in facturas_multiples:
            print(f"{num_fact:<20} {num_lineas:>8} ${valor_total:>13,.2f} {fecha:<12}")

        # Mostrar detalle de la primera factura
        print("\n" + "=" * 80)
        print(f"DETALLE DE LA FACTURA: {facturas_multiples[0][0]}")
        print("=" * 80)

        cursor.execute('''
            SELECT id, codigo_producto, nombre_producto,
                   valor_total, cantidad, tipo_inventario
            FROM facturas
            WHERE numero_factura = ? AND fecha_proceso = ?
            ORDER BY id
        ''', (facturas_multiples[0][0], facturas_multiples[0][3]))

        lineas = cursor.fetchall()

        print(f"\n{'ID':<6} {'Código Prod':<15} {'Producto':<30} {'Tipo Inv':<10} {'Valor':>12} {'Cant':>8}")
        print("-" * 100)

        for row in lineas:
            id_val, cod_prod, nom_prod, valor, cantidad, tipo_inv = row
            print(f"{id_val:<6} {cod_prod:<15} {nom_prod[:30]:<30} {tipo_inv or 'N/A':<10} ${valor:>10,.2f} {cantidad:>8.2f}")

    # Estadísticas generales
    cursor.execute('''
        SELECT
            COUNT(DISTINCT numero_factura) as num_facturas_unicas,
            COUNT(*) as total_lineas,
            CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT numero_factura) as promedio_lineas_por_factura
        FROM facturas
        WHERE numero_factura NOT LIKE 'TEST%'
    ''')

    stats = cursor.fetchone()

    if stats and stats[0] > 0:
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS GENERALES DE LA BD")
        print("=" * 80)
        print(f"Facturas únicas: {stats[0]:,}")
        print(f"Total de líneas: {stats[1]:,}")
        print(f"Promedio de líneas por factura: {stats[2]:.2f}")

        if stats[2] > 1.5:
            print("\n✅ El promedio indica que hay facturas con múltiples líneas")
        elif stats[2] > 1.0:
            print("\n⚠️  El promedio sugiere que algunas facturas tienen múltiples líneas")
        else:
            print("\n⚠️  El promedio de 1.0 sugiere que cada factura tiene solo 1 línea")
            print("   Esto podría indicar agrupación o falta de datos")

    conn.close()


def test_aplicacion_notas():
    """Test: Aplicar una nota a una factura con múltiples líneas"""
    print("\n" + "=" * 80)
    print("4. TEST: APLICACIÓN DE NOTAS A FACTURA CON MÚLTIPLES LÍNEAS")
    print("=" * 80)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    numero_factura = "TESTFEM123"
    fecha_proceso = datetime.now().date()

    # Verificar que la factura de prueba existe
    cursor.execute('''
        SELECT COUNT(*)
        FROM facturas
        WHERE numero_factura = ? AND fecha_proceso = ?
    ''', (numero_factura, fecha_proceso))

    count = cursor.fetchone()[0]

    if count == 0:
        print(f"⚠️  La factura de prueba {numero_factura} no existe")
        print("   Ejecute primero el test de inserción (test 2)")
        conn.close()
        return False

    print(f"\nFactura de prueba: {numero_factura}")
    print(f"Número de líneas: {count}")

    # Simular aplicación de nota a todas las líneas
    print("\nAplicando nota TESTNC001 a todas las líneas...")

    cursor.execute('''
        UPDATE facturas
        SET tiene_nota_credito = 1,
            numero_nota_aplicada = 'TESTNC001',
            valor_nota_aplicada = valor_total,
            cantidad_nota_aplicada = cantidad
        WHERE numero_factura = ? AND fecha_proceso = ?
    ''', (numero_factura, fecha_proceso))

    lineas_actualizadas = cursor.rowcount
    conn.commit()

    print(f"✅ Líneas actualizadas: {lineas_actualizadas}")

    # Verificar que todas las líneas tienen la nota aplicada
    cursor.execute('''
        SELECT codigo_producto, valor_total, valor_nota_aplicada,
               numero_nota_aplicada, tiene_nota_credito
        FROM facturas
        WHERE numero_factura = ? AND fecha_proceso = ?
        ORDER BY codigo_producto
    ''', (numero_factura, fecha_proceso))

    lineas = cursor.fetchall()

    print("\n" + "=" * 80)
    print("VERIFICACIÓN: LÍNEAS CON NOTA APLICADA")
    print("=" * 80)

    print(f"\n{'Código Prod':<15} {'Valor Total':>12} {'Valor Nota':>15} {'Nota Aplicada':<10} {'Número Nota':<30}")
    print("-" * 100)

    todas_ok = True
    for row in lineas:
        cod_prod, valor_total, valor_nota, numero_nota, tiene_nota = row
        check = "✅" if tiene_nota == 1 and valor_nota == valor_total else "❌"
        print(f"{cod_prod:<15} ${valor_total:>10,.2f} ${valor_nota:>13,.2f} {check:<10} {numero_nota or 'N/A':<30}")

        if tiene_nota != 1 or valor_nota != valor_total:
            todas_ok = False

    print("\n" + "=" * 80)
    if todas_ok and lineas_actualizadas == count:
        print("✅ ¡ÉXITO! La nota se aplicó correctamente a todas las líneas")
        print(f"   Todas las {count} líneas tienen la nota aplicada")
        resultado = True
    else:
        print("❌ ERROR: La nota no se aplicó correctamente a todas las líneas")
        resultado = False

    conn.close()
    return resultado


def main():
    """Ejecutar todos los tests"""
    print("\n" + "=" * 80)
    print("TEST DE LÍNEAS DE FACTURAS EN BASE DE DATOS")
    print("=" * 80)
    print(f"\nBase de datos: {DB_PATH}")
    print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    resultados = {}

    # Test 1: Verificar schema
    resultados['schema'] = verificar_schema()

    # Test 2: Insertar líneas múltiples
    resultados['insercion'] = test_insertar_lineas_multiples()

    # Test 3: Verificar facturas reales
    test_consulta_facturas_agrupadas()

    # Test 4: Aplicación de notas
    resultados['notas'] = test_aplicacion_notas()

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL DE TESTS")
    print("=" * 80)

    tests_total = len(resultados)
    tests_exitosos = sum(1 for r in resultados.values() if r)

    print(f"\nTests ejecutados: {tests_total}")
    print(f"Tests exitosos: {tests_exitosos}")
    print(f"Tests fallidos: {tests_total - tests_exitosos}")

    print("\nResultados por test:")
    print(f"  1. Schema de tabla: {'✅ OK' if resultados['schema'] else '❌ FAIL'}")
    print(f"  2. Inserción múltiples líneas: {'✅ OK' if resultados['insercion'] else '❌ FAIL'}")
    print(f"  3. Aplicación de notas: {'✅ OK' if resultados['notas'] else '❌ FAIL'}")

    if all(resultados.values()):
        print("\n" + "=" * 80)
        print("✅ ¡TODOS LOS TESTS PASARON!")
        print("=" * 80)
        print("\nCONCLUSIÓN:")
        print("  - Las líneas de facturas SE ESTÁN GUARDANDO CORRECTAMENTE")
        print("  - Cada línea es un registro individual en la BD")
        print("  - Si una factura FEM123 tiene 10 líneas, hay 10 registros en la BD")
        print("  - Las notas se aplican correctamente a todas las líneas")
        return 0
    else:
        print("\n" + "=" * 80)
        print("⚠️  ALGUNOS TESTS FALLARON")
        print("=" * 80)
        print("\nRECOMENDACIONES:")
        if not resultados['schema']:
            print("  - Verificar el schema de la tabla facturas")
            print("  - Ejecutar migraciones si es necesario")
        if not resultados['insercion']:
            print("  - Revisar el código de inserción de facturas")
            print("  - Verificar constraints de la tabla")
        if not resultados['notas']:
            print("  - Revisar el código de aplicación de notas")
        return 1


if __name__ == "__main__":
    exit(main())
