#!/usr/bin/env python3
"""
Script de consulta y reporte de notas crédito
Permite visualizar el estado actual de las notas crédito en el sistema
"""
import os
import sys
from datetime import datetime
from src.notas_credito_manager import NotasCreditoManager

def print_separator(char='=', length=80):
    """Imprime un separador"""
    print(char * length)

def print_section(title):
    """Imprime título de sección"""
    print(f"\n{title}")
    print_separator('-')

def consultar_resumen():
    """Muestra resumen general de notas crédito"""
    print_separator()
    print("CONSULTA DE NOTAS CRÉDITO - RESUMEN GENERAL")
    print_separator()
    
    db_path = os.getenv('DB_PATH', './data/notas_credito.db')
    
    if not os.path.exists(db_path):
        print(f"\n❌ Error: No se encontró la base de datos en {db_path}")
        print("   Ejecute el proceso principal al menos una vez para inicializar la BD")
        return
    
    manager = NotasCreditoManager(db_path)
    resumen = manager.obtener_resumen_notas()
    
    print_section("📊 RESUMEN GENERAL")
    print(f"Notas crédito pendientes:      {resumen.get('notas_pendientes', 0)}")
    print(f"Saldo pendiente total:         ${resumen.get('saldo_pendiente_total', 0):,.2f} COP")
    print(f"Notas aplicadas (histórico):   {resumen.get('notas_aplicadas', 0)}")
    print(f"Total aplicaciones realizadas: {resumen.get('total_aplicaciones', 0)}")
    print(f"Monto total aplicado:          ${resumen.get('monto_total_aplicado', 0):,.2f} COP")
    
    return manager

def consultar_notas_pendientes(manager):
    """Muestra detalle de notas crédito pendientes"""
    import sqlite3
    
    conn = sqlite3.connect(manager.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM notas_credito
        WHERE estado = 'PENDIENTE'
        ORDER BY fecha_nota ASC
    ''')
    
    notas = cursor.fetchall()
    conn.close()
    
    if not notas:
        print("\n✅ No hay notas crédito pendientes")
        return
    
    print_section("📋 NOTAS CRÉDITO PENDIENTES")
    print(f"Total: {len(notas)} notas\n")
    
    for nota in notas:
        print(f"Nota: {nota['numero_nota']}")
        print(f"  Fecha:            {nota['fecha_nota']}")
        print(f"  Cliente:          {nota['nombre_cliente']} (NIT: {nota['nit_cliente']})")
        print(f"  Producto:         {nota['nombre_producto']} (Código: {nota['codigo_producto']})")
        print(f"  Valor original:   ${nota['valor_total']:,.2f}")
        print(f"  Saldo pendiente:  ${nota['saldo_pendiente']:,.2f}")
        print(f"  Cantidad original: {nota['cantidad']:.5f}")
        print(f"  Cantidad pendiente: {nota['cantidad_pendiente']:.5f}")
        print(f"  Registrada:       {nota['fecha_registro']}")
        print()

def consultar_aplicaciones_recientes(manager, dias=7):
    """Muestra aplicaciones recientes de notas crédito"""
    import sqlite3
    from datetime import timedelta
    
    conn = sqlite3.connect(manager.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT * FROM aplicaciones_notas
        WHERE fecha_aplicacion >= ?
        ORDER BY fecha_aplicacion DESC
    ''', (fecha_limite,))
    
    aplicaciones = cursor.fetchall()
    conn.close()
    
    if not aplicaciones:
        print(f"\n✅ No hay aplicaciones en los últimos {dias} días")
        return
    
    print_section(f"🔄 APLICACIONES RECIENTES (últimos {dias} días)")
    print(f"Total: {len(aplicaciones)} aplicaciones\n")
    
    for app in aplicaciones:
        print(f"Aplicación ID: {app['id']}")
        print(f"  Nota:             {app['numero_nota']}")
        print(f"  Factura:          {app['numero_factura']}")
        print(f"  Fecha factura:    {app['fecha_factura']}")
        print(f"  Cliente (NIT):    {app['nit_cliente']}")
        print(f"  Producto:         {app['codigo_producto']}")
        print(f"  Valor aplicado:   ${app['valor_aplicado']:,.2f}")
        print(f"  Cantidad aplicada: {app['cantidad_aplicada']:.5f}")
        print(f"  Fecha aplicación: {app['fecha_aplicacion']}")
        print()

def consultar_historial_nota(manager, numero_nota):
    """Muestra historial completo de una nota específica"""
    import sqlite3
    
    conn = sqlite3.connect(manager.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Obtener información de la nota
    cursor.execute('''
        SELECT * FROM notas_credito
        WHERE numero_nota = ?
    ''', (numero_nota,))
    
    nota = cursor.fetchone()
    
    if not nota:
        print(f"\n❌ No se encontró la nota {numero_nota}")
        conn.close()
        return
    
    print_section(f"📄 HISTORIAL DE NOTA: {numero_nota}")
    
    print("\nInformación General:")
    print(f"  Estado:           {nota['estado']}")
    print(f"  Fecha nota:       {nota['fecha_nota']}")
    print(f"  Cliente:          {nota['nombre_cliente']} (NIT: {nota['nit_cliente']})")
    print(f"  Producto:         {nota['nombre_producto']} (Código: {nota['codigo_producto']})")
    print(f"  Valor original:   ${nota['valor_total']:,.2f}")
    print(f"  Saldo pendiente:  ${nota['saldo_pendiente']:,.2f}")
    print(f"  Registrada:       {nota['fecha_registro']}")
    if nota['fecha_aplicacion_completa']:
        print(f"  Aplicada completamente: {nota['fecha_aplicacion_completa']}")
    
    # Obtener aplicaciones
    cursor.execute('''
        SELECT * FROM aplicaciones_notas
        WHERE numero_nota = ?
        ORDER BY fecha_aplicacion ASC
    ''', (numero_nota,))
    
    aplicaciones = cursor.fetchall()
    conn.close()
    
    if aplicaciones:
        print(f"\nAplicaciones ({len(aplicaciones)}):")
        for i, app in enumerate(aplicaciones, 1):
            print(f"\n  {i}. Factura: {app['numero_factura']}")
            print(f"     Fecha:           {app['fecha_factura']}")
            print(f"     Valor aplicado:  ${app['valor_aplicado']:,.2f}")
            print(f"     Cantidad:        {app['cantidad_aplicada']:.5f}")
            print(f"     Fecha aplicación: {app['fecha_aplicacion']}")
    else:
        print("\n  No se han realizado aplicaciones de esta nota")

def menu_interactivo():
    """Menú interactivo para consultas"""
    manager = consultar_resumen()
    
    if not manager:
        return
    
    while True:
        print_section("MENÚ DE OPCIONES")
        print("1. Ver notas crédito pendientes")
        print("2. Ver aplicaciones recientes (últimos 7 días)")
        print("3. Ver aplicaciones recientes (últimos 30 días)")
        print("4. Consultar historial de nota específica")
        print("5. Actualizar resumen")
        print("0. Salir")
        
        opcion = input("\nSeleccione una opción: ").strip()
        
        if opcion == '1':
            consultar_notas_pendientes(manager)
        elif opcion == '2':
            consultar_aplicaciones_recientes(manager, dias=7)
        elif opcion == '3':
            consultar_aplicaciones_recientes(manager, dias=30)
        elif opcion == '4':
            numero_nota = input("Ingrese el número de la nota (ej: N001234): ").strip()
            consultar_historial_nota(manager, numero_nota)
        elif opcion == '5':
            manager = consultar_resumen()
        elif opcion == '0':
            print("\n¡Hasta luego!")
            break
        else:
            print("\n❌ Opción no válida")
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            # Modo comando directo
            comando = sys.argv[1].lower()
            db_path = os.getenv('DB_PATH', './data/notas_credito.db')
            manager = NotasCreditoManager(db_path)
            
            if comando == 'resumen':
                consultar_resumen()
            elif comando == 'pendientes':
                consultar_notas_pendientes(manager)
            elif comando == 'aplicaciones':
                dias = int(sys.argv[2]) if len(sys.argv) > 2 else 7
                consultar_aplicaciones_recientes(manager, dias)
            elif comando == 'nota':
                if len(sys.argv) < 3:
                    print("❌ Debe especificar el número de nota")
                else:
                    consultar_historial_nota(manager, sys.argv[2])
            else:
                print(f"❌ Comando no reconocido: {comando}")
                print("\nComandos disponibles:")
                print("  resumen      - Muestra resumen general")
                print("  pendientes   - Lista notas pendientes")
                print("  aplicaciones [dias] - Aplicaciones recientes")
                print("  nota [numero] - Historial de nota específica")
        else:
            # Modo interactivo
            menu_interactivo()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
