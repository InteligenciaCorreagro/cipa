#!/usr/bin/env python3
"""
Script para crear la tabla de facturas en la base de datos
IMPORTANTE: Permite múltiples líneas por factura (como el Excel de operativa)
"""
import sqlite3
import sys
import os
from pathlib import Path

# Agregar backend al path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Usar la misma BD del proyecto raíz (no backend/data/)
PROJECT_ROOT = BACKEND_DIR.parent
DB_PATH = Path(os.getenv('DB_PATH', str(PROJECT_ROOT / 'data' / 'notas_credito.db')))

def crear_tabla_facturas():
    """
    Crea la tabla de facturas si no existe
    IMPORTANTE: Permite múltiples líneas por factura (una factura FME123 puede tener 4 líneas)
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Tabla de facturas - Guarda LÍNEAS COMPLETAS igual que el Excel de operativa
    # IMPORTANTE: Una factura puede tener múltiples líneas (productos)
    # El constraint UNIQUE es (numero_factura, codigo_producto) para permitir múltiples líneas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_factura TEXT NOT NULL,
            fecha_factura DATE NOT NULL,
            nit_cliente TEXT NOT NULL,
            nombre_cliente TEXT NOT NULL,
            codigo_producto TEXT NOT NULL,
            nombre_producto TEXT NOT NULL,
            tipo_inventario TEXT,
            valor_total REAL NOT NULL,
            cantidad REAL NOT NULL,
            valor_transado REAL DEFAULT 0,
            cantidad_transada REAL DEFAULT 0,
            descripcion_nota_aplicada TEXT,
            estado TEXT DEFAULT 'VALIDA',
            tiene_nota_credito INTEGER DEFAULT 0,
            es_valida INTEGER DEFAULT 1,
            razon_invalidez TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_proceso DATE NOT NULL,
            UNIQUE(numero_factura, codigo_producto, fecha_proceso)
        )
    ''')

    # Crear índices para mejorar performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_numero
        ON facturas(numero_factura)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_cliente
        ON facturas(nit_cliente)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_fecha
        ON facturas(fecha_factura)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_fecha_proceso
        ON facturas(fecha_proceso)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_estado
        ON facturas(estado)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_nota_aplicada
        ON facturas(tiene_nota_credito)
    ''')

    conn.commit()
    conn.close()

    print("✅ Tabla de facturas creada exitosamente")
    print(f"📍 Base de datos: {DB_PATH}")

if __name__ == '__main__':
    crear_tabla_facturas()
