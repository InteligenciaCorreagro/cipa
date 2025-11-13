#!/usr/bin/env python3
"""
Script de pruebas básicas del sistema de gestión de facturas
Valida el funcionamiento de los componentes principales
"""
import sys
import os

# Agregar backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_business_rules():
    """Prueba validador de reglas de negocio"""
    print("\n" + "="*60)
    print("TEST: Business Rules Validator")
    print("="*60)

    from core.business_rules import BusinessRulesValidator
    
    validator = BusinessRulesValidator()
    
    # Test 1: Identificar nota crédito
    print("\n1. Identificación de notas crédito:")
    factura_nc = {'f_prefijo': 'N', 'f_nrodocto': '001234'}
    factura_regular = {'f_prefijo': 'F', 'f_nrodocto': '005678'}
    
    assert validator.es_nota_credito(factura_nc) == True
    assert validator.es_nota_credito(factura_regular) == False
    print("   ✓ Notas crédito identificadas correctamente")
    
    # Test 2: Tipo de inventario excluido
    print("\n2. Validación de tipos de inventario:")
    factura_excluida = {
        'f_prefijo': 'F',
        'f_cod_tipo_inv': 'VSMENOR',
        'f_valor_subtotal_local': 500000
    }
    factura_permitida = {
        'f_prefijo': 'F',
        'f_cod_tipo_inv': 'VENTA_NORMAL',
        'f_valor_subtotal_local': 500000
    }
    
    assert validator.tipo_inventario_permitido(factura_excluida) == False
    assert validator.tipo_inventario_permitido(factura_permitida) == True
    print("   ✓ Tipos de inventario validados correctamente")
    
    # Test 3: Monto mínimo
    print("\n3. Validación de monto mínimo:")
    factura_valida = {'f_valor_subtotal_local': 500000}
    factura_invalida = {'f_valor_subtotal_local': 400000}
    
    assert validator.cumple_monto_minimo(factura_valida) == True
    assert validator.cumple_monto_minimo(factura_invalida) == False
    print(f"   ✓ Monto mínimo ${validator.MONTO_MINIMO:,.0f} validado correctamente")
    
    # Test 4: Filtrado completo
    print("\n4. Filtrado completo de facturas:")
    facturas_test = [
        # Factura válida
        {
            'f_prefijo': 'F',
            'f_nrodocto': '001',
            'f_cod_tipo_inv': 'VENTA_NORMAL',
            'f_valor_subtotal_local': 500000
        },
        # Nota crédito
        {
            'f_prefijo': 'N',
            'f_nrodocto': '002',
            'f_cod_tipo_inv': 'VENTA_NORMAL',
            'f_valor_subtotal_local': 300000
        },
        # Tipo excluido
        {
            'f_prefijo': 'F',
            'f_nrodocto': '003',
            'f_cod_tipo_inv': 'VSMENOR',
            'f_valor_subtotal_local': 600000
        },
        # Monto bajo
        {
            'f_prefijo': 'F',
            'f_nrodocto': '004',
            'f_cod_tipo_inv': 'VENTA_NORMAL',
            'f_valor_subtotal_local': 400000
        }
    ]
    
    validas, notas, rechazadas = validator.filtrar_facturas(facturas_test)
    
    assert len(validas) == 1
    assert len(notas) == 1
    assert len(rechazadas) == 2
    print(f"   ✓ Filtrado correcto: {len(validas)} válidas, {len(notas)} notas, {len(rechazadas)} rechazadas")
    
    print("\n✅ TODOS LOS TESTS DE BUSINESS RULES PASARON\n")
    return True

def test_notas_credito_manager():
    """Prueba gestor de notas crédito"""
    print("\n" + "="*60)
    print("TEST: Notas Crédito Manager")
    print("="*60)

    from core.notas_credito_manager import NotasCreditoManager
    from datetime import datetime
    import tempfile
    
    # Usar base de datos temporal para tests
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_test = tf.name
    
    try:
        manager = NotasCreditoManager(db_test)
        
        # Test 1: Crear base de datos
        print("\n1. Creación de base de datos:")
        assert os.path.exists(db_test)
        print("   ✓ Base de datos creada correctamente")
        
        # Test 2: Registrar nota crédito
        print("\n2. Registro de nota crédito:")
        nota_test = {
            'f_prefijo': 'N',
            'f_nrodocto': '001234',
            'f_fecha': datetime.now().isoformat(),
            'f_cliente_desp': '900123456',
            'f_cliente_fact_razon_soc': 'Cliente Test',
            'f_cod_item': 'PROD001',
            'f_desc_item': 'Producto Test',
            'f_valor_subtotal_local': 1000000,
            'f_cant_base': 100.0
        }
        
        resultado = manager.registrar_nota_credito(nota_test)
        assert resultado == True
        print("   ✓ Nota crédito registrada correctamente")
        
        # Test 3: No duplicar nota
        print("\n3. Validación de duplicados:")
        resultado_dup = manager.registrar_nota_credito(nota_test)
        assert resultado_dup == False
        print("   ✓ Duplicados prevenidos correctamente")
        
        # Test 4: Obtener notas pendientes
        print("\n4. Consulta de notas pendientes:")
        notas = manager.obtener_notas_pendientes('900123456', 'PROD001')
        assert len(notas) == 1
        assert notas[0]['numero_nota'] == 'N001234'
        print("   ✓ Consulta de notas pendientes correcta")
        
        # Test 5: Aplicar nota a factura
        print("\n5. Aplicación de nota a factura:")
        factura_test = {
            'numero_factura': 'F005678',
            'nit_comprador': '900123456',
            'codigo_producto_api': 'PROD001',
            'valor_total': 800000,
            'cantidad_original': 80.0,
            'fecha_factura': datetime.now().date()
        }
        
        nota_bd = notas[0]
        aplicacion = manager.aplicar_nota_a_factura(nota_bd, factura_test)
        
        assert aplicacion is not None
        assert aplicacion['valor_aplicado'] == 800000
        print(f"   ✓ Nota aplicada: ${aplicacion['valor_aplicado']:,.2f}")
        
        # Test 6: Resumen
        print("\n6. Obtención de resumen:")
        resumen = manager.obtener_resumen_notas()
        assert resumen['notas_pendientes'] == 1
        assert resumen['total_aplicaciones'] == 1
        print(f"   ✓ Resumen correcto: {resumen['notas_pendientes']} pendientes, "
              f"{resumen['total_aplicaciones']} aplicaciones")
        
        print("\n✅ TODOS LOS TESTS DE NOTAS CRÉDITO PASARON\n")
        return True
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(db_test):
            os.remove(db_test)

def test_excel_processor():
    """Prueba procesador de Excel"""
    print("\n" + "="*60)
    print("TEST: Excel Processor")
    print("="*60)

    from core.excel_processor import ExcelProcessor
    from datetime import datetime
    
    processor = ExcelProcessor()
    
    # Test 1: Transformar factura
    print("\n1. Transformación de factura:")
    factura_api = {
        'f_prefijo': 'F',
        'f_nrodocto': '123456',
        'f_fecha': '2025-10-26T00:00:00',
        'f_desc_grupo_impositivo': 'IVA 19% RTF',
        'f_ciudad_punto_envio': '001-Pereira',
        'f_um_inv_desc': 'KILOGRAMO',
        'f_cant_base': 100.0,
        'f_um_base': 'BT40',
        'f_valor_subtotal_local': 4000000,
        'f_cliente_desp': '900123456',
        'f_cliente_fact_razon_soc': 'Cliente Test',
        'f_desc_item': 'Producto Test',
        'f_desc_tipo_inv': 'Venta Normal',
        'f_cod_item': 'PROD001'
    }
    
    factura_transformada = processor.transformar_factura(factura_api)
    
    assert factura_transformada['numero_factura'] == 'F123456'
    assert factura_transformada['iva'] == '19'
    assert factura_transformada['municipio'] == 'Pereira'
    assert factura_transformada['unidad_medida'] == 'KG'
    assert factura_transformada['cantidad'] == 4000.0  # 100 * 40
    assert factura_transformada['cantidad_original'] == 100.0
    print("   ✓ Factura transformada correctamente")
    print(f"   - Número: {factura_transformada['numero_factura']}")
    print(f"   - IVA: {factura_transformada['iva']}%")
    print(f"   - Ciudad: {factura_transformada['municipio']}")
    print(f"   - Cantidad: {factura_transformada['cantidad']:.2f} {factura_transformada['unidad_medida']}")
    
    # Test 2: Extraer IVA
    print("\n2. Extracción de IVA:")
    assert processor._extraer_iva('IVA 19% RTF BIENES') == '19'
    assert processor._extraer_iva('IVA 5%') == '5'
    assert processor._extraer_iva('SIN IVA') == '0'
    print("   ✓ IVA extraído correctamente")
    
    # Test 3: Normalizar unidad de medida
    print("\n3. Normalización de unidades:")
    assert processor._normalizar_unidad_medida('KILOGRAMO') == 'KG'
    assert processor._normalizar_unidad_medida('LITRO') == 'LT'
    assert processor._normalizar_unidad_medida('UNIDAD') == 'UN'
    assert processor._normalizar_unidad_medida('BULTO') == 'KG'
    print("   ✓ Unidades normalizadas correctamente")
    
    # Test 4: Extraer multiplicador
    print("\n4. Extracción de multiplicador:")
    assert processor._extraer_multiplicador_um_base('BT40') == 40.0
    assert processor._extraer_multiplicador_um_base('BT30') == 30.0
    assert processor._extraer_multiplicador_um_base('KLS') == 1.0
    print("   ✓ Multiplicadores extraídos correctamente")
    
    print("\n✅ TODOS LOS TESTS DE EXCEL PROCESSOR PASARON\n")
    return True

def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("SUITE DE PRUEBAS - SISTEMA DE GESTIÓN DE FACTURAS")
    print("="*60)
    
    resultados = []
    
    try:
        resultados.append(("Business Rules", test_business_rules()))
    except Exception as e:
        print(f"\n❌ Error en Business Rules: {e}")
        resultados.append(("Business Rules", False))
        import traceback
        traceback.print_exc()
    
    try:
        resultados.append(("Notas Crédito", test_notas_credito_manager()))
    except Exception as e:
        print(f"\n❌ Error en Notas Crédito: {e}")
        resultados.append(("Notas Crédito", False))
        import traceback
        traceback.print_exc()
    
    try:
        resultados.append(("Excel Processor", test_excel_processor()))
    except Exception as e:
        print(f"\n❌ Error en Excel Processor: {e}")
        resultados.append(("Excel Processor", False))
        import traceback
        traceback.print_exc()
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    total = len(resultados)
    exitosos = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{status} - {nombre}")
    
    print(f"\nTotal: {exitosos}/{total} tests pasaron")
    
    if exitosos == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        return 0
    else:
        print(f"\n⚠️  {total - exitosos} test(s) fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
