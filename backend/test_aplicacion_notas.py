#!/usr/bin/env python3
"""
Test de Verificación de Aplicación de Notas de Crédito
======================================================

Este script verifica que la lógica de aplicación de notas de crédito
funcione correctamente según las reglas de negocio:

REGLAS DE APLICACIÓN:
1. Cantidad nota <= Cantidad factura
2. Valor nota <= Valor factura

Si AMBAS condiciones se cumplen → La nota SE APLICA
Si ALGUNA condición falla → La nota NO SE APLICA
"""

import sys
import os
from datetime import datetime

# Agregar el directorio core al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from notas_credito_manager import NotasCreditoManager


class TestAplicacionNotas:
    """Clase para probar la aplicación de notas de crédito"""

    def __init__(self):
        # Usar base de datos temporal para pruebas
        self.db_path = '/tmp/test_notas.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.manager = NotasCreditoManager(db_path=self.db_path)
        self.casos_prueba = []
        self.resultados = []

    def crear_nota(self, numero_nota, nit_cliente, codigo_producto, cantidad, valor):
        """Crea una nota de crédito de prueba"""
        return {
            'id': len(self.casos_prueba) + 1,
            'numero_nota': numero_nota,
            'nit_cliente': nit_cliente,
            'codigo_producto': codigo_producto,
            'cantidad_pendiente': cantidad,
            'saldo_pendiente': valor,
            'nombre_cliente': 'Cliente Test',
            'nombre_producto': 'Producto Test',
            'estado': 'PENDIENTE'
        }

    def crear_factura(self, numero_factura, nit_cliente, codigo_producto, cantidad, valor):
        """Crea una factura de prueba"""
        return {
            'numero_factura': numero_factura,
            'nit_comprador': nit_cliente,
            'codigo_producto_api': codigo_producto,
            'cantidad': cantidad,
            'cantidad_original': cantidad,
            'valor_total': valor,
            'fecha_factura': datetime.now().date(),
            'nombre_comprador': 'Cliente Test',
            'nombre_producto': 'Producto Test'
        }

    def ejecutar_caso(self, nombre, nota, factura, debe_aplicarse, razon):
        """
        Ejecuta un caso de prueba

        Args:
            nombre: Nombre descriptivo del caso
            nota: Diccionario con datos de la nota
            factura: Diccionario con datos de la factura
            debe_aplicarse: True si se espera que la nota se aplique
            razon: Explicación de por qué se aplica o no
        """
        print(f"\n{'='*80}")
        print(f"CASO: {nombre}")
        print(f"{'='*80}")

        print(f"\n📄 FACTURA {factura['numero_factura']}:")
        print(f"   • Cantidad: {factura['cantidad']}")
        print(f"   • Valor: ${factura['valor_total']:,.2f}")

        print(f"\n📋 NOTA {nota['numero_nota']}:")
        print(f"   • Cantidad: {nota['cantidad_pendiente']}")
        print(f"   • Valor: ${nota['saldo_pendiente']:,.2f}")

        # Validar condiciones
        cantidad_ok = nota['cantidad_pendiente'] <= factura['cantidad']
        valor_ok = nota['saldo_pendiente'] <= factura['valor_total']

        print(f"\n🔍 VALIDACIÓN:")
        print(f"   • Cantidad nota ({nota['cantidad_pendiente']}) <= Cantidad factura ({factura['cantidad']}): {'✅ SÍ' if cantidad_ok else '❌ NO'}")
        print(f"   • Valor nota (${nota['saldo_pendiente']:,.2f}) <= Valor factura (${factura['valor_total']:,.2f}): {'✅ SÍ' if valor_ok else '❌ NO'}")

        # Ejecutar aplicación
        resultado = self.manager.aplicar_nota_a_factura(nota, factura)

        se_aplico = resultado is not None

        print(f"\n💡 RAZÓN:")
        print(f"   {razon}")

        print(f"\n📊 RESULTADO:")
        if se_aplico:
            print(f"   ✅ LA NOTA SE APLICÓ CORRECTAMENTE")
            print(f"   • Cantidad aplicada: {resultado['cantidad_aplicada']}")
            print(f"   • Valor aplicado: ${resultado['valor_aplicado']:,.2f}")
            print(f"   • Cantidad restante en factura: {resultado['cantidad_restante_factura']}")
            print(f"   • Valor restante en factura: ${resultado['valor_restante_factura']:,.2f}")
            print(f"   • Estado de la nota: {resultado['estado_nota']}")
        else:
            print(f"   ❌ LA NOTA NO SE APLICÓ")

        # Verificar si el resultado coincide con lo esperado
        exito = se_aplico == debe_aplicarse

        if exito:
            print(f"\n✅ TEST PASADO: El comportamiento fue el esperado")
        else:
            print(f"\n❌ TEST FALLIDO: Se esperaba que {'SÍ' if debe_aplicarse else 'NO'} se aplicara")

        self.resultados.append({
            'nombre': nombre,
            'exito': exito,
            'se_aplico': se_aplico,
            'debe_aplicarse': debe_aplicarse
        })

        return exito

    def ejecutar_todos_los_casos(self):
        """Ejecuta todos los casos de prueba"""

        print("\n" + "="*80)
        print("TEST DE APLICACIÓN DE NOTAS DE CRÉDITO")
        print("="*80)
        print("\nVerificando la lógica de aplicación según las reglas de negocio:")
        print("1. Cantidad nota <= Cantidad factura")
        print("2. Valor nota <= Valor factura")
        print("\nAmbas condiciones deben cumplirse para que la nota se aplique.")

        # ===================================================================
        # CASO 1: Nota válida - SE DEBE APLICAR
        # ===================================================================
        self.ejecutar_caso(
            nombre="Caso 1: Nota válida - Cantidad y valor menores",
            nota=self.crear_nota('NC001', '900123456', 'PROD001', 24, 96000),
            factura=self.crear_factura('FEM001', '900123456', 'PROD001', 25, 100000),
            debe_aplicarse=True,
            razon="La cantidad de la nota (24) es menor que la cantidad de la factura (25) Y "
                  "el valor de la nota ($96.000) es menor que el valor de la factura ($100.000). "
                  "✅ AMBAS condiciones se cumplen → La nota SE APLICA"
        )

        # ===================================================================
        # CASO 2: Nota con valor excedido - NO SE DEBE APLICAR
        # ===================================================================
        self.ejecutar_caso(
            nombre="Caso 2: Nota con valor excedido - Cantidad OK pero valor excede",
            nota=self.crear_nota('NC002', '900123456', 'PROD002', 24, 101000),
            factura=self.crear_factura('FEM002', '900123456', 'PROD002', 25, 100000),
            debe_aplicarse=False,
            razon="La cantidad de la nota (24) es menor que la cantidad de la factura (25) ✅ "
                  "PERO el valor de la nota ($101.000) es MAYOR que el valor de la factura ($100.000) ❌. "
                  "Como NO se cumplen AMBAS condiciones → La nota NO SE APLICA"
        )

        # ===================================================================
        # CASO 3: Nota con cantidad excedida - NO SE DEBE APLICAR
        # ===================================================================
        self.ejecutar_caso(
            nombre="Caso 3: Nota con cantidad excedida - Valor OK pero cantidad excede",
            nota=self.crear_nota('NC003', '900123456', 'PROD003', 30, 90000),
            factura=self.crear_factura('FEM003', '900123456', 'PROD003', 25, 100000),
            debe_aplicarse=False,
            razon="El valor de la nota ($90.000) es menor que el valor de la factura ($100.000) ✅ "
                  "PERO la cantidad de la nota (30) es MAYOR que la cantidad de la factura (25) ❌. "
                  "Como NO se cumplen AMBAS condiciones → La nota NO SE APLICA"
        )

        # ===================================================================
        # CASO 4: Nota igual a factura - SE DEBE APLICAR
        # ===================================================================
        self.ejecutar_caso(
            nombre="Caso 4: Nota igual a factura - Aplicación completa",
            nota=self.crear_nota('NC004', '900123456', 'PROD004', 25, 100000),
            factura=self.crear_factura('FEM004', '900123456', 'PROD004', 25, 100000),
            debe_aplicarse=True,
            razon="La cantidad de la nota (25) es igual a la cantidad de la factura (25) ✅ "
                  "Y el valor de la nota ($100.000) es igual al valor de la factura ($100.000) ✅. "
                  "AMBAS condiciones se cumplen → La nota SE APLICA COMPLETAMENTE"
        )

        # ===================================================================
        # CASO 5: Nota con ambos valores excedidos - NO SE DEBE APLICAR
        # ===================================================================
        self.ejecutar_caso(
            nombre="Caso 5: Nota con cantidad y valor excedidos",
            nota=self.crear_nota('NC005', '900123456', 'PROD005', 30, 120000),
            factura=self.crear_factura('FEM005', '900123456', 'PROD005', 25, 100000),
            debe_aplicarse=False,
            razon="La cantidad de la nota (30) es MAYOR que la cantidad de la factura (25) ❌ "
                  "Y el valor de la nota ($120.000) es MAYOR que el valor de la factura ($100.000) ❌. "
                  "NINGUNA de las condiciones se cumple → La nota NO SE APLICA"
        )

        # ===================================================================
        # CASO 6: Nota muy pequeña - SE DEBE APLICAR
        # ===================================================================
        self.ejecutar_caso(
            nombre="Caso 6: Nota pequeña aplicada a factura grande",
            nota=self.crear_nota('NC006', '900123456', 'PROD006', 5, 20000),
            factura=self.crear_factura('FEM006', '900123456', 'PROD006', 100, 400000),
            debe_aplicarse=True,
            razon="La cantidad de la nota (5) es mucho menor que la cantidad de la factura (100) ✅ "
                  "Y el valor de la nota ($20.000) es mucho menor que el valor de la factura ($400.000) ✅. "
                  "AMBAS condiciones se cumplen → La nota SE APLICA (aplicación parcial)"
        )

        # ===================================================================
        # RESUMEN FINAL
        # ===================================================================
        print(f"\n\n{'='*80}")
        print("RESUMEN DE RESULTADOS")
        print(f"{'='*80}\n")

        total = len(self.resultados)
        exitosos = sum(1 for r in self.resultados if r['exito'])
        fallidos = total - exitosos

        for i, resultado in enumerate(self.resultados, 1):
            icono = "✅" if resultado['exito'] else "❌"
            estado = "PASADO" if resultado['exito'] else "FALLIDO"
            print(f"{icono} Test {i}: {resultado['nombre']} - {estado}")

        print(f"\n{'='*80}")
        print(f"Total de tests: {total}")
        print(f"Tests exitosos: {exitosos} ({exitosos/total*100:.1f}%)")
        print(f"Tests fallidos: {fallidos} ({fallidos/total*100:.1f}%)")
        print(f"{'='*80}\n")

        if fallidos == 0:
            print("🎉 ¡TODOS LOS TESTS PASARON! La lógica de aplicación funciona correctamente.\n")
            return True
        else:
            print(f"⚠️  {fallidos} test(s) fallaron. Revisar la implementación.\n")
            return False

    def limpiar(self):
        """Limpia la base de datos temporal"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


if __name__ == '__main__':
    test = TestAplicacionNotas()
    try:
        exito = test.ejecutar_todos_los_casos()
        test.limpiar()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ ERROR durante la ejecución del test: {e}")
        import traceback
        traceback.print_exc()
        test.limpiar()
        sys.exit(1)
