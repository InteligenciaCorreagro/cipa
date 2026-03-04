import os
import sys
import unittest
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.business_rules import BusinessRulesValidator


class TestReglasNegocio(unittest.TestCase):
    def setUp(self):
        os.environ['MONTO_MINIMO_VALIDO'] = '524000'
        self.validator = BusinessRulesValidator()

    def test_nota_credito_no_aplica_tipo_inventario(self):
        nota = {
            'f_prefijo': 'N',
            'f_nrodocto': '123',
            'f_cod_tipo_inv': 'P',
            'f_02_014': 'AGENTE',
            'f_valor_subtotal_local': 1000
        }
        facturas_validas, notas, facturas_rechazadas = self.validator.filtrar_facturas([nota])
        self.assertEqual(len(notas), 1)
        self.assertEqual(len(facturas_rechazadas), 0)
        self.assertEqual(len(facturas_validas), 0)

    def test_nota_credito_rechaza_no_agente(self):
        nota = {
            'f_prefijo': 'N',
            'f_nrodocto': '124',
            'f_cod_tipo_inv': 'P',
            'f_02_014': 'NO AGENTE DE RETENCION',
            'f_valor_subtotal_local': 1000
        }
        facturas_validas, notas, facturas_rechazadas = self.validator.filtrar_facturas([nota])
        self.assertEqual(len(notas), 0)
        self.assertEqual(len(facturas_rechazadas), 1)
        self.assertEqual(len(facturas_validas), 0)

    def test_factura_rechaza_monto_minimo(self):
        factura = {
            'f_prefijo': 'F',
            'f_nrodocto': '001',
            'f_valor_subtotal_local': 1000,
            'f_02_014': 'AGENTE',
            'f_cod_tipo_inv': 'C'
        }
        facturas_validas, notas, facturas_rechazadas = self.validator.filtrar_facturas([factura])
        self.assertEqual(len(facturas_validas), 0)
        self.assertEqual(len(facturas_rechazadas), 1)
        self.assertEqual(len(notas), 0)


if __name__ == '__main__':
    unittest.main()
