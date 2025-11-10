#!/usr/bin/env python3
"""
Script para verificar notas en la base de datos y sus tipos de inventario
"""
import sqlite3
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.business_rules import BusinessRulesValidator

def main():
    db_path = backend_path / 'data' / 'notas_credito.db'

    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Obtener tipos excluidos
    validator = BusinessRulesValidator()
    tipos_excluidos = validator.TIPOS_INVENTARIO_EXCLUIDOS

    print("="*80)
    print("VERIFICACIÓN DE NOTAS EN LA BASE DE DATOS")
    print("="*80)
    print(f"\nTipos de inventario excluidos: {len(tipos_excluidos)}")
    print(f"{', '.join(sorted(tipos_excluidos))}\n")

    # Contar total de notas
    cursor.execute("SELECT COUNT(*) FROM notas_credito")
    total_notas = cursor.fetchone()[0]
    print(f"Total notas en BD: {total_notas}")

    # Ver distribución por tipo de inventario
    cursor.execute("""
        SELECT tipo_inventario, COUNT(*), SUM(valor_total), estado
        FROM notas_credito
        GROUP BY tipo_inventario, estado
        ORDER BY COUNT(*) DESC
    """)

    print("\n" + "="*80)
    print("DISTRIBUCIÓN DE NOTAS POR TIPO DE INVENTARIO")
    print("="*80)

    tipos_con_problemas = []
    for row in cursor.fetchall():
        tipo_inv, count, valor_total, estado = row
        tipo_normalizado = str(tipo_inv).strip().upper() if tipo_inv else 'NULL'
        es_excluido = tipo_normalizado in tipos_excluidos

        marca = "❌ EXCLUIDO" if es_excluido else "✅"
        print(f"{marca} {tipo_normalizado:20} | Cantidad: {count:4} | Valor: ${valor_total:,.2f} | Estado: {estado}")

        if es_excluido:
            tipos_con_problemas.append((tipo_normalizado, count, valor_total))

    # Mostrar resumen de notas a eliminar
    if tipos_con_problemas:
        print("\n" + "="*80)
        print("⚠️  NOTAS CON TIPOS EXCLUIDOS QUE DEBEN SER ELIMINADAS")
        print("="*80)
        total_eliminar = sum(count for _, count, _ in tipos_con_problemas)
        valor_total_eliminar = sum(valor for _, _, valor in tipos_con_problemas)

        print(f"\nTotal a eliminar: {total_eliminar} notas | Valor: ${valor_total_eliminar:,.2f}\n")

        for tipo, count, valor in tipos_con_problemas:
            print(f"  - {tipo:20} | {count:4} notas | ${valor:,.2f}")
    else:
        print("\n" + "="*80)
        print("✅ NO HAY NOTAS CON TIPOS EXCLUIDOS EN LA BASE DE DATOS")
        print("="*80)

    # Verificar notas con tipo NULL o vacío
    cursor.execute("""
        SELECT COUNT(*), SUM(valor_total)
        FROM notas_credito
        WHERE tipo_inventario IS NULL OR tipo_inventario = ''
    """)
    count_null, valor_null = cursor.fetchone()

    if count_null > 0:
        print(f"\n⚠️  Hay {count_null} notas con tipo de inventario NULL/vacío | Valor: ${valor_null:,.2f}")

        # Mostrar algunas de estas notas
        cursor.execute("""
            SELECT numero_nota, nombre_producto, valor_total, estado
            FROM notas_credito
            WHERE tipo_inventario IS NULL OR tipo_inventario = ''
            LIMIT 10
        """)

        print("\nPrimeras 10 notas sin tipo:")
        for nota in cursor.fetchall():
            numero, nombre, valor, estado = nota
            print(f"  - {numero:15} | {nombre[:50]:50} | ${valor:10,.2f} | {estado}")

    conn.close()
    return 0

if __name__ == '__main__':
    exit(main())
