import os
import sqlite3
import argparse

import mysql.connector


def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'cipa'),
        autocommit=False
    )


def fetch_table(sqlite_conn, table: str):
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    return columns, rows


def insert_rows(mysql_conn, table: str, columns, rows):
    if not rows:
        return
    placeholders = ','.join(['%s'] * len(columns))
    col_list = ','.join(columns)
    query = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    cursor = mysql_conn.cursor()
    cursor.executemany(query, rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlite-path', default='backend/data/notas_credito.db')
    parser.add_argument('--truncate', action='store_true')
    args = parser.parse_args()

    sqlite_conn = sqlite3.connect(args.sqlite_path)
    mysql_conn = get_mysql_connection()
    mysql_cursor = mysql_conn.cursor()

    tables = [
        'usuarios',
        'usuarios_2fa',
        'sesiones',
        'intentos_login',
        'facturas',
        'facturas_rechazadas',
        'notas_credito',
        'aplicaciones_notas',
        'log_motivos_no_aplicacion',
        'audit_logs',
        'notas_pendientes',
        'aplicaciones_sistema'
    ]

    try:
        if args.truncate:
            for table in tables:
                mysql_cursor.execute(f"DELETE FROM {table}")

        for table in tables:
            columns, rows = fetch_table(sqlite_conn, table)
            insert_rows(mysql_conn, table, columns, rows)

        mysql_conn.commit()
    finally:
        sqlite_conn.close()
        mysql_conn.close()


if __name__ == '__main__':
    main()
