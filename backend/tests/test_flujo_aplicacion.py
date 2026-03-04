import os
import sys
import tempfile
import unittest
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.notas_credito_manager import NotasCreditoManager


class TestFlujoAplicacion(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.manager = NotasCreditoManager(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_aplicar_nota_elimina_linea(self):
        factura = {
            'numero_factura': 'F001',
            'codigo_factura': 'F001',
            'fecha_factura': '2024-01-10',
            'nit_cliente': '900100200',
            'nombre_cliente': 'Cliente Demo',
            'codigo_producto': 'P001',
            'nombre_producto': 'Producto',
            'cantidad_original': 10,
            'valor_total': 600000,
            'indice_linea': 0
        }
        self.assertTrue(self.manager.registrar_factura(factura))

        nota = {
            'numero_nota': 'NC001',
            'fecha_nota': '2024-01-11',
            'nit_cliente': '900100200',
            'nombre_cliente': 'Cliente Demo',
            'codigo_producto': 'P001',
            'nombre_producto': 'Producto',
            'cantidad': 10,
            'valor_total': 600000,
            'es_agente': 'AGENTE'
        }
        self.assertTrue(self.manager.registrar_nota_credito(nota))

        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notas_credito WHERE numero_nota = ?', ('NC001',))
        nota_db = dict(cursor.fetchone())
        cursor.execute('SELECT * FROM facturas WHERE numero_factura = ?', ('F001',))
        factura_db = dict(cursor.fetchone())
        conn.close()

        factura_payload = {
            'numero_factura': factura_db['numero_factura'],
            'f_cliente_desp': factura_db['nit_encrypted'],
            'f_cod_item': factura_db['codigo_producto'],
            'f_cant_base': factura_db['cantidad_restante'],
            'f_valor_subtotal_local': factura_db['valor_restante'],
            'f_fecha': factura_db['fecha_factura'],
            '_indice_linea': factura_db['indice_linea']
        }

        resultado = self.manager.aplicar_nota_a_factura(nota_db, factura_payload)
        self.assertIsNotNone(resultado)

        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM facturas WHERE numero_factura = ?', ('F001',))
        restantes = cursor.fetchone()[0]
        cursor.execute('SELECT estado FROM notas_credito WHERE numero_nota = ?', ('NC001',))
        estado = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(restantes, 0)
        self.assertEqual(estado, 'APLICADA')

    def test_abc123_repeticiones(self):
        base_factura = {
            'fecha_factura': '2024-01-10',
            'nit_cliente': '900100200',
            'nombre_cliente': 'Cliente Demo',
            'codigo_producto': 'P001',
            'nombre_producto': 'Producto',
            'cantidad_original': 1,
            'indice_linea': 0
        }
        f1 = {**base_factura, 'numero_factura': 'A1', 'codigo_factura': 'abc123', 'valor_total': 100000}
        f2 = {**base_factura, 'numero_factura': 'A2', 'codigo_factura': 'abc123', 'valor_total': 200000}
        f3 = {**base_factura, 'numero_factura': 'A3', 'codigo_factura': 'abc123', 'valor_total': 300000}

        self.assertTrue(self.manager.registrar_factura(f1))
        self.assertTrue(self.manager.registrar_factura(f2))
        self.assertTrue(self.manager.registrar_factura(f3))

        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT registrable FROM facturas WHERE codigo_factura = ?', ('abc123',))
        registrables = {row[0] for row in cursor.fetchall()}
        conn.close()

        self.assertIn(1, registrables)


if __name__ == '__main__':
    unittest.main()
