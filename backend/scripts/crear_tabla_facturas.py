#!/usr/bin/env python3
"""
Script para crear la tabla de facturas en la base de datos
"""
import sqlite3
import sys
from pathlib import Path

# Agregar backend al path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

DB_PATH = BACKEND_DIR / 'data' / 'notas_credito.db'

def crear_tabla_facturas():
    """Crea la tabla de facturas si no existe"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Tabla de facturas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_factura TEXT NOT NULL UNIQUE,
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
            estado TEXT DEFAULT 'VALIDA',
            tiene_nota_credito BOOLEAN DEFAULT 0,
            es_valida BOOLEAN DEFAULT 1,
            razon_invalidez TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Crear índices para mejorar performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_cliente
        ON facturas(nit_cliente)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_fecha
        ON facturas(fecha_factura)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_facturas_estado
        ON facturas(estado)
    ''')

    conn.commit()
    conn.close()

    print("✅ Tabla de facturas creada exitosamente")
    print(f"📍 Base de datos: {DB_PATH}")

if __name__ == '__main__':
    crear_tabla_facturas()
