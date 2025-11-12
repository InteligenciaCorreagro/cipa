#!/usr/bin/env python3
"""
Script para probar validación de notas
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.business_rules import BusinessRulesValidator

# Ejemplos de notas del usuario
notas_test = [
    {
        "f_prefijo": "NCE",
        "f_nrodocto": 8262,
        "f_tipo_inv": "INV143005 ",
        "f_desc_tipo_inv": "MASCOTAS-PRODUCTO TERMINADO",
        "f_desc_item": "CIPACAN CROQUETAS POLLO 800GR",
        "f_valor_subtotal_local": -3242.0000,
        "f_cant_base": -1.0000,
        "f_fecha": "2025-11-10T00:00:00",
        "f_cliente_desp": "800098870",
        "f_cliente_fact_razon_soc": "VENTAS DEL TOLIMA S.A.S."
    },
    {
        "f_prefijo": "NPA",
        "f_nrodocto": 2,
        "f_tipo_inv": "INV143001 ",
        "f_desc_tipo_inv": "AVICULTURA-PRODUCTO TERMINADO",
        "f_desc_item": "SUELTAS PDO X 1 KG",
        "f_valor_subtotal_local": -3705.0000,
        "f_cant_base": -2.0000,
        "f_fecha": "2025-11-10T00:00:00",
        "f_cliente_desp": "900203566",
        "f_cliente_fact_razon_soc": "ABASTECEMOS DE OCCIDENTE SOCIEDAD POR ACCIONES SIMPLIFICADA"
    },
    {
        "f_prefijo": "NPA",
        "f_nrodocto": 2,
        "f_tipo_inv": "INV143002 ",
        "f_desc_tipo_inv": "ENGORDE-PRODUCTO TERMINADO",
        "f_desc_item": "POLLOS CAMPO PDO X 1 KILO",
        "f_valor_subtotal_local": -1649.0000,
        "f_cant_base": -1.0000,
        "f_fecha": "2025-11-10T00:00:00",
        "f_cliente_desp": "900203566",
        "f_cliente_fact_razon_soc": "ABASTECEMOS DE OCCIDENTE SOCIEDAD POR ACCIONES SIMPLIFICADA"
    },
    {
        "f_prefijo": "NPA",
        "f_nrodocto": 2,
        "f_tipo_inv": "INV143009 ",
        "f_desc_tipo_inv": "OTRAS ESPECIES-PRODUCTO TERMINADO",
        "f_desc_item": "CONEJOS PDO X 1 KILO",
        "f_valor_subtotal_local": -2270.0000,
        "f_cant_base": -1.0000,
        "f_fecha": "2025-11-10T00:00:00",
        "f_cliente_desp": "900203566",
        "f_cliente_fact_razon_soc": "ABASTECEMOS DE OCCIDENTE SOCIEDAD POR ACCIONES SIMPLIFICADA"
    }
]

print("=" * 80)
print("PRUEBA DE VALIDACIÓN DE NOTAS")
print("=" * 80)

validator = BusinessRulesValidator()

print(f"\nTipos de inventario excluidos: {len(validator.TIPOS_INVENTARIO_EXCLUIDOS)}")
print(f"Monto mínimo: ${validator.MONTO_MINIMO:,.2f}")

print("\n" + "=" * 80)
print("PROBANDO NOTAS INDIVIDUALES")
print("=" * 80)

for nota in notas_test:
    numero = f"{nota['f_prefijo']}{nota['f_nrodocto']}"
    tipo_inv_raw = nota.get('f_tipo_inv', '')
    tipo_inv_normalizado = validator._obtener_tipo_inventario_normalizado(nota)
    es_nc = validator.es_nota_credito(nota)
    es_permitido = validator.tipo_inventario_permitido(nota)

    print(f"\n📄 {numero}")
    print(f"   Producto: {nota.get('f_desc_item', '')[:50]}")
    print(f"   Valor: ${nota.get('f_valor_subtotal_local', 0):,.2f}")
    print(f"   Tipo inv raw: '{tipo_inv_raw}'")
    print(f"   Tipo inv normalizado: '{tipo_inv_normalizado}'")
    print(f"   Es nota crédito: {es_nc}")
    print(f"   Tipo permitido: {es_permitido}")
    print(f"   ¿Está en excluidos?: {tipo_inv_normalizado in validator.TIPOS_INVENTARIO_EXCLUIDOS}")

    if es_permitido:
        print("   ✅ DEBERÍA SER ACEPTADA")
    else:
        print("   ❌ SERÍA RECHAZADA")

print("\n" + "=" * 80)
print("FILTRADO COMPLETO")
print("=" * 80)

facturas_validas, notas_credito, facturas_rechazadas = validator.filtrar_facturas(notas_test)

print(f"\n📊 Resultados:")
print(f"   Facturas válidas: {len(facturas_validas)}")
print(f"   Notas crédito aceptadas: {len(notas_credito)}")
print(f"   Facturas/notas rechazadas: {len(facturas_rechazadas)}")

if notas_credito:
    print(f"\n✅ Notas crédito aceptadas:")
    for nota in notas_credito:
        numero = f"{nota['f_prefijo']}{nota['f_nrodocto']}"
        print(f"   - {numero}: {nota.get('f_desc_item', '')[:40]}")

if facturas_rechazadas:
    print(f"\n❌ Documentos rechazados:")
    for item in facturas_rechazadas:
        nota = item['factura']
        numero = f"{nota['f_prefijo']}{nota['f_nrodocto']}"
        print(f"   - {numero}: {item['razon_rechazo']}")

print("\n" + "=" * 80)
