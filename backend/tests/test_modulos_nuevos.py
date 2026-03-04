import os
import tempfile
import unittest

from core.notas_credito_manager import NotasCreditoManager


class TestModulosNuevos(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.manager = NotasCreditoManager(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_tablas_nuevas(self):
        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notas_pendientes'")
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='aplicaciones_sistema'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_insertar_nota_pendiente(self):
        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notas_pendientes
            (numero_nota, prioridad, fecha_vencimiento, responsable, estado, descripcion)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('N-001', 'alta', '2024-02-10', 'Juan', 'PENDIENTE', 'Pendiente de revisión'))
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM notas_pendientes")
        total = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(total, 1)

    def test_insertar_aplicacion(self):
        conn = self.manager._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO aplicaciones_sistema
            (nombre, version, fecha_instalacion, estado, uso_total)
            VALUES (?, ?, ?, ?, ?)
        ''', ('App CIPA', '1.0.0', '2024-02-10', 'ACTIVA', 3))
        conn.commit()
        cursor.execute("SELECT nombre, uso_total FROM aplicaciones_sistema")
        row = cursor.fetchone()
        conn.close()
        self.assertEqual(row[0], 'App CIPA')
        self.assertEqual(row[1], 3)


if __name__ == '__main__':
    unittest.main()
