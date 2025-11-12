#!/usr/bin/env python3
"""
Script para probar conexión con la API de SIESA
"""
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.api_client import SiesaAPIClient

print("=" * 80)
print("TEST DE CONEXIÓN API SIESA")
print("=" * 80)

# Cargar credenciales
load_dotenv()

CONNI_KEY = os.getenv('CONNI_KEY')
CONNI_TOKEN = os.getenv('CONNI_TOKEN')

if not CONNI_KEY or not CONNI_TOKEN:
    print("\n❌ ERROR: Faltan credenciales en .env")
    print("   CONNI_KEY:", "✅ Configurado" if CONNI_KEY else "❌ Falta")
    print("   CONNI_TOKEN:", "✅ Configurado" if CONNI_TOKEN else "❌ Falta")
    sys.exit(1)

print("\n✅ Credenciales encontradas")
print(f"   CONNI_KEY: {CONNI_KEY[:10]}...")
print(f"   CONNI_TOKEN: {CONNI_TOKEN[:10]}...")

# Inicializar cliente
api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)

# Fechas de prueba
fechas_prueba = [
    ("Ayer", datetime.now() - timedelta(days=1)),
    ("Hace 3 días", datetime.now() - timedelta(days=3)),
    ("10 Nov 2024", datetime(2024, 11, 10)),
    ("11 Nov 2024", datetime(2024, 11, 11)),
]

print("\n" + "=" * 80)
print("PROBANDO DIFERENTES FECHAS")
print("=" * 80)

for nombre, fecha in fechas_prueba:
    fecha_str = fecha.strftime('%Y-%m-%d')
    print(f"\n📅 Probando: {nombre} ({fecha_str})")
    print("-" * 80)

    try:
        documentos = api_client.obtener_facturas(fecha)

        if documentos:
            print(f"   ✅ Éxito: {len(documentos)} documentos obtenidos")

            # Mostrar primer documento como ejemplo
            if len(documentos) > 0:
                doc = documentos[0]
                print(f"\n   Ejemplo de documento:")
                print(f"      Prefijo: {doc.get('f_prefijo', 'N/A')}")
                print(f"      Número: {doc.get('f_nrodocto', 'N/A')}")
                print(f"      Cliente: {doc.get('f_cliente_fact_razon_soc', 'N/A')[:40]}")
                print(f"      Producto: {doc.get('f_desc_item', 'N/A')[:40]}")
                print(f"      Valor: ${doc.get('f_valor_subtotal_local', 0):,.2f}")
                print(f"      Tipo Inv: {doc.get('f_tipo_inv', 'N/A')}")
        else:
            print(f"   ⚠️  No hay documentos para esta fecha")

    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print("\n" + "=" * 80)
print("TEST COMPLETADO")
print("=" * 80)
print("\n💡 Si ves errores 400 Bad Request:")
print("   - Verifica que las fechas sean válidas (no futuras)")
print("   - Verifica que las credenciales sean correctas")
print("   - Verifica que la API tenga datos para esas fechas")
print("\n💡 Si todas las pruebas fallan:")
print("   - Verifica las credenciales CONNI_KEY y CONNI_TOKEN")
print("   - Contacta al equipo de SIESA para verificar acceso")
