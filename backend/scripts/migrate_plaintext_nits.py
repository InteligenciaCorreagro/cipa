import argparse
import os
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from db import get_mysql_config
import mysql.connector as mc


def _build_fernet():
    key = os.getenv('DATA_ENCRYPTION_KEY')
    if not key:
        raise ValueError('DATA_ENCRYPTION_KEY no configurada')
    if isinstance(key, str):
        key = key.encode('utf-8')
    return Fernet(key)


def _decrypt_value(fernet: Fernet, value: str) -> str:
    if not value:
        return ''
    if not str(value).startswith('gAAAA'):
        return value
    try:
        return fernet.decrypt(str(value).encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return value


def _encrypt_value(fernet: Fernet, value: str) -> str:
    if value is None:
        return ''
    return fernet.encrypt(str(value).encode('utf-8')).decode('utf-8')


def _hash_value(value: str, salt: str) -> str:
    raw = f"{salt}{value}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def migrate_up(conn):
    fernet = _build_fernet()
    cursor = conn.cursor()

    for table in ['facturas', 'facturas_rechazadas', 'notas_credito']:
        cursor.execute(f"SELECT id, nit_encrypted, nombre_cliente_encrypted, nit_hash FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            nit_plain = _decrypt_value(fernet, row[1])
            nombre_plain = _decrypt_value(fernet, row[2])
            cursor.execute(
                f"UPDATE {table} SET nit_encrypted = %s, nombre_cliente_encrypted = %s, nit_hash = %s WHERE id = %s",
                (nit_plain, nombre_plain, nit_plain, row[0])
            )

    cursor.execute("SELECT id, nit_hash FROM aplicaciones_notas")
    for row in cursor.fetchall():
        nit_plain = _decrypt_value(fernet, row[1])
        cursor.execute("UPDATE aplicaciones_notas SET nit_hash = %s WHERE id = %s", (nit_plain, row[0]))

    for index_name in ['idx_facturas_nit_hash', 'idx_rechazadas_nit_hash', 'idx_notas_cliente', 'idx_aplicaciones_nit_hash']:
        try:
            cursor.execute(f"DROP INDEX {index_name} ON {'notas_credito' if index_name == 'idx_notas_cliente' else ('aplicaciones_notas' if index_name == 'idx_aplicaciones_nit_hash' else ('facturas' if index_name == 'idx_facturas_nit_hash' else 'facturas_rechazadas'))}")
        except Exception:
            pass
    for query in [
        "CREATE INDEX idx_facturas_nit ON facturas(nit_encrypted)",
        "CREATE INDEX idx_rechazadas_nit ON facturas_rechazadas(nit_encrypted)",
        "CREATE INDEX idx_notas_cliente ON notas_credito(nit_encrypted)",
        "CREATE INDEX idx_aplicaciones_nit ON aplicaciones_notas(nit_hash)",
    ]:
        try:
            cursor.execute(query)
        except Exception:
            pass

    conn.commit()


def migrate_down(conn):
    fernet = _build_fernet()
    salt = os.getenv('DATA_HASH_SALT', '')
    cursor = conn.cursor()

    for table in ['facturas', 'facturas_rechazadas', 'notas_credito']:
        cursor.execute(f"SELECT id, nit_encrypted, nombre_cliente_encrypted FROM {table}")
        for row in cursor.fetchall():
            nit_enc = _encrypt_value(fernet, row[1])
            nombre_enc = _encrypt_value(fernet, row[2])
            nit_hash = _hash_value(row[1], salt)
            cursor.execute(
                f"UPDATE {table} SET nit_encrypted = %s, nombre_cliente_encrypted = %s, nit_hash = %s WHERE id = %s",
                (nit_enc, nombre_enc, nit_hash, row[0])
            )

    cursor.execute("SELECT id, nit_hash FROM aplicaciones_notas")
    for row in cursor.fetchall():
        nit_enc = _encrypt_value(fernet, row[1])
        cursor.execute("UPDATE aplicaciones_notas SET nit_hash = %s WHERE id = %s", (nit_enc, row[0]))

    for index_name in ['idx_facturas_nit', 'idx_rechazadas_nit', 'idx_notas_cliente', 'idx_aplicaciones_nit']:
        try:
            cursor.execute(f"DROP INDEX {index_name} ON {'notas_credito' if index_name == 'idx_notas_cliente' else ('aplicaciones_notas' if index_name == 'idx_aplicaciones_nit' else ('facturas' if index_name == 'idx_facturas_nit' else 'facturas_rechazadas'))}")
        except Exception:
            pass
    for query in [
        "CREATE INDEX idx_facturas_nit_hash ON facturas(nit_hash)",
        "CREATE INDEX idx_rechazadas_nit_hash ON facturas_rechazadas(nit_hash)",
        "CREATE INDEX idx_notas_cliente ON notas_credito(nit_hash)",
        "CREATE INDEX idx_aplicaciones_nit_hash ON aplicaciones_notas(nit_hash)",
    ]:
        try:
            cursor.execute(query)
        except Exception:
            pass

    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--direction', choices=['up', 'down'], default='up')
    args = parser.parse_args()

    conn = mc.connect(**get_mysql_config())
    try:
        if args.direction == 'up':
            migrate_up(conn)
        else:
            migrate_down(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
