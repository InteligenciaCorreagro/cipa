#!/usr/bin/env python3
"""
Script de prueba para verificar el registro de facturas válidas
"""
import sys
from pathlib import Path
from datetime import datetime

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core.notas_credito_manager import NotasCreditoManager

def test_registro_factura():
    """Probar el registro de una factura de ejemplo"""

    notas_manager = NotasCreditoManager('./data/notas_credito.db')

    # Factura de prueba (formato después de transformar)
    factura_prueba = {
        'Nro factura': 'FV00001234',
        'Fecha factura': '2025-11-10',
        'NIT Cliente': '900123456',
        'Razón social': 'Cliente de Prueba S.A.S',
        'Código producto': 'PROD001',
        'Nombre producto': 'Producto de Prueba',
        'Tipo inventario': '01',
        'Vr subtotal': 1000000.0,
        'Cantidad': 100.0,
        'Vr unitario': 10000.0
    }

    print("\n" + "="*60)
    print("PROBANDO REGISTRO DE FACTURA VÁLIDA")
    print("="*60)
    print(f"\nFactura de prueba:")
    for key, value in factura_prueba.items():
        print(f"  {key}: {value}")

    print(f"\n{'='*60}")
    print("Intentando registrar...")
    print("="*60)

    try:
        resultado = notas_manager.registrar_factura_valida(factura_prueba)

        if resultado:
            print("\n✅ Factura registrada exitosamente!")

            # Verificar en BD
            import sqlite3
            conn = sqlite3.connect('./data/notas_credito.db')
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM facturas WHERE numero_factura = ?", ('FV00001234',))
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"✅ Verificado en BD: {count} registro(s) encontrado(s)")

                cursor.execute("SELECT * FROM facturas WHERE numero_factura = ?", ('FV00001234',))
                row = cursor.fetchone()
                print(f"\nDatos en BD:")
                cursor.execute("PRAGMA table_info(facturas)")
                columns = [col[1] for col in cursor.fetchall()]
                for i, col in enumerate(columns):
                    if i < len(row):
                        print(f"  {col}: {row[i]}")
            else:
                print(f"❌ No se encontró en BD")

            conn.close()
        else:
            print("\n❌ Error: El método retornó False")

    except Exception as e:
        print(f"\n❌ Error durante el registro: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    import os
    os.chdir('/home/user/cipa')
    test_registro_factura()
