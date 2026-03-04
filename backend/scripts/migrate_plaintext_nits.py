import argparse
import os
import sqlite3
import hashlib
from cryptography.fernet import Fernet, InvalidToken


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


def migrate_up(conn: sqlite3.Connection):
    fernet = _build_fernet()
    cursor = conn.cursor()

    for table in ['facturas', 'facturas_rechazadas', 'notas_credito']:
        cursor.execute(f"SELECT id, nit_encrypted, nombre_cliente_encrypted, nit_hash FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            nit_plain = _decrypt_value(fernet, row[1])
            nombre_plain = _decrypt_value(fernet, row[2])
            cursor.execute(
                f"UPDATE {table} SET nit_encrypted = ?, nombre_cliente_encrypted = ?, nit_hash = ? WHERE id = ?",
                (nit_plain, nombre_plain, nit_plain, row[0])
            )

    cursor.execute("SELECT id, nit_hash FROM aplicaciones_notas")
    for row in cursor.fetchall():
        nit_plain = _decrypt_value(fernet, row[1])
        cursor.execute("UPDATE aplicaciones_notas SET nit_hash = ? WHERE id = ?", (nit_plain, row[0]))

    cursor.execute("DROP INDEX IF EXISTS idx_facturas_nit_hash")
    cursor.execute("DROP INDEX IF EXISTS idx_rechazadas_nit_hash")
    cursor.execute("DROP INDEX IF EXISTS idx_notas_cliente")
    cursor.execute("DROP INDEX IF EXISTS idx_aplicaciones_nit_hash")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_facturas_nit ON facturas(nit_encrypted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rechazadas_nit ON facturas_rechazadas(nit_encrypted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas_credito(nit_encrypted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aplicaciones_nit ON aplicaciones_notas(nit_hash)")

    conn.commit()


def migrate_down(conn: sqlite3.Connection):
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
                f"UPDATE {table} SET nit_encrypted = ?, nombre_cliente_encrypted = ?, nit_hash = ? WHERE id = ?",
                (nit_enc, nombre_enc, nit_hash, row[0])
            )

    cursor.execute("SELECT id, nit_hash FROM aplicaciones_notas")
    for row in cursor.fetchall():
        nit_enc = _encrypt_value(fernet, row[1])
        cursor.execute("UPDATE aplicaciones_notas SET nit_hash = ? WHERE id = ?", (nit_enc, row[0]))

    cursor.execute("DROP INDEX IF EXISTS idx_facturas_nit")
    cursor.execute("DROP INDEX IF EXISTS idx_rechazadas_nit")
    cursor.execute("DROP INDEX IF EXISTS idx_notas_cliente")
    cursor.execute("DROP INDEX IF EXISTS idx_aplicaciones_nit")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_facturas_nit_hash ON facturas(nit_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rechazadas_nit_hash ON facturas_rechazadas(nit_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas_credito(nit_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aplicaciones_nit_hash ON aplicaciones_notas(nit_hash)")

    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-path', default='./data/notas_credito.db')
    parser.add_argument('--direction', choices=['up', 'down'], default='up')
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        if args.direction == 'up':
            migrate_up(conn)
        else:
            migrate_down(conn)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
