#!/usr/bin/env python3
"""
Script para analizar datos anteriores a diciembre 2025
"""
import sqlite3
from datetime import datetime

def analizar_datos(db_path='./data/notas_credito.db'):
    """Analizar datos antes de diciembre 2025"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("="*80)
    print("ANÁLISIS DE DATOS PRE-DICIEMBRE 2025")
    print("="*80 + "\n")

    # Fecha límite
    fecha_limite = '2025-12-01'

    # Analizar aplicaciones_notas
    print("TABLA: aplicaciones_notas")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM aplicaciones_notas")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}")

    cursor.execute(f"SELECT COUNT(*) FROM aplicaciones_notas WHERE fecha_factura < '{fecha_limite}'")
    pre_dic = cursor.fetchone()[0]
    print(f"Registros antes de dic 2025: {pre_dic}")

    cursor.execute("SELECT MIN(fecha_factura), MAX(fecha_factura) FROM aplicaciones_notas")
    min_fecha, max_fecha = cursor.fetchone()
    print(f"Rango de fechas: {min_fecha} a {max_fecha}")
    print()

    # Analizar facturas
    print("TABLA: facturas")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM facturas")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}")

    cursor.execute(f"SELECT COUNT(*) FROM facturas WHERE fecha_factura < '{fecha_limite}'")
    pre_dic = cursor.fetchone()[0]
    print(f"Registros antes de dic 2025: {pre_dic}")

    cursor.execute("SELECT MIN(fecha_factura), MAX(fecha_factura) FROM facturas")
    min_fecha, max_fecha = cursor.fetchone()
    print(f"Rango de fechas (fecha_factura): {min_fecha} a {max_fecha}")

    cursor.execute("SELECT MIN(fecha_proceso), MAX(fecha_proceso) FROM facturas WHERE fecha_proceso IS NOT NULL")
    min_fecha, max_fecha = cursor.fetchone()
    print(f"Rango de fechas (fecha_proceso): {min_fecha} a {max_fecha}")
    print()

    # Analizar facturas_rechazadas
    print("TABLA: facturas_rechazadas")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM facturas_rechazadas")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}")

    cursor.execute(f"SELECT COUNT(*) FROM facturas_rechazadas WHERE fecha_factura < '{fecha_limite}'")
    pre_dic = cursor.fetchone()[0]
    print(f"Registros antes de dic 2025: {pre_dic}")

    cursor.execute("SELECT MIN(fecha_factura), MAX(fecha_factura) FROM facturas_rechazadas")
    min_fecha, max_fecha = cursor.fetchone()
    print(f"Rango de fechas: {min_fecha} a {max_fecha}")
    print()

    # Analizar notas_credito
    print("TABLA: notas_credito")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM notas_credito")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}")

    cursor.execute(f"SELECT COUNT(*) FROM notas_credito WHERE fecha_nota < '{fecha_limite}'")
    pre_dic = cursor.fetchone()[0]
    print(f"Registros antes de dic 2025: {pre_dic}")

    cursor.execute("SELECT MIN(fecha_nota), MAX(fecha_nota) FROM notas_credito")
    min_fecha, max_fecha = cursor.fetchone()
    print(f"Rango de fechas: {min_fecha} a {max_fecha}")
    print()

    # Analizar tipos_inventario_detectados
    print("TABLA: tipos_inventario_detectados")
    print("-"*80)
    cursor.execute("SELECT COUNT(*) FROM tipos_inventario_detectados")
    total = cursor.fetchone()[0]
    print(f"Total registros: {total}")

    cursor.execute(f"SELECT COUNT(*) FROM tipos_inventario_detectados WHERE primera_deteccion < '{fecha_limite}'")
    pre_dic = cursor.fetchone()[0]
    print(f"Registros detectados antes de dic 2025: {pre_dic}")
    print()

    print("="*80)

    conn.close()

if __name__ == '__main__':
    import os
    os.chdir('/home/user/cipa')
    analizar_datos()
