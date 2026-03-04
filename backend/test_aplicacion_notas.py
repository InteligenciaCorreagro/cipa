import os
import sys
import tempfile
import unittest
sys.path.append(os.path.dirname(__file__))
from core.notas_credito_manager import NotasCreditoManager


class TestAplicacionNotas(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.manager = NotasCreditoManager(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_aplicacion_basica(self):
        factura = {
            'numero_factura': 'F123',
            'codigo_factura': 'F123',
            'fecha_factura': '2024-01-10',
            'nit_cliente': '123456789',
            'nombre_cliente': 'Cliente',
            'codigo_producto': 'P001',
            'nombre_producto': 'Producto',
            'cantidad_original': 25,
            'valor_total': 600000,
            'indice_linea': 0
        }
        nota = {
            'numero_nota': 'N001',
            'fecha_nota': '2024-01-10',
            'nit_cliente': '123456789',
            'nombre_cliente': 'Cliente',
            'codigo_producto': 'P001',
            'nombre_producto': 'Producto',
            'cantidad': 20,
            'valor_total': 200000,
            'es_agente': 'AGENTE'
        }
        self.assertTrue(self.manager.registrar_factura(factura))
        self.assertTrue(self.manager.registrar_nota_credito(nota))

        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notas_credito WHERE numero_nota = ?', ('N001',))
        nota_db = dict(cursor.fetchone())
        cursor.execute('SELECT * FROM facturas WHERE numero_factura = ?', ('F123',))
        factura_db = dict(cursor.fetchone())
        conn.close()

        resultado = self.manager.aplicar_nota_a_factura(nota_db, {
            'numero_factura': factura_db['numero_factura'],
            'f_cliente_desp': factura_db['nit_encrypted'],
            'f_cod_item': factura_db['codigo_producto'],
            'f_cant_base': factura_db['cantidad_restante'],
            'f_valor_subtotal_local': factura_db['valor_restante'],
            'f_fecha': factura_db['fecha_factura'],
            '_indice_linea': factura_db['indice_linea']
        })
        self.assertIsNotNone(resultado)


if __name__ == "__main__":
    unittest.main()
