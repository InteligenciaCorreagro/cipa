#!/usr/bin/env python3
"""
Script para poblar la tabla de facturas con datos de transacciones diarias
Genera facturas de ejemplo con valores transados para testing

IMPORTANTE: Usa las mismas reglas de negocio que el proceso de Excel:
- Monto mínimo: $498,000 COP por factura
- Tipos de inventario PERMITIDOS (excluye los 24 tipos bloqueados)
- Tipos de inventario vienen tal cual como en el API SIESA
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Agregar backend al path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

DB_PATH = BACKEND_DIR / 'data' / 'notas_credito.db'

# IMPORTANTE: Monto mínimo según reglas de negocio
MONTO_MINIMO = 498000.0

# Datos de ejemplo
CLIENTES = [
    ("900123456", "Agroindustrias del Valle S.A."),
    ("800234567", "Comercializadora Agropecuaria Ltda"),
    ("900345678", "Distribuidora de Insumos Agrícolas"),
    ("800456789", "Fertilizantes del Norte S.A."),
    ("900567890", "Semillas y Agroquímicos S.A.S"),
    ("800678901", "Cooperativa Agropecuaria del Sur"),
    ("900789012", "Productos Agrícolas del Cauca"),
    ("800890123", "Agrocomercial del Tolima Ltda"),
]

# IMPORTANTE: Tipos de inventario PERMITIDOS (como vienen del API SIESA)
# Estos NO están en la lista de excluidos
PRODUCTOS = [
    ("FERT001", "Fertilizante NPK 15-15-15", "FERTILIZ"),
    ("FERT002", "Urea Granulada 46%", "FERTILIZ"),
    ("HERB001", "Herbicida Glifosato 48%", "HERBICIDA"),
    ("HERB002", "Herbicida 2,4-D Amina", "HERBICIDA"),
    ("FUNG001", "Fungicida Mancozeb 80%", "FUNGICIDA"),
    ("INSEC001", "Insecticida Clorpirifos", "INSECTICIDA"),
    ("SEM001", "Semilla de Maíz Híbrido", "SEMILLAS"),
    ("SEM002", "Semilla de Arroz Premium", "SEMILLAS"),
    ("ABONO001", "Abono Orgánico Compostado", "ABONOS"),
    ("NUTRI001", "Nutriente Foliar Completo", "NUTRIENTES"),
    ("INVAGRIC", "Insumo Agrícola General", "INVAGRIC"),
    ("PRODUCTO", "Producto Agropecuario", "PRODUCTO"),
]

def generar_facturas_dia(fecha, cantidad_facturas=10):
    """
    Genera facturas para un día específico siguiendo reglas de negocio

    IMPORTANTE: Las facturas generadas cumplen con:
    - Monto mínimo de $498,000 COP
    - Tipos de inventario permitidos
    - 70% tienen transacciones
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    facturas_creadas = 0
    fecha_str = fecha.strftime('%Y-%m-%d')

    for i in range(cantidad_facturas):
        # Seleccionar cliente y producto aleatorio
        nit, nombre_cliente = random.choice(CLIENTES)
        codigo_prod, nombre_prod, tipo_inv = random.choice(PRODUCTOS)

        # Generar número de factura único (formato similar al API)
        numero_factura = f"FV{fecha.strftime('%Y%m%d')}{str(i+1).zfill(4)}"

        # Generar valores aleatorios PERO asegurando monto mínimo
        # Para cumplir el monto mínimo de $498,000, generamos valores apropiados
        cantidad = random.uniform(5, 100)
        # Precio unitario que asegure superar el monto mínimo
        precio_unitario = random.uniform(
            MONTO_MINIMO * 1.1 / cantidad,  # Al menos 10% más del mínimo
            2000000  # Hasta 2M por unidad
        )
        valor_total = cantidad * precio_unitario

        # Validar que cumple monto mínimo
        if valor_total < MONTO_MINIMO:
            valor_total = MONTO_MINIMO * random.uniform(1.0, 2.0)
            precio_unitario = valor_total / cantidad

        # Algunas facturas tienen transacciones (70% de probabilidad)
        tiene_transaccion = random.random() < 0.7

        if tiene_transaccion:
            # Valor transado entre 50% y 100% del valor total
            porcentaje_transado = random.uniform(0.5, 1.0)
            valor_transado = valor_total * porcentaje_transado
            cantidad_transada = cantidad * porcentaje_transado
            tiene_nota_credito = random.random() < 0.3  # 30% tienen nota de crédito
            estado = 'PROCESADA' if porcentaje_transado >= 0.99 else 'PARCIAL'
        else:
            valor_transado = 0
            cantidad_transada = 0
            tiene_nota_credito = False
            estado = 'VALIDA'

        # Todas son válidas porque ya cumplen las reglas
        es_valida = True
        razon_invalidez = None

        try:
            cursor.execute('''
                INSERT INTO facturas (
                    numero_factura, fecha_factura, nit_cliente, nombre_cliente,
                    codigo_producto, nombre_producto, tipo_inventario,
                    valor_total, cantidad, valor_transado, cantidad_transada,
                    estado, tiene_nota_credito, es_valida, razon_invalidez,
                    fecha_registro
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                numero_factura, fecha_str, nit, nombre_cliente,
                codigo_prod, nombre_prod, tipo_inv,
                valor_total, cantidad, valor_transado, cantidad_transada,
                estado, tiene_nota_credito, es_valida, razon_invalidez,
                datetime.now().isoformat()
            ))
            facturas_creadas += 1
        except sqlite3.IntegrityError:
            # Si la factura ya existe, continuar
            pass

    conn.commit()
    conn.close()

    return facturas_creadas

def poblar_ultimos_n_dias(dias=30, facturas_por_dia=15):
    """Poblar facturas para los últimos N días"""
    print(f"Poblando facturas para los últimos {dias} días...")
    print(f"Facturas por día: {facturas_por_dia}")
    print(f"Base de datos: {DB_PATH}")
    print("=" * 60)

    total_creadas = 0
    hoy = datetime.now()

    for i in range(dias):
        fecha = hoy - timedelta(days=i)
        cantidad = generar_facturas_dia(fecha, facturas_por_dia)
        total_creadas += cantidad
        print(f"📅 {fecha.strftime('%Y-%m-%d')}: {cantidad} facturas creadas")

    print("=" * 60)
    print(f"✅ Total de facturas creadas: {total_creadas}")

    # Mostrar estadísticas
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM facturas')
    total_facturas = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM facturas WHERE valor_transado > 0')
    total_transadas = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(valor_transado) FROM facturas WHERE es_valida = 1')
    valor_total_transado = cursor.fetchone()[0] or 0

    conn.close()

    print(f"\n📊 ESTADÍSTICAS:")
    print(f"  Total facturas en BD: {total_facturas}")
    print(f"  Facturas transadas: {total_transadas}")
    print(f"  Valor total transado: ${valor_total_transado:,.2f}")

def poblar_ayer(facturas=20):
    """Poblar facturas solo para ayer"""
    ayer = datetime.now() - timedelta(days=1)
    print(f"Poblando facturas para ayer ({ayer.strftime('%Y-%m-%d')})...")
    print(f"Cantidad de facturas: {facturas}")
    print("=" * 60)

    cantidad = generar_facturas_dia(ayer, facturas)

    print(f"✅ {cantidad} facturas creadas para ayer")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Poblar tabla de facturas con datos de ejemplo')
    parser.add_argument('--dias', type=int, default=30, help='Número de días a poblar (default: 30)')
    parser.add_argument('--por-dia', type=int, default=15, help='Facturas por día (default: 15)')
    parser.add_argument('--solo-ayer', action='store_true', help='Poblar solo el día de ayer')
    parser.add_argument('--ayer-cantidad', type=int, default=20, help='Cantidad de facturas para ayer (default: 20)')

    args = parser.parse_args()

    if args.solo_ayer:
        poblar_ayer(args.ayer_cantidad)
    else:
        poblar_ultimos_n_dias(args.dias, args.por_dia)
