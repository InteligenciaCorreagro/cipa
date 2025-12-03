#!/usr/bin/env python3
"""
Script para ver ejemplos de facturas en la BD y entender el problema
"""
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'notas_credito.db'

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("=" * 80)
print("ANÁLISIS DE DATOS ACTUALES EN LA BD")
print("=" * 80)

# Ver una muestra de facturas
cursor.execute('''
    SELECT numero_factura, codigo_producto, nombre_producto,
           valor_total, cantidad, fecha_proceso
    FROM facturas
    WHERE numero_factura NOT LIKE 'TEST%'
    LIMIT 20
''')

print("\nMuestra de 20 registros:")
print(f"{'Factura':<15} {'Código Prod':<20} {'Producto':<30} {'Valor':>12} {'Cant':>8} {'Fecha':<12}")
print("-" * 120)

for row in cursor.fetchall():
    num_fact, cod_prod, nom_prod, valor, cant, fecha = row
    print(f"{num_fact:<15} {cod_prod:<20} {nom_prod[:30]:<30} ${valor:>10,.2f} {cant:>8.2f} {fecha:<12}")

print("\n" + "=" * 80)
print("CONCLUSIÓN")
print("=" * 80)
print("Si cada registro tiene un código_producto diferente, entonces SÍ se están")
print("guardando líneas individuales. El promedio de 1.0 sugiere que:")
print("  1. Las facturas históricas solo tienen 1 producto cada una, O")
print("  2. Los datos fueron procesados con un código que agrupaba")

conn.close()
