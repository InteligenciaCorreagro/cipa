#!/usr/bin/env python3
"""
Script para limpiar notas de crédito con tipos de inventario inválidos

Este script identifica y elimina notas de crédito que tienen tipos de inventario
que están en la lista de exclusión (DESCESPEC, DESCUENTO, etc.)

Uso:
    python3 limpiar_notas_invalidas.py [--dry-run] [--tipos TIPO1,TIPO2,...]

Opciones:
    --dry-run: Solo muestra qué notas se eliminarían sin borrarlas
    --tipos: Lista de tipos a eliminar separados por coma (default: usa TIPOS_INVENTARIO_EXCLUIDOS)
"""

import sqlite3
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Importar tipos excluidos de business_rules
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from business_rules import BusinessRulesValidator


def conectar_bd():
    """Conecta a la base de datos"""
    db_path = Path(__file__).parent / 'data' / 'notas_credito.db'
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(str(db_path))


def buscar_notas_invalidas(conn, tipos_invalidos=None):
    """Busca notas con tipos de inventario inválidos"""
    cursor = conn.cursor()

    # Si no se especifican tipos, usar todos los excluidos
    if tipos_invalidos is None:
        validador = BusinessRulesValidator()
        tipos_invalidos = list(validador.TIPOS_INVENTARIO_EXCLUIDOS)

    print("\n" + "="*80)
    print("BUSCANDO NOTAS CON TIPOS DE INVENTARIO INVÁLIDOS")
    print("="*80)
    print(f"Tipos a buscar: {', '.join(sorted(tipos_invalidos))}\n")

    # Preparar consulta con placeholders
    placeholders = ','.join('?' * len(tipos_invalidos))

    # Buscar notas con tipos inválidos
    query = f'''
        SELECT id, numero_nota, nombre_producto, tipo_inventario, valor_total, estado, fecha_registro
        FROM notas_credito
        WHERE tipo_inventario IN ({placeholders})
        ORDER BY fecha_registro DESC
    '''

    cursor.execute(query, tipos_invalidos)
    notas_invalidas = cursor.fetchall()

    # También buscar notas con tipos NULL o vacíos que puedan contener DESCUENTO en el nombre
    cursor.execute('''
        SELECT id, numero_nota, nombre_producto, tipo_inventario, valor_total, estado, fecha_registro
        FROM notas_credito
        WHERE (tipo_inventario IS NULL OR tipo_inventario = '')
          AND (nombre_producto LIKE '%DESCUENTO%' OR nombre_producto LIKE '%DESCESPEC%')
        ORDER BY fecha_registro DESC
    ''')
    notas_sin_tipo = cursor.fetchall()

    resultados = {
        'con_tipo_invalido': notas_invalidas,
        'sin_tipo_sospechosas': notas_sin_tipo
    }

    # Mostrar resultados
    print(f"→ Notas con tipo de inventario inválido: {len(notas_invalidas)}")
    if notas_invalidas:
        print("\nPrimeras 10 notas con tipo inválido:")
        for i, nota in enumerate(notas_invalidas[:10], 1):
            id_nota, numero, nombre_prod, tipo_inv, valor, estado, fecha = nota
            print(f"  {i:2}. ID: {id_nota:4} | Nota: {numero:12} | Tipo: {tipo_inv:15} | "
                  f"Valor: {valor:12,.2f} | Estado: {estado}")
            print(f"      Producto: {nombre_prod[:70]}")

        if len(notas_invalidas) > 10:
            print(f"\n  ... y {len(notas_invalidas) - 10} notas más")

    print(f"\n→ Notas sin tipo con nombre sospechoso: {len(notas_sin_tipo)}")
    if notas_sin_tipo:
        print("\nPrimeras 10 notas sin tipo:")
        for i, nota in enumerate(notas_sin_tipo[:10], 1):
            id_nota, numero, nombre_prod, tipo_inv, valor, estado, fecha = nota
            print(f"  {i:2}. ID: {id_nota:4} | Nota: {numero:12} | Tipo: {tipo_inv or 'NULL':15} | "
                  f"Valor: {valor:12,.2f} | Estado: {estado}")
            print(f"      Producto: {nombre_prod[:70]}")

        if len(notas_sin_tipo) > 10:
            print(f"\n  ... y {len(notas_sin_tipo) - 10} notas más")

    # Estadísticas
    total_notas_invalidas = len(notas_invalidas) + len(notas_sin_tipo)

    if total_notas_invalidas > 0:
        cursor.execute(f'''
            SELECT SUM(valor_total)
            FROM notas_credito
            WHERE tipo_inventario IN ({placeholders})
        ''', tipos_invalidos)
        total_valor_con_tipo = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT SUM(valor_total)
            FROM notas_credito
            WHERE (tipo_inventario IS NULL OR tipo_inventario = '')
              AND (nombre_producto LIKE '%DESCUENTO%' OR nombre_producto LIKE '%DESCESPEC%')
        ''')
        total_valor_sin_tipo = cursor.fetchone()[0] or 0

        print("\n" + "="*80)
        print("ESTADÍSTICAS")
        print("="*80)
        print(f"Total notas inválidas: {total_notas_invalidas}")
        print(f"  - Con tipo inválido: {len(notas_invalidas):4} | Valor total: ${total_valor_con_tipo:,.2f}")
        print(f"  - Sin tipo (sospechosas): {len(notas_sin_tipo):4} | Valor total: ${total_valor_sin_tipo:,.2f}")
        print(f"Valor total a eliminar: ${total_valor_con_tipo + total_valor_sin_tipo:,.2f}")

    return resultados


def eliminar_notas(conn, resultados, dry_run=False):
    """Elimina las notas inválidas encontradas"""
    notas_con_tipo = resultados['con_tipo_invalido']
    notas_sin_tipo = resultados['sin_tipo_sospechosas']

    total_eliminar = len(notas_con_tipo) + len(notas_sin_tipo)

    if total_eliminar == 0:
        print("\n" + "="*80)
        print("✓ NO HAY NOTAS PARA ELIMINAR")
        print("="*80)
        return

    print("\n" + "="*80)
    if dry_run:
        print("MODO DRY-RUN: Las siguientes notas SERÍAN eliminadas:")
    else:
        print("ELIMINANDO NOTAS:")
    print("="*80)

    cursor = conn.cursor()
    total_eliminados = 0

    # Eliminar notas con tipo inválido
    if notas_con_tipo:
        ids_eliminar = [nota[0] for nota in notas_con_tipo]
        placeholders = ','.join('?' * len(ids_eliminar))

        if not dry_run:
            # Primero eliminar aplicaciones relacionadas
            cursor.execute(f'''
                DELETE FROM aplicaciones_notas
                WHERE id_nota IN ({placeholders})
            ''', ids_eliminar)

            aplicaciones_eliminadas = cursor.rowcount

            # Luego eliminar las notas
            cursor.execute(f'''
                DELETE FROM notas_credito
                WHERE id IN ({placeholders})
            ''', ids_eliminar)

            total_eliminados += cursor.rowcount
            print(f"{'[DRY-RUN] ' if dry_run else ''}Eliminadas {cursor.rowcount} notas con tipo inválido")
            if aplicaciones_eliminadas > 0:
                print(f"{'[DRY-RUN] ' if dry_run else ''}Eliminadas {aplicaciones_eliminadas} aplicaciones relacionadas")
        else:
            print(f"[DRY-RUN] Se eliminarían {len(notas_con_tipo)} notas con tipo inválido")

    # Eliminar notas sin tipo sospechosas
    if notas_sin_tipo:
        ids_eliminar = [nota[0] for nota in notas_sin_tipo]
        placeholders = ','.join('?' * len(ids_eliminar))

        if not dry_run:
            # Primero eliminar aplicaciones relacionadas
            cursor.execute(f'''
                DELETE FROM aplicaciones_notas
                WHERE id_nota IN ({placeholders})
            ''', ids_eliminar)

            aplicaciones_eliminadas = cursor.rowcount

            # Luego eliminar las notas
            cursor.execute(f'''
                DELETE FROM notas_credito
                WHERE id IN ({placeholders})
            ''', ids_eliminar)

            total_eliminados += cursor.rowcount
            print(f"{'[DRY-RUN] ' if dry_run else ''}Eliminadas {cursor.rowcount} notas sin tipo (sospechosas)")
            if aplicaciones_eliminadas > 0:
                print(f"{'[DRY-RUN] ' if dry_run else ''}Eliminadas {aplicaciones_eliminadas} aplicaciones relacionadas")
        else:
            print(f"[DRY-RUN] Se eliminarían {len(notas_sin_tipo)} notas sin tipo (sospechosas)")

    if not dry_run:
        conn.commit()
        print(f"\n✓ Total de notas eliminadas: {total_eliminados}")
        print(f"✓ Cambios guardados en la base de datos")
    else:
        print(f"\n[DRY-RUN] Se eliminarían aproximadamente {total_eliminar} notas")


def generar_reporte(resultados):
    """Genera un reporte de la limpieza"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reporte_path = Path(__file__).parent / f'reporte_limpieza_notas_{timestamp}.txt'

    notas_con_tipo = resultados['con_tipo_invalido']
    notas_sin_tipo = resultados['sin_tipo_sospechosas']
    total = len(notas_con_tipo) + len(notas_sin_tipo)

    with open(reporte_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("REPORTE DE LIMPIEZA DE NOTAS CON TIPOS INVÁLIDOS\n")
        f.write("="*80 + "\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if total == 0:
            f.write("✓ NO SE ENCONTRARON NOTAS INVÁLIDAS\n")
        else:
            f.write(f"RESUMEN: {total} notas inválidas encontradas\n")
            f.write("-"*80 + "\n\n")

            if notas_con_tipo:
                f.write(f"Notas con tipo inválido: {len(notas_con_tipo)}\n")
                for nota in notas_con_tipo:
                    id_nota, numero, nombre_prod, tipo_inv, valor, estado, fecha = nota
                    f.write(f"  - ID: {id_nota} | Nota: {numero} | Tipo: {tipo_inv} | "
                           f"Valor: ${valor:,.2f} | Estado: {estado}\n")
                    f.write(f"    Producto: {nombre_prod}\n")
                f.write("\n")

            if notas_sin_tipo:
                f.write(f"Notas sin tipo (sospechosas): {len(notas_sin_tipo)}\n")
                for nota in notas_sin_tipo:
                    id_nota, numero, nombre_prod, tipo_inv, valor, estado, fecha = nota
                    f.write(f"  - ID: {id_nota} | Nota: {numero} | Tipo: {tipo_inv or 'NULL'} | "
                           f"Valor: ${valor:,.2f} | Estado: {estado}\n")
                    f.write(f"    Producto: {nombre_prod}\n")

    print(f"\n✓ Reporte guardado en: {reporte_path}")
    return reporte_path


def main():
    parser = argparse.ArgumentParser(
        description='Limpia notas de crédito con tipos de inventario inválidos'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo muestra qué notas se eliminarían sin borrarlas'
    )
    parser.add_argument(
        '--tipos',
        type=str,
        help='Lista de tipos a eliminar separados por coma (default: usa TIPOS_INVENTARIO_EXCLUIDOS)'
    )

    args = parser.parse_args()

    tipos_invalidos = None
    if args.tipos:
        tipos_invalidos = [t.strip().upper() for t in args.tipos.split(',')]

    print("="*80)
    print("SCRIPT DE LIMPIEZA DE NOTAS CON TIPOS INVÁLIDOS")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo: {'DRY-RUN (sin cambios)' if args.dry_run else 'EJECUCIÓN REAL'}")

    try:
        # Conectar a la base de datos
        conn = conectar_bd()

        # Buscar notas inválidas
        resultados = buscar_notas_invalidas(conn, tipos_invalidos)

        # Eliminar notas (o mostrar qué se eliminaría)
        eliminar_notas(conn, resultados, dry_run=args.dry_run)

        # Generar reporte
        generar_reporte(resultados)

        # Cerrar conexión
        conn.close()

        print("\n" + "="*80)
        print("✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
