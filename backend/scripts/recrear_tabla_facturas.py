#!/usr/bin/env python3
"""
Script para recrear la tabla de facturas con campos EXACTOS del API SIESA

IMPORTANTE: La tabla se crea con TODOS los campos tal cual vienen del API
Cada LÍNEA de factura es un registro separado
"""
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
DB_PATH = BACKEND_DIR / 'data' / 'notas_credito.db'

def recrear_tabla_facturas():
    """Elimina y recrea la tabla facturas con estructura correcta"""

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("="*70)
    print("RECREANDO TABLA DE FACTURAS CON CAMPOS DEL API SIESA")
    print("="*70)

    # 1. Eliminar tabla existente
    print("\n🗑️  Eliminando tabla existente...")
    cursor.execute('DROP TABLE IF EXISTS facturas')
    print("✅ Tabla eliminada")

    # 2. Crear nueva tabla con TODOS los campos del API
    print("\n📋 Creando nueva tabla con campos del API...")
    cursor.execute('''
        CREATE TABLE facturas (
            -- ID interno
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Campos básicos de factura (del API)
            f_prefijo TEXT NOT NULL,
            f_nrodocto INTEGER NOT NULL,
            numero_factura TEXT NOT NULL,  -- f_prefijo + f_nrodocto
            f_numero INTEGER,
            f_fecha TEXT,

            -- Cliente
            f_cliente_desp TEXT,
            f_cliente_fact_razon_soc TEXT,
            f_ciudad_punto_envio TEXT,

            -- Producto/Item
            f_desc_item TEXT,
            f_cod_item TEXT,  -- Agregado para código de producto

            -- Unidades de medida
            f_um_base TEXT,
            f_um_inv_desc TEXT,
            f_cant_base REAL,
            f_peso REAL,

            -- Valores monetarios
            f_valor_subtotal_local REAL,
            f_precio_unit_docto REAL,

            -- Condiciones de pago
            f_desc_cond_pago TEXT,

            -- Tipo de inventario (CRÍTICO para reglas de negocio)
            f_tipo_inv TEXT,
            f_desc_tipo_inv TEXT,
            f_desc_un_movto TEXT,

            -- Impuestos
            f_grupo_impositivo TEXT,
            f_desc_grupo_impositivo TEXT,

            -- Notas y causales
            f_notas_causal_dev TEXT,

            -- Campos técnicos del API
            f_rowid_movto INTEGER,
            f_rowid INTEGER,
            f_id_clase_docto INTEGER,
            f_cia INTEGER,
            f_destare_ocul INTEGER,

            -- Utilidades (del API)
            f_divisor_margen_prom REAL,
            f_utilidad_prom_f REAL,
            f_divisor_margen_mp REAL,
            f_utilidad_mp_f REAL,

            -- Clasificaciones adicionales (del API)
            f_01_006 TEXT,
            f_01_003 TEXT,
            f_01_011 TEXT,
            f_02_015 TEXT,
            f_02_014 TEXT,

            -- Campos calculados/procesados
            es_valida BOOLEAN DEFAULT 1,
            razon_invalidez TEXT,
            factura_cumple_monto_minimo BOOLEAN DEFAULT 1,
            valor_total_factura REAL,  -- Suma de todas las líneas

            -- Transacciones (para el sistema)
            valor_transado REAL DEFAULT 0,
            cantidad_transada REAL DEFAULT 0,
            estado TEXT DEFAULT 'VALIDA',
            tiene_nota_credito BOOLEAN DEFAULT 0,
            nota_aplicada TEXT,  -- Descripción de la nota de crédito aplicada (NULL si no tiene)

            -- Auditoría
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Índice único por línea de factura
            UNIQUE(numero_factura, f_rowid)
        )
    ''')

    # 3. Crear índices para mejorar performance
    print("\n📊 Creando índices...")

    cursor.execute('''
        CREATE INDEX idx_facturas_numero
        ON facturas(numero_factura)
    ''')

    cursor.execute('''
        CREATE INDEX idx_facturas_cliente
        ON facturas(f_cliente_desp)
    ''')

    cursor.execute('''
        CREATE INDEX idx_facturas_fecha
        ON facturas(f_fecha)
    ''')

    cursor.execute('''
        CREATE INDEX idx_facturas_tipo_inv
        ON facturas(f_tipo_inv)
    ''')

    cursor.execute('''
        CREATE INDEX idx_facturas_valida
        ON facturas(es_valida)
    ''')

    cursor.execute('''
        CREATE INDEX idx_facturas_transado
        ON facturas(valor_transado)
    ''')

    conn.commit()
    conn.close()

    print("✅ Tabla creada con éxito")
    print("\n📊 ESTRUCTURA:")
    print("   - Campos del API SIESA: Todos los campos tal cual")
    print("   - Cada LÍNEA de factura: Un registro separado")
    print("   - Tipo de inventario: f_tipo_inv (sin espacios extras)")
    print("   - Índice único: (numero_factura, f_rowid)")
    print("="*70)

if __name__ == '__main__':
    recrear_tabla_facturas()
