#!/usr/bin/env python3
"""
Script para ver el esquema de la base de datos
"""
import sqlite3

def view_schema(db_path='./data/notas_credito.db'):
    """Ver esquema de todas las tablas"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = [t[0] for t in cursor.fetchall()]

    for tabla in tablas:
        if tabla == 'sqlite_sequence':
            continue
        print(f"\n{'='*60}")
        print(f"Tabla: {tabla}")
        print(f"{'='*60}")
        cursor.execute(f"PRAGMA table_info({tabla})")
        columnas = cursor.fetchall()
        for col in columnas:
            print(f"  {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}{' NOT NULL' if col[3] else ''}")

    conn.close()

if __name__ == '__main__':
    import os
    os.chdir('/home/user/cipa')
    view_schema()
