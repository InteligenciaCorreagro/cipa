import os
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.notas_credito_manager import NotasCreditoManager


class TestRegistroFacturasPlain(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.manager = NotasCreditoManager(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_insercion_100_facturas_y_explicaciones(self):
        facturas_validas = []
        facturas_rechazadas = []

        for i in range(1, 101):
            numero = f"F{i:03d}"
            facturas_validas.append({
                'numero_factura': numero,
                'codigo_factura': numero,
                'fecha_factura': '2024-02-10',
                'nit_cliente': '900123456',
                'nombre_cliente': 'Cliente Prueba',
                'codigo_producto': f"P{i:03d}",
                'nombre_producto': 'Producto',
                'cantidad_original': 1,
                'valor_total': 600000,
                'indice_linea': 0
            })
            facturas_rechazadas.append({
                'factura': {
                    'f_prefijo': 'R',
                    'f_nrodocto': f"{i:03d}",
                    'f_fecha': '2024-02-10',
                    'f_cod_item': f"X{i:03d}",
                    'f_desc_item': 'Producto Rechazado',
                    'f_cliente_desp': '900123456',
                    'f_cliente_fact_razon_soc': 'Cliente Prueba',
                    'f_cant_base': 1,
                    'f_valor_subtotal_local': 1000,
                    'f_cod_tipo_inv': 'INV'
                },
                'razon_rechazo': f"Rechazo {i}"
            })

        ok, error_detalle = self.manager.registrar_facturas_y_rechazos(
            facturas_validas,
            facturas_rechazadas
        )
        self.assertTrue(ok, error_detalle)

        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM facturas')
        total_facturas = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM facturas_rechazadas')
        total_rechazadas = cursor.fetchone()[0]

        cursor.execute('SELECT nit_encrypted, nombre_cliente_encrypted FROM facturas LIMIT 1')
        nit_cliente, nombre_cliente = cursor.fetchone()

        cursor.execute('SELECT razon_rechazo, nit_encrypted FROM facturas_rechazadas LIMIT 1')
        razon_rechazo, nit_rechazo = cursor.fetchone()
        conn.close()

        self.assertEqual(total_facturas, 100)
        self.assertEqual(total_rechazadas, 100)
        self.assertEqual(nit_cliente, '900123456')
        self.assertEqual(nombre_cliente, 'Cliente Prueba')
        self.assertEqual(nit_rechazo, '900123456')
        self.assertTrue(razon_rechazo.startswith('Rechazo'))
        self.assertFalse(str(nit_cliente).startswith('gAAAA'))
        self.assertFalse(str(nit_rechazo).startswith('gAAAA'))


if __name__ == '__main__':
    unittest.main()
