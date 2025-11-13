#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos
"""
import sqlite3
import sys
from pathlib import Path

# Agregar el directorio backend al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

def check_database(db_path='./data/notas_credito.db'):
    """Verifica el estado de la base de datos"""
    print(f"\n{'='*60}")
    print(f"📊 Estado de la Base de Datos: {db_path}")
    print(f"{'='*60}\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [t[0] for t in cursor.fetchall()]
        print(f"📋 Tablas existentes: {len(tablas)}")
        for tabla in tablas:
            print(f"  - {tabla}")

        print(f"\n{'='*60}")
        print("📈 Conteo de Registros:")
        print(f"{'='*60}\n")

        # Contar notas de crédito
        if 'notas_credito' in tablas:
            cursor.execute("SELECT COUNT(*) FROM notas_credito")
            total_notas = cursor.fetchone()[0]
            print(f"  Notas de crédito totales: {total_notas}")

            if total_notas > 0:
                cursor.execute("SELECT estado, COUNT(*) FROM notas_credito GROUP BY estado")
                print(f"  Por estado:")
                for estado, cantidad in cursor.fetchall():
                    print(f"    {estado}: {cantidad}")

                cursor.execute("""
                    SELECT numero_nota, fecha_nota, nombre_cliente, estado,
                           valor_total, saldo_pendiente
                    FROM notas_credito
                    ORDER BY fecha_nota DESC
                    LIMIT 5
                """)
                print(f"\n  Últimas 5 notas:")
                for row in cursor.fetchall():
                    print(f"    {row[0]} | {row[1]} | {row[2][:30]} | {row[3]} | ${row[4]:,.0f} (saldo: ${row[5]:,.0f})")

        # Contar aplicaciones
        if 'aplicaciones_notas' in tablas or 'aplicaciones_notas_credito' in tablas:
            tabla_app = 'aplicaciones_notas' if 'aplicaciones_notas' in tablas else 'aplicaciones_notas_credito'
            cursor.execute(f"SELECT COUNT(*) FROM {tabla_app}")
            total_aplicaciones = cursor.fetchone()[0]
            print(f"\n  Aplicaciones de notas: {total_aplicaciones}")

        # Contar usuarios
        if 'usuarios' in tablas:
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]
            print(f"\n  Usuarios registrados: {total_usuarios}")

            if total_usuarios > 0:
                cursor.execute("SELECT username, rol FROM usuarios")
                print(f"  Usuarios:")
                for username, rol in cursor.fetchall():
                    print(f"    - {username} ({rol})")

        # Contar facturas rechazadas
        if 'facturas_rechazadas' in tablas:
            cursor.execute("SELECT COUNT(*) FROM facturas_rechazadas")
            total_rechazadas = cursor.fetchone()[0]
            print(f"\n  Facturas rechazadas: {total_rechazadas}")

            if total_rechazadas > 0:
                cursor.execute("""
                    SELECT DATE(fecha_proceso) as fecha, COUNT(*) as cantidad
                    FROM facturas_rechazadas
                    GROUP BY DATE(fecha_proceso)
                    ORDER BY fecha DESC
                    LIMIT 10
                """)
                print(f"\n  Facturas rechazadas por fecha (últimos 10 días):")
                for fecha, cantidad in cursor.fetchall():
                    print(f"    {fecha}: {cantidad} facturas")

        # Tipos de inventario detectados
        if 'tipos_inventario_detectados' in tablas:
            cursor.execute("SELECT COUNT(*) FROM tipos_inventario_detectados")
            total_tipos = cursor.fetchone()[0]
            print(f"\n  Tipos de inventario detectados: {total_tipos}")

        conn.close()

        print(f"\n{'='*60}\n")

        return {
            'notas': total_notas if 'notas_credito' in tablas else 0,
            'usuarios': total_usuarios if 'usuarios' in tablas else 0,
            'rechazadas': total_rechazadas if 'facturas_rechazadas' in tablas else 0
        }

    except sqlite3.Error as e:
        print(f"❌ Error al acceder a la base de datos: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    import os
    os.chdir('/home/user/cipa')
    check_database()
