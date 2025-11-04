"""
Sistema de archivado de notas de crédito aplicadas

Este módulo maneja el archivado automático de notas completamente aplicadas
para controlar el tamaño de la base de datos principal.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ArchivadorNotas:
    """Gestiona el archivado de notas de crédito aplicadas"""

    def __init__(self, db_path: str = "./data/notas_credito.db"):
        self.db_path = db_path
        self.archivo_db_path = str(Path(db_path).parent / "archivo_notas.db")
        self._inicializar_bd_archivo()

    def _inicializar_bd_archivo(self):
        """Inicializa la base de datos de archivo si no existe"""
        conn = sqlite3.connect(self.archivo_db_path)
        cursor = conn.cursor()

        # Tabla de notas archivadas (misma estructura que notas_credito)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas_archivadas (
                id INTEGER PRIMARY KEY,
                numero_nota TEXT NOT NULL UNIQUE,
                fecha_nota DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                nombre_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                nombre_producto TEXT NOT NULL,
                tipo_inventario TEXT,
                valor_total REAL NOT NULL,
                cantidad REAL NOT NULL,
                saldo_pendiente REAL NOT NULL,
                cantidad_pendiente REAL NOT NULL,
                estado TEXT,
                fecha_registro TIMESTAMP,
                fecha_aplicacion_completa TIMESTAMP,
                fecha_archivado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de aplicaciones archivadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aplicaciones_archivadas (
                id INTEGER PRIMARY KEY,
                id_nota INTEGER NOT NULL,
                numero_nota TEXT NOT NULL,
                numero_factura TEXT NOT NULL,
                fecha_factura DATE NOT NULL,
                nit_cliente TEXT NOT NULL,
                codigo_producto TEXT NOT NULL,
                valor_aplicado REAL NOT NULL,
                cantidad_aplicada REAL NOT NULL,
                fecha_aplicacion TIMESTAMP,
                fecha_archivado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de metadata de archivado
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata_archivado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_archivado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notas_archivadas INTEGER,
                aplicaciones_archivadas INTEGER,
                espacio_liberado_bytes INTEGER,
                notas_restantes INTEGER
            )
        ''')

        # Índices
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_arch_notas_fecha
            ON notas_archivadas(fecha_archivado)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_arch_aplicaciones_nota
            ON aplicaciones_archivadas(numero_nota)
        ''')

        conn.commit()
        conn.close()

    def obtener_notas_para_archivar(self, dias_minimos: int = 30) -> List[Dict]:
        """
        Obtiene lista de notas completamente aplicadas que pueden archivarse

        Args:
            dias_minimos: Días mínimos desde aplicación completa

        Returns:
            Lista de notas candidatas para archivo
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        fecha_limite = datetime.now() - timedelta(days=dias_minimos)

        cursor.execute('''
            SELECT id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                   codigo_producto, nombre_producto, tipo_inventario,
                   valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                   estado, fecha_registro, fecha_aplicacion_completa
            FROM notas_credito
            WHERE estado = 'APLICADA'
              AND fecha_aplicacion_completa IS NOT NULL
              AND fecha_aplicacion_completa <= ?
        ''', (fecha_limite,))

        notas = []
        for row in cursor.fetchall():
            notas.append({
                'id': row[0],
                'numero_nota': row[1],
                'fecha_nota': row[2],
                'nit_cliente': row[3],
                'nombre_cliente': row[4],
                'codigo_producto': row[5],
                'nombre_producto': row[6],
                'tipo_inventario': row[7],
                'valor_total': row[8],
                'cantidad': row[9],
                'saldo_pendiente': row[10],
                'cantidad_pendiente': row[11],
                'estado': row[12],
                'fecha_registro': row[13],
                'fecha_aplicacion_completa': row[14]
            })

        conn.close()
        return notas

    def archivar_notas(self, notas_ids: List[int] = None, dias_minimos: int = 30,
                       dry_run: bool = False) -> Dict:
        """
        Archiva notas completamente aplicadas

        Args:
            notas_ids: IDs específicos a archivar (None = automático por fecha)
            dias_minimos: Días mínimos desde aplicación completa
            dry_run: Solo mostrar qué se archivaría sin hacer cambios

        Returns:
            Diccionario con estadísticas del archivado
        """
        stats = {
            'notas_archivadas': 0,
            'aplicaciones_archivadas': 0,
            'espacio_liberado_bytes': 0,
            'notas_restantes': 0,
            'dry_run': dry_run
        }

        conn_principal = sqlite3.connect(self.db_path)
        conn_archivo = sqlite3.connect(self.archivo_db_path)

        cursor_principal = conn_principal.cursor()
        cursor_archivo = conn_archivo.cursor()

        try:
            # Obtener notas a archivar
            if notas_ids:
                placeholders = ','.join('?' * len(notas_ids))
                cursor_principal.execute(f'''
                    SELECT id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                           codigo_producto, nombre_producto, tipo_inventario,
                           valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                           estado, fecha_registro, fecha_aplicacion_completa
                    FROM notas_credito
                    WHERE id IN ({placeholders})
                      AND estado = 'APLICADA'
                ''', notas_ids)
            else:
                fecha_limite = datetime.now() - timedelta(days=dias_minimos)
                cursor_principal.execute('''
                    SELECT id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                           codigo_producto, nombre_producto, tipo_inventario,
                           valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                           estado, fecha_registro, fecha_aplicacion_completa
                    FROM notas_credito
                    WHERE estado = 'APLICADA'
                      AND fecha_aplicacion_completa IS NOT NULL
                      AND fecha_aplicacion_completa <= ?
                ''', (fecha_limite,))

            notas = cursor_principal.fetchall()

            if not notas:
                logger.info("No hay notas para archivar")
                return stats

            # Calcular tamaño antes
            cursor_principal.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            tamano_antes = cursor_principal.fetchone()[0]

            for nota in notas:
                id_nota = nota[0]
                numero_nota = nota[1]

                # Obtener aplicaciones de esta nota
                cursor_principal.execute('''
                    SELECT id, id_nota, numero_nota, numero_factura, fecha_factura,
                           nit_cliente, codigo_producto, valor_aplicado, cantidad_aplicada,
                           fecha_aplicacion
                    FROM aplicaciones_notas
                    WHERE id_nota = ?
                ''', (id_nota,))

                aplicaciones = cursor_principal.fetchall()

                if not dry_run:
                    # Insertar nota en archivo
                    cursor_archivo.execute('''
                        INSERT INTO notas_archivadas
                        (id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                         codigo_producto, nombre_producto, tipo_inventario,
                         valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                         estado, fecha_registro, fecha_aplicacion_completa)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', nota)

                    # Insertar aplicaciones en archivo
                    for app in aplicaciones:
                        cursor_archivo.execute('''
                            INSERT INTO aplicaciones_archivadas
                            (id, id_nota, numero_nota, numero_factura, fecha_factura,
                             nit_cliente, codigo_producto, valor_aplicado,
                             cantidad_aplicada, fecha_aplicacion)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', app)

                    # Eliminar de base principal
                    cursor_principal.execute('DELETE FROM aplicaciones_notas WHERE id_nota = ?', (id_nota,))
                    cursor_principal.execute('DELETE FROM notas_credito WHERE id = ?', (id_nota,))

                stats['notas_archivadas'] += 1
                stats['aplicaciones_archivadas'] += len(aplicaciones)

                logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Archivada nota: {numero_nota} "
                          f"con {len(aplicaciones)} aplicaciones")

            # Contar notas restantes
            cursor_principal.execute('SELECT COUNT(*) FROM notas_credito')
            stats['notas_restantes'] = cursor_principal.fetchone()[0]

            if not dry_run:
                # Guardar metadata
                cursor_archivo.execute('''
                    INSERT INTO metadata_archivado
                    (notas_archivadas, aplicaciones_archivadas, notas_restantes)
                    VALUES (?, ?, ?)
                ''', (stats['notas_archivadas'], stats['aplicaciones_archivadas'],
                      stats['notas_restantes']))

                # VACUUM para liberar espacio
                conn_principal.execute('VACUUM')

                # Calcular tamaño después
                cursor_principal.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                tamano_despues = cursor_principal.fetchone()[0]

                stats['espacio_liberado_bytes'] = tamano_antes - tamano_despues

            conn_archivo.commit()
            conn_principal.commit()

        except Exception as e:
            conn_archivo.rollback()
            conn_principal.rollback()
            raise e
        finally:
            conn_archivo.close()
            conn_principal.close()

        return stats

    def obtener_estadisticas_archivo(self) -> Dict:
        """Obtiene estadísticas del archivo"""
        conn = sqlite3.connect(self.archivo_db_path)
        cursor = conn.cursor()

        stats = {}

        # Total notas archivadas
        cursor.execute('SELECT COUNT(*) FROM notas_archivadas')
        stats['total_notas_archivadas'] = cursor.fetchone()[0]

        # Total aplicaciones archivadas
        cursor.execute('SELECT COUNT(*) FROM aplicaciones_archivadas')
        stats['total_aplicaciones_archivadas'] = cursor.fetchone()[0]

        # Último archivado
        cursor.execute('SELECT MAX(fecha_archivado) FROM metadata_archivado')
        stats['ultimo_archivado'] = cursor.fetchone()[0]

        # Total archivados
        cursor.execute('SELECT SUM(notas_archivadas) FROM metadata_archivado')
        stats['total_operaciones_archivado'] = cursor.fetchone()[0] or 0

        # Tamaño del archivo
        archivo_path = Path(self.archivo_db_path)
        if archivo_path.exists():
            stats['tamano_archivo_bytes'] = archivo_path.stat().st_size
            stats['tamano_archivo_mb'] = stats['tamano_archivo_bytes'] / (1024 * 1024)

        conn.close()
        return stats

    def restaurar_notas(self, notas_ids: List[int]) -> int:
        """
        Restaura notas archivadas a la base principal

        Args:
            notas_ids: IDs de notas a restaurar

        Returns:
            Cantidad de notas restauradas
        """
        conn_principal = sqlite3.connect(self.db_path)
        conn_archivo = sqlite3.connect(self.archivo_db_path)

        cursor_principal = conn_principal.cursor()
        cursor_archivo = conn_archivo.cursor()

        restauradas = 0

        try:
            for id_nota in notas_ids:
                # Obtener nota del archivo
                cursor_archivo.execute('''
                    SELECT id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                           codigo_producto, nombre_producto, tipo_inventario,
                           valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                           estado, fecha_registro, fecha_aplicacion_completa
                    FROM notas_archivadas
                    WHERE id = ?
                ''', (id_nota,))

                nota = cursor_archivo.fetchone()
                if not nota:
                    continue

                # Obtener aplicaciones
                cursor_archivo.execute('''
                    SELECT id, id_nota, numero_nota, numero_factura, fecha_factura,
                           nit_cliente, codigo_producto, valor_aplicado,
                           cantidad_aplicada, fecha_aplicacion
                    FROM aplicaciones_archivadas
                    WHERE id_nota = ?
                ''', (id_nota,))

                aplicaciones = cursor_archivo.fetchall()

                # Insertar en base principal
                cursor_principal.execute('''
                    INSERT INTO notas_credito
                    (id, numero_nota, fecha_nota, nit_cliente, nombre_cliente,
                     codigo_producto, nombre_producto, tipo_inventario,
                     valor_total, cantidad, saldo_pendiente, cantidad_pendiente,
                     estado, fecha_registro, fecha_aplicacion_completa)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', nota[:15])

                for app in aplicaciones:
                    cursor_principal.execute('''
                        INSERT INTO aplicaciones_notas
                        (id, id_nota, numero_nota, numero_factura, fecha_factura,
                         nit_cliente, codigo_producto, valor_aplicado,
                         cantidad_aplicada, fecha_aplicacion)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', app)

                # Eliminar del archivo
                cursor_archivo.execute('DELETE FROM aplicaciones_archivadas WHERE id_nota = ?', (id_nota,))
                cursor_archivo.execute('DELETE FROM notas_archivadas WHERE id = ?', (id_nota,))

                restauradas += 1
                logger.info(f"Restaurada nota ID: {id_nota}")

            conn_archivo.commit()
            conn_principal.commit()

        except Exception as e:
            conn_archivo.rollback()
            conn_principal.rollback()
            raise e
        finally:
            conn_archivo.close()
            conn_principal.close()

        return restauradas
