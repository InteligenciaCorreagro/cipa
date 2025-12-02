#!/usr/bin/env python3
"""
Script para limpiar la base de datos dejando solo registros de una fecha exacta.
Por defecto conserva únicamente el día 2025-12-01 y elimina todo lo demás.
"""

import os
import sqlite3
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def limpiar_bd_por_fecha(db_path: str, fecha_objetivo: str = "2025-12-01"):
    """
    Deja en la base únicamente los registros de la fecha objetivo.

    Args:
        db_path: Ruta de la base de datos SQLite.
        fecha_objetivo: Fecha a conservar en formato YYYY-MM-DD.
    """
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info(f"Conectado a base de datos: {db_path}")
        logger.info(f"Fecha a conservar: {fecha_objetivo}")
        logger.info("=" * 60)

        # ===== CONTAR REGISTROS ANTES DE LIMPIAR =====
        cursor.execute("SELECT COUNT(*) FROM notas_credito")
        notas_antes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facturas")
        facturas_antes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facturas_rechazadas")
        rechazadas_antes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM aplicaciones_notas")
        aplicaciones_antes = cursor.fetchone()[0]

        logger.info("Registros ANTES de limpiar:")
        logger.info(f"  - Notas crédito: {notas_antes}")
        logger.info(f"  - Facturas: {facturas_antes}")
        logger.info(f"  - Facturas rechazadas: {rechazadas_antes}")
        logger.info(f"  - Aplicaciones notas: {aplicaciones_antes}")
        logger.info("=" * 60)

        # ===== LISTAR REGISTROS QUE SE ELIMINARÁN =====
        logger.info("\n📋 REGISTROS A ELIMINAR (todas las fechas diferentes a la objetivo):\n")

        cursor.execute(
            """
            SELECT numero_nota, fecha_nota, valor_total
            FROM notas_credito
            WHERE fecha_nota <> ?
            ORDER BY fecha_nota DESC
            """,
            (fecha_objetivo,),
        )
        notas_eliminar = cursor.fetchall()
        if notas_eliminar:
            logger.info("Notas crédito a eliminar:")
            for nota_num, fecha, valor in notas_eliminar[:20]:  # Mostrar primeras 20
                logger.info(f"  - {nota_num} ({fecha}): ${valor:,.2f}")
            if len(notas_eliminar) > 20:
                logger.info(f"  ... y {len(notas_eliminar) - 20} más")

        cursor.execute(
            """
            SELECT numero_factura, fecha_factura, valor_total
            FROM facturas
            WHERE fecha_factura <> ?
            ORDER BY fecha_factura DESC
            """,
            (fecha_objetivo,),
        )
        facturas_eliminar = cursor.fetchall()
        if facturas_eliminar:
            logger.info("\nFacturas a eliminar:")
            for fact_num, fecha, valor in facturas_eliminar[:20]:  # Mostrar primeras 20
                logger.info(f"  - {fact_num} ({fecha}): ${valor:,.2f}")
            if len(facturas_eliminar) > 20:
                logger.info(f"  ... y {len(facturas_eliminar) - 20} más")

        logger.info("\n" + "=" * 60)

        # Pedir confirmación
        print("\n⚠️  ADVERTENCIA: Esta operación eliminará:")
        print(f"   - {len(notas_eliminar)} notas crédito")
        print(f"   - {len(facturas_eliminar)} facturas")
        print(f"   - Todos los registros que NO sean de la fecha {fecha_objetivo}")
        respuesta = input("\n¿Desea continuar? (escriba 'SI' para confirmar): ").strip().upper()

        if respuesta != "SI":
            logger.warning("Operación cancelada por el usuario")
            conn.close()
            return False

        logger.info("\n" + "=" * 60)
        logger.info("🧹  Iniciando limpieza de base de datos...\n")

        # ===== ELIMINAR REGISTROS =====

        # 1. Eliminar aplicaciones de notas que no sean de la fecha objetivo
        cursor.execute(
            """
            DELETE FROM aplicaciones_notas
            WHERE id_nota IN (
                SELECT id FROM notas_credito WHERE fecha_nota <> ?
            )
            """,
            (fecha_objetivo,),
        )
        apps_eliminadas = cursor.rowcount
        logger.info(f"✅ Aplicaciones de notas eliminadas: {apps_eliminadas}")

        # 2. Eliminar notas crédito que no sean de la fecha objetivo
        cursor.execute(
            """
            DELETE FROM notas_credito
            WHERE fecha_nota <> ?
            """,
            (fecha_objetivo,),
        )
        notas_eliminadas = cursor.rowcount
        logger.info(f"✅ Notas crédito eliminadas: {notas_eliminadas}")

        # 3. Eliminar facturas que no sean de la fecha objetivo
        cursor.execute(
            """
            DELETE FROM facturas
            WHERE fecha_factura <> ?
            """,
            (fecha_objetivo,),
        )
        facturas_eliminadas = cursor.rowcount
        logger.info(f"✅ Facturas eliminadas: {facturas_eliminadas}")

        # 4. Eliminar facturas rechazadas que no sean de la fecha objetivo
        cursor.execute(
            """
            DELETE FROM facturas_rechazadas
            WHERE fecha_factura <> ?
            """,
            (fecha_objetivo,),
        )
        rechazadas_eliminadas = cursor.rowcount
        logger.info(f"✅ Facturas rechazadas eliminadas: {rechazadas_eliminadas}")

        # Commit de cambios
        conn.commit()

        # ===== CONTAR REGISTROS DESPUÉS DE LIMPIAR =====
        logger.info("\n" + "=" * 60)
        logger.info("📊 VERIFICACIÓN FINAL:\n")

        cursor.execute("SELECT COUNT(*) FROM notas_credito")
        notas_despues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facturas")
        facturas_despues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facturas_rechazadas")
        rechazadas_despues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM aplicaciones_notas")
        aplicaciones_despues = cursor.fetchone()[0]

        logger.info("Registros DESPUÉS de limpiar:")
        logger.info(f"  - Notas crédito: {notas_antes} → {notas_despues} (-{notas_antes - notas_despues})")
        logger.info(f"  - Facturas: {facturas_antes} → {facturas_despues} (-{facturas_antes - facturas_despues})")
        logger.info(f"  - Facturas rechazadas: {rechazadas_antes} → {rechazadas_despues} (-{rechazadas_antes - rechazadas_despues})")
        logger.info(f"  - Aplicaciones notas: {aplicaciones_antes} → {aplicaciones_despues} (-{aplicaciones_antes - aplicaciones_despues})")

        logger.info("\n" + "=" * 60)
        logger.info("✅ ¡Base de datos limpiada exitosamente!")
        logger.info("=" * 60)

        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"Error en la base de datos: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return False


if __name__ == "__main__":
    # Obtener ruta de la BD
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    db_path = str(project_root / "data" / "notas_credito.db")

    # Ejecutar limpieza
    limpiar_bd_por_fecha(db_path)
