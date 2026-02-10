#!/usr/bin/env python3
"""
Test de Verificación de Aplicación de Notas - BASE DE DATOS REAL
=================================================================

Este script analiza la base de datos real y verifica qué notas de crédito
deberían aplicarse a facturas y cuáles no, explicando las razones.

REGLAS DE APLICACIÓN:
1. Cantidad nota <= Cantidad factura
2. Valor nota <= Valor factura
3. Mismo cliente (NIT)
4. Mismo producto (código)

Si TODAS las condiciones se cumplen → La nota SE PUEDE APLICAR
Si ALGUNA condición falla → La nota NO SE PUEDE APLICAR
"""

import sys
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple

# Agregar el directorio core al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from notas_credito_manager import NotasCreditoManager


class TestAplicacionNotasBaseDatos:
    """Clase para probar la aplicación de notas con datos reales de la BD"""

    def __init__(self, db_path='./data/notas_credito.db'):
        """
        Inicializa el test con la base de datos real

        Args:
            db_path: Ruta a la base de datos real
        """
        if not os.path.exists(db_path):
            print(f"❌ ERROR: No se encontró la base de datos en {db_path}")
            sys.exit(1)

        self.db_path = db_path
        self.manager = NotasCreditoManager(db_path=db_path)
        self.resultados = {
            'puede_aplicarse': [],
            'no_puede_aplicarse': [],
            'ya_aplicadas': []
        }

    def obtener_notas_pendientes(self) -> List[Dict]:
        """Obtiene todas las notas de crédito en estado PENDIENTE"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM notas_credito
                WHERE estado IN ('PENDIENTE', 'PARCIAL')
                AND saldo_pendiente != 0
                ORDER BY fecha_nota ASC, numero_nota ASC
            ''')

            notas = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return notas

        except Exception as e:
            print(f"❌ Error al obtener notas pendientes: {e}")
            return []

    def obtener_facturas_sin_nota(self) -> List[Dict]:
        """Obtiene facturas que no tienen nota aplicada"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM facturas
                WHERE nota_aplicada = 0
                AND cantidad_restante > 0
                AND valor_restante > 0
                ORDER BY fecha_factura DESC, numero_factura ASC
            ''')

            facturas = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return facturas

        except Exception as e:
            print(f"❌ Error al obtener facturas: {e}")
            return []

    def obtener_estadisticas_bd(self) -> Dict:
        """Obtiene estadísticas generales de la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Notas por estado
            cursor.execute('SELECT estado, COUNT(*), SUM(saldo_pendiente) FROM notas_credito GROUP BY estado')
            notas_por_estado = {row[0]: {'count': row[1], 'saldo': row[2] or 0} for row in cursor.fetchall()}

            # Facturas
            cursor.execute('SELECT COUNT(*), SUM(valor_restante) FROM facturas WHERE nota_aplicada = 0')
            facturas_sin_nota = cursor.fetchone()

            cursor.execute('SELECT COUNT(*), SUM(descuento_valor) FROM facturas WHERE nota_aplicada = 1')
            facturas_con_nota = cursor.fetchone()

            conn.close()

            return {
                'notas_por_estado': notas_por_estado,
                'facturas_sin_nota': {'count': facturas_sin_nota[0] or 0, 'valor': facturas_sin_nota[1] or 0},
                'facturas_con_nota': {'count': facturas_con_nota[0] or 0, 'descuento': facturas_con_nota[1] or 0}
            }

        except Exception as e:
            print(f"❌ Error al obtener estadísticas: {e}")
            return {}

    def analizar_compatibilidad(self, nota: Dict, factura: Dict) -> Tuple[bool, str, Dict]:
        """
        Analiza si una nota puede aplicarse a una factura

        Returns:
            Tupla con (puede_aplicarse, razon, detalles)
        """
        detalles = {
            'cliente_ok': False,
            'producto_ok': False,
            'cantidad_ok': False,
            'valor_ok': False
        }

        # Verificar cliente
        if nota['nit_cliente'] != factura['nit_cliente']:
            return False, f"Cliente diferente (Nota: {nota['nit_cliente']}, Factura: {factura['nit_cliente']})", detalles
        detalles['cliente_ok'] = True

        # Verificar producto
        if nota['codigo_producto'] != factura['codigo_producto']:
            return False, f"Producto diferente (Nota: {nota['codigo_producto'][:30]}..., Factura: {factura['codigo_producto'][:30]}...)", detalles
        detalles['producto_ok'] = True

        # Verificar cantidad
        cantidad_nota = abs(nota['cantidad_pendiente'])
        cantidad_factura = abs(factura['cantidad_restante'])
        detalles['cantidad_nota'] = cantidad_nota
        detalles['cantidad_factura'] = cantidad_factura

        if cantidad_nota > cantidad_factura:
            return False, f"Cantidad excede (Nota: {cantidad_nota} > Factura: {cantidad_factura})", detalles
        detalles['cantidad_ok'] = True

        # Verificar valor
        valor_nota = abs(nota['saldo_pendiente'])
        valor_factura = abs(factura['valor_restante'])
        detalles['valor_nota'] = valor_nota
        detalles['valor_factura'] = valor_factura

        if valor_nota > valor_factura:
            return False, f"Valor excede (Nota: ${valor_nota:,.2f} > Factura: ${valor_factura:,.2f})", detalles
        detalles['valor_ok'] = True

        # Si llegamos aquí, todas las condiciones se cumplen
        return True, "Todas las condiciones se cumplen - Puede aplicarse", detalles

    def analizar_todas_las_combinaciones(self):
        """Analiza todas las combinaciones posibles de notas y facturas"""

        print("\n" + "="*80)
        print("ANÁLISIS DE APLICACIÓN DE NOTAS - BASE DE DATOS REAL")
        print("="*80)

        # Obtener datos
        print("\n🔍 Cargando datos de la base de datos...")
        notas = self.obtener_notas_pendientes()
        facturas = self.obtener_facturas_sin_nota()
        estadisticas = self.obtener_estadisticas_bd()

        print(f"\n📊 ESTADO DE LA BASE DE DATOS:")
        print(f"   • Notas pendientes/parciales: {len(notas)}")
        if estadisticas.get('notas_por_estado'):
            for estado, datos in estadisticas['notas_por_estado'].items():
                print(f"     - {estado}: {datos['count']} notas (Saldo: ${datos['saldo']:,.2f})")
        print(f"   • Facturas sin nota: {estadisticas['facturas_sin_nota']['count']} (Valor: ${estadisticas['facturas_sin_nota']['valor']:,.2f})")
        print(f"   • Facturas con nota: {estadisticas['facturas_con_nota']['count']} (Descuento: ${estadisticas['facturas_con_nota']['descuento']:,.2f})")

        if len(notas) == 0:
            print("\n✅ No hay notas pendientes para procesar")
            return True

        if len(facturas) == 0:
            print("\n⚠️  No hay facturas disponibles sin nota aplicada")
            return True

        print(f"\n🔄 Analizando {len(notas)} notas contra {len(facturas)} facturas...")
        print("="*80)

        # Analizar cada nota
        for idx_nota, nota in enumerate(notas, 1):
            print(f"\n{'─'*80}")
            print(f"📋 NOTA {idx_nota}/{len(notas)}: {nota['numero_nota']}")
            print(f"{'─'*80}")
            print(f"   • Cliente: {nota['nit_cliente']} - {nota['nombre_cliente'][:40]}")
            print(f"   • Producto: {nota['codigo_producto'][:50]}")
            print(f"   • Cantidad pendiente: {nota['cantidad_pendiente']}")
            print(f"   • Saldo pendiente: ${nota['saldo_pendiente']:,.2f}")
            print(f"   • Estado: {nota['estado']}")
            print(f"   • Fecha: {nota['fecha_nota']}")

            # Buscar facturas compatibles
            facturas_compatibles = []
            facturas_incompatibles = []

            for factura in facturas:
                puede_aplicarse, razon, detalles = self.analizar_compatibilidad(nota, factura)

                if detalles['cliente_ok'] and detalles['producto_ok']:
                    # Solo considerar si cliente y producto coinciden
                    if puede_aplicarse:
                        facturas_compatibles.append({
                            'factura': factura,
                            'razon': razon,
                            'detalles': detalles
                        })
                    else:
                        facturas_incompatibles.append({
                            'factura': factura,
                            'razon': razon,
                            'detalles': detalles
                        })

            # Mostrar resultados
            total_candidatas = len(facturas_compatibles) + len(facturas_incompatibles)

            if total_candidatas == 0:
                print(f"\n   ❌ NO SE ENCONTRARON FACTURAS del mismo cliente y producto")
                self.resultados['no_puede_aplicarse'].append({
                    'nota': nota,
                    'razon': 'No hay facturas del mismo cliente y producto'
                })
            else:
                print(f"\n   🔍 Facturas del mismo cliente y producto: {total_candidatas}")

                if facturas_compatibles:
                    print(f"\n   ✅ PUEDE APLICARSE a {len(facturas_compatibles)} factura(s):")
                    for i, item in enumerate(facturas_compatibles[:5], 1):  # Mostrar máximo 5
                        f = item['factura']
                        d = item['detalles']
                        print(f"\n      {i}. Factura: {f['numero_factura']} (Línea {f['numero_linea']})")
                        print(f"         • Cantidad disponible: {d['cantidad_factura']} (nota usa {d['cantidad_nota']})")
                        print(f"         • Valor disponible: ${d['valor_factura']:,.2f} (nota usa ${d['valor_nota']:,.2f})")
                        print(f"         • Fecha: {f['fecha_factura']}")
                        print(f"         ✅ {item['razon']}")

                    if len(facturas_compatibles) > 5:
                        print(f"\n      ... y {len(facturas_compatibles) - 5} factura(s) más")

                    self.resultados['puede_aplicarse'].append({
                        'nota': nota,
                        'facturas_compatibles': facturas_compatibles,
                        'total': len(facturas_compatibles)
                    })
                else:
                    print(f"\n   ❌ NO PUEDE APLICARSE a ninguna factura")

                if facturas_incompatibles:
                    print(f"\n   ❌ NO puede aplicarse a {len(facturas_incompatibles)} factura(s) por:")
                    razones_agrupadas = {}
                    for item in facturas_incompatibles:
                        razon = item['razon'].split('(')[0].strip()  # Agrupar por tipo de razón
                        if razon not in razones_agrupadas:
                            razones_agrupadas[razon] = []
                        razones_agrupadas[razon].append(item)

                    for razon, items in razones_agrupadas.items():
                        print(f"\n      • {razon}: {len(items)} factura(s)")
                        # Mostrar primera como ejemplo
                        ejemplo = items[0]
                        f = ejemplo['factura']
                        print(f"        Ejemplo: Factura {f['numero_factura']}")
                        print(f"        Razón completa: {ejemplo['razon']}")

                    self.resultados['no_puede_aplicarse'].append({
                        'nota': nota,
                        'facturas_incompatibles': facturas_incompatibles,
                        'razones': razones_agrupadas
                    })

        # Resumen final
        self.mostrar_resumen_final()
        return True

    def mostrar_resumen_final(self):
        """Muestra el resumen final del análisis"""

        print(f"\n\n{'='*80}")
        print("RESUMEN FINAL DEL ANÁLISIS")
        print(f"{'='*80}\n")

        puede_aplicarse = len(self.resultados['puede_aplicarse'])
        no_puede_aplicarse = len(self.resultados['no_puede_aplicarse'])
        total = puede_aplicarse + no_puede_aplicarse

        print(f"📊 RESUMEN DE NOTAS ANALIZADAS:")
        print(f"   • Total de notas analizadas: {total}")
        print(f"   • ✅ Pueden aplicarse: {puede_aplicarse} ({puede_aplicarse/total*100 if total > 0 else 0:.1f}%)")
        print(f"   • ❌ No pueden aplicarse: {no_puede_aplicarse} ({no_puede_aplicarse/total*100 if total > 0 else 0:.1f}%)")

        if puede_aplicarse > 0:
            print(f"\n✅ NOTAS QUE PUEDEN APLICARSE:")
            total_facturas_disponibles = 0
            valor_total_aplicable = 0

            for item in self.resultados['puede_aplicarse']:
                nota = item['nota']
                total_facturas_disponibles += item['total']
                valor_total_aplicable += nota['saldo_pendiente']
                print(f"\n   📋 {nota['numero_nota']}")
                print(f"      • Valor: ${nota['saldo_pendiente']:,.2f}")
                print(f"      • Puede aplicarse a: {item['total']} factura(s)")
                print(f"      • Cliente: {nota['nit_cliente']} - {nota['nombre_cliente'][:40]}")
                print(f"      • Producto: {nota['codigo_producto'][:50]}")

            print(f"\n   💰 Total aplicable: ${valor_total_aplicable:,.2f}")
            print(f"   📄 Total de facturas candidatas: {total_facturas_disponibles}")

        if no_puede_aplicarse > 0:
            print(f"\n❌ NOTAS QUE NO PUEDEN APLICARSE:")
            valor_total_bloqueado = 0
            razones_comunes = {}

            for item in self.resultados['no_puede_aplicarse']:
                nota = item['nota']
                valor_total_bloqueado += nota['saldo_pendiente']
                razon_principal = item.get('razon', 'Múltiples razones')

                if 'razones' in item:
                    for razon in item['razones'].keys():
                        razones_comunes[razon] = razones_comunes.get(razon, 0) + 1

                print(f"\n   📋 {nota['numero_nota']}")
                print(f"      • Valor: ${nota['saldo_pendiente']:,.2f}")
                print(f"      • Razón: {razon_principal}")
                print(f"      • Cliente: {nota['nit_cliente']} - {nota['nombre_cliente'][:40]}")
                print(f"      • Producto: {nota['codigo_producto'][:50]}")

            print(f"\n   💰 Total bloqueado: ${valor_total_bloqueado:,.2f}")

            if razones_comunes:
                print(f"\n   📊 Razones más comunes:")
                for razon, count in sorted(razones_comunes.items(), key=lambda x: x[1], reverse=True):
                    print(f"      • {razon}: {count} nota(s)")

        print(f"\n{'='*80}")
        print("\n💡 EXPLICACIÓN DE POR QUÉ SE APLICA O NO:")
        print("""
   Una nota SE APLICA a una factura cuando:
   1. ✅ Cliente (NIT) es el mismo
   2. ✅ Producto (código) es el mismo
   3. ✅ Cantidad de la nota ≤ Cantidad disponible en factura
   4. ✅ Valor de la nota ≤ Valor disponible en factura

   Una nota NO SE APLICA cuando:
   1. ❌ Cliente o producto no coinciden
   2. ❌ Cantidad de la nota > Cantidad disponible en factura
   3. ❌ Valor de la nota > Valor disponible en factura
   4. ❌ No hay facturas disponibles del mismo cliente y producto
        """)
        print(f"{'='*80}\n")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Test de aplicación de notas con base de datos real')
    parser.add_argument('--db', default='./data/notas_credito.db', help='Ruta a la base de datos')
    args = parser.parse_args()

    test = TestAplicacionNotasBaseDatos(db_path=args.db)

    try:
        test.analizar_todas_las_combinaciones()
        print("✅ Análisis completado exitosamente\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR durante el análisis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
