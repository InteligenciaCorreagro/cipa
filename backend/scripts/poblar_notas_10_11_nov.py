#!/usr/bin/env python3
"""
Script para poblar notas de crédito del 10-11 de NOVIEMBRE 2025 desde API SIESA

IMPORTANTE:
- Extrae notas de crédito (prefijo empieza con 'N')
- Guarda en tabla notas_credito
- Cada LÍNEA de nota es un registro separado
"""
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Agregar backend al path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.api_client import SiesaAPIClient

DB_PATH = BACKEND_DIR / 'data' / 'notas_credito.db'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def es_nota_credito(documento):
    """Verifica si es nota de crédito (prefijo empieza con N)"""
    prefijo = str(documento.get('f_prefijo', '')).strip().upper()
    return prefijo.startswith('N')


def guardar_nota_credito(documento, conn):
    """Guarda una nota de crédito en la base de datos"""
    cursor = conn.cursor()

    # Extraer datos del documento
    prefijo = str(documento.get('f_prefijo', '')).strip()
    nrodocto = str(documento.get('f_nrodocto', '')).strip()
    numero_nota = f"{prefijo}{nrodocto}"

    fecha_nota = documento.get('f_fecha')
    nit_cliente = documento.get('f_cliente_desp')
    nombre_cliente = documento.get('f_cliente_fact_razon_soc')
    codigo_producto = documento.get('f_cod_item')
    nombre_producto = documento.get('f_desc_item')
    tipo_inventario = str(documento.get('f_tipo_inv', '')).strip().upper()

    # Valores (notas de crédito suelen tener valores negativos, usamos absoluto)
    valor_total = abs(float(documento.get('f_valor_subtotal_local', 0) or 0))
    cantidad = abs(float(documento.get('f_cant_base', 0) or 0))

    causal_devolucion = documento.get('f_notas_causal_dev')

    try:
        cursor.execute('''
            INSERT INTO notas_credito (
                numero_nota,
                fecha_nota,
                nit_cliente,
                nombre_cliente,
                codigo_producto,
                nombre_producto,
                tipo_inventario,
                valor_total,
                cantidad,
                saldo_pendiente,
                cantidad_pendiente,
                causal_devolucion,
                estado,
                fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE', ?)
        ''', (
            numero_nota,
            fecha_nota,
            nit_cliente,
            nombre_cliente,
            codigo_producto,
            nombre_producto,
            tipo_inventario,
            valor_total,
            cantidad,
            valor_total,  # saldo_pendiente inicialmente igual a valor_total
            cantidad,  # cantidad_pendiente inicialmente igual a cantidad
            causal_devolucion,
            datetime.now().isoformat()
        ))
        return True
    except sqlite3.IntegrityError:
        # Ya existe esta combinación de nota + producto
        logger.debug(f"Nota {numero_nota} - {codigo_producto} ya existe")
        return False
    except Exception as e:
        logger.error(f"Error guardando nota {numero_nota}: {e}")
        return False


def poblar_notas_10_11_nov():
    """Pobla notas de crédito del 10 y 11 de noviembre 2025"""
    load_dotenv()

    CONNI_KEY = os.getenv('CONNI_KEY')
    CONNI_TOKEN = os.getenv('CONNI_TOKEN')

    if not all([CONNI_KEY, CONNI_TOKEN]):
        logger.error("❌ Faltan credenciales del API (CONNI_KEY, CONNI_TOKEN)")
        logger.info("💡 Configura el archivo .env con las credenciales")
        return

    print("\n" + "="*70)
    print("POBLACIÓN DE NOTAS DE CRÉDITO - 10 y 11 de NOVIEMBRE 2025")
    print("="*70)

    api_client = SiesaAPIClient(CONNI_KEY, CONNI_TOKEN)
    conn = sqlite3.connect(str(DB_PATH))

    # Procesar del 10 y 11 de noviembre
    fechas = [
        datetime(2025, 11, 10),
        datetime(2025, 11, 11)
    ]

    total_notas = 0
    total_guardadas = 0
    dias_procesados = 0

    for fecha_actual in fechas:
        fecha_str = fecha_actual.strftime('%Y-%m-%d')

        print(f"\n{'='*70}")
        print(f"📅 {fecha_str}")
        print(f"{'='*70}")

        try:
            # Obtener del API
            documentos = api_client.obtener_facturas(fecha_actual)

            if not documentos:
                print(f"ℹ️  Sin documentos")
                continue

            # Filtrar solo notas de crédito (prefijo empieza con 'N')
            notas = [doc for doc in documentos if es_nota_credito(doc)]

            if not notas:
                print(f"ℹ️  Sin notas de crédito")
                continue

            print(f"✅ Encontradas {len(notas)} notas de crédito")

            # Guardar notas
            guardadas = 0
            for nota in notas:
                if guardar_nota_credito(nota, conn):
                    guardadas += 1

            conn.commit()

            print(f"💾 Guardadas: {guardadas} notas")

            total_notas += len(notas)
            total_guardadas += guardadas
            dias_procesados += 1

        except Exception as e:
            logger.error(f"❌ Error en {fecha_str}: {e}")
            import traceback
            traceback.print_exc()

    conn.close()

    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN FINAL - NOTAS DE CRÉDITO")
    print(f"{'='*70}")
    print(f"✅ Días procesados: {dias_procesados}/2")
    print(f"📊 Total notas encontradas: {total_notas}")
    print(f"📊 Total notas guardadas: {total_guardadas}")
    print(f"📊 Total duplicadas/existentes: {total_notas - total_guardadas}")
    print(f"{'='*70}")
    print("\n✅ Proceso completado")


if __name__ == '__main__':
    poblar_notas_10_11_nov()
