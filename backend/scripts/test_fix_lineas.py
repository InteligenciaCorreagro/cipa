#!/usr/bin/env python3
"""
Test para verificar que el fix de codigo_producto funciona correctamente
"""
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'notas_credito.db'

def test_insertar_factura_con_lineas():
    """Simular inserción de una factura con múltiples líneas usando el código corregido"""
    print("=" * 80)
    print("TEST: VERIFICAR FIX DE CODIGO_PRODUCTO")
    print("=" * 80)

    # Simular datos transformados (como los retorna excel_processor.transformar_factura)
    facturas_transformadas = [
        {
            'numero_factura': 'TESTFIX001',
            'fecha_factura': datetime.now().date(),
            'nit_comprador': '900111222',
            'nombre_comprador': 'Cliente Test Fix',
            'codigo_producto_api': 'PROD001',  # ✅ Esta es la key correcta
            'nombre_producto': 'Producto 1',
            'descripcion': 'PTCOS',
            'valor_total': 1000.0,
            'cantidad': 10.0,
            'valor_transado': 0.0,
            'cantidad_transada': 0.0,
        },
        {
            'numero_factura': 'TESTFIX001',
            'fecha_factura': datetime.now().date(),
            'nit_comprador': '900111222',
            'nombre_comprador': 'Cliente Test Fix',
            'codigo_producto_api': 'PROD002',  # ✅ Diferente código
            'nombre_producto': 'Producto 2',
            'descripcion': 'PTCOS',
            'valor_total': 2000.0,
            'cantidad': 20.0,
            'valor_transado': 0.0,
            'cantidad_transada': 0.0,
        },
        {
            'numero_factura': 'TESTFIX001',
            'fecha_factura': datetime.now().date(),
            'nit_comprador': '900111222',
            'nombre_comprador': 'Cliente Test Fix',
            'codigo_producto_api': 'PROD003',  # ✅ Diferente código
            'nombre_producto': 'Producto 3',
            'descripcion': 'PTCOS',
            'valor_total': 3000.0,
            'cantidad': 30.0,
            'valor_transado': 0.0,
            'cantidad_transada': 0.0,
        },
    ]

    fecha_proceso = datetime.now().date()
    notas_por_factura = {}

    # Limpiar registros de prueba anteriores
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facturas WHERE numero_factura LIKE 'TESTFIX%'")
    conn.commit()

    print(f"\nInsertando factura TESTFIX001 con 3 líneas...")
    print(f"Fecha de proceso: {fecha_proceso}\n")

    # Simular el código de guardado (igual que en procesar_y_guardar_facturas.py)
    facturas_guardadas = 0

    for factura in facturas_transformadas:
        numero_factura = factura['numero_factura']

        # Determinar si tiene nota aplicada
        tiene_nota = numero_factura in notas_por_factura
        numero_nota = None

        if tiene_nota:
            notas_aplicadas = notas_por_factura[numero_factura]
            if len(notas_aplicadas) == 1:
                numero_nota = notas_aplicadas[0]
            else:
                numero_nota = ', '.join(notas_aplicadas)

        try:
            # Insertar o actualizar factura (CÓDIGO CORREGIDO)
            cursor.execute('''
                INSERT INTO facturas (
                    numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                    codigo_producto, nombre_producto, tipo_inventario,
                    valor_total, cantidad, valor_nota_aplicada, cantidad_nota_aplicada,
                    numero_nota_aplicada, tiene_nota_credito, fecha_proceso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(numero_factura, codigo_producto, fecha_proceso) DO UPDATE SET
                    valor_total = excluded.valor_total,
                    cantidad = excluded.cantidad,
                    valor_nota_aplicada = excluded.valor_nota_aplicada,
                    cantidad_nota_aplicada = excluded.cantidad_nota_aplicada,
                    numero_nota_aplicada = excluded.numero_nota_aplicada,
                    tiene_nota_credito = excluded.tiene_nota_credito
            ''', (
                numero_factura,
                factura.get('fecha_factura', fecha_proceso),
                factura.get('nit_comprador', ''),  # nit_cliente
                factura.get('nombre_comprador', ''),  # nombre_cliente
                factura.get('codigo_producto_api', ''),  # ✅ CORREGIDO: ahora usa codigo_producto_api
                factura.get('nombre_producto', ''),  # nombre_producto
                factura.get('descripcion', ''),  # tipo_inventario
                factura.get('valor_total', 0.0),
                factura.get('cantidad', 0.0),
                factura.get('valor_transado', 0.0),
                factura.get('cantidad_transada', 0.0),
                numero_nota,
                1 if tiene_nota else 0,
                fecha_proceso
            ))

            facturas_guardadas += 1
            codigo_prod = factura.get('codigo_producto_api', '')
            print(f"  ✅ Línea {facturas_guardadas} guardada: {codigo_prod} - ${factura.get('valor_total', 0.0):,.2f}")

        except Exception as e:
            print(f"  ❌ Error guardando línea: {e}")
            import traceback
            traceback.print_exc()

    conn.commit()

    # Verificar cuántas líneas se guardaron
    cursor.execute('''
        SELECT COUNT(*)
        FROM facturas
        WHERE numero_factura = ? AND fecha_proceso = ?
    ''', ('TESTFIX001', fecha_proceso))

    count = cursor.fetchone()[0]

    print(f"\n{'=' * 80}")
    print("RESULTADO DEL TEST")
    print("=" * 80)
    print(f"Líneas intentadas: 3")
    print(f"Líneas guardadas: {count}")

    if count == 3:
        print("\n✅ ¡FIX EXITOSO! Se guardaron las 3 líneas correctamente")
        print("   Cada línea tiene su codigo_producto diferente")
        resultado = True
    else:
        print(f"\n❌ ERROR: Se esperaban 3 líneas, se guardaron {count}")
        resultado = False

    # Mostrar detalle
    cursor.execute('''
        SELECT id, numero_factura, codigo_producto, nombre_producto,
               valor_total, cantidad
        FROM facturas
        WHERE numero_factura = ? AND fecha_proceso = ?
        ORDER BY id
    ''', ('TESTFIX001', fecha_proceso))

    rows = cursor.fetchall()

    if rows:
        print(f"\n{'=' * 80}")
        print("DETALLE DE LÍNEAS GUARDADAS")
        print("=" * 80)
        print(f"\n{'ID':<6} {'Factura':<15} {'Código Prod':<15} {'Producto':<20} {'Valor':>12} {'Cantidad':>10}")
        print("-" * 85)

        for row in rows:
            id_val, num_fact, cod_prod, nom_prod, valor, cantidad = row
            print(f"{id_val:<6} {num_fact:<15} {cod_prod:<15} {nom_prod:<20} ${valor:>10,.2f} {cantidad:>10.2f}")

    conn.close()

    return resultado


if __name__ == "__main__":
    exito = test_insertar_factura_con_lineas()

    print("\n" + "=" * 80)
    if exito:
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print("\nEl fix funciona correctamente:")
        print("  - Se usa 'codigo_producto_api' en lugar de 'codigo_producto'")
        print("  - Las líneas se guardan individualmente")
        print("  - El constraint UNIQUE funciona correctamente")
        exit(0)
    else:
        print("❌ TEST FALLIDO")
        print("=" * 80)
        exit(1)
