#!/usr/bin/env python3
"""
Script para verificar el usuario admin en la base de datos
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'notas_credito.db'

print(f"Verificando base de datos en: {DB_PATH}")
print(f"¿Existe la BD? {DB_PATH.exists()}\n")

if not DB_PATH.exists():
    print("❌ La base de datos no existe!")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Verificar tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tablas en la BD: {[t[0] for t in tables]}\n")

# Verificar si existe la tabla usuarios
if ('usuarios',) not in tables:
    print("❌ La tabla 'usuarios' no existe!")
    conn.close()
    exit(1)

# Ver todos los usuarios
cursor.execute("SELECT id, username, email, rol, activo, intentos_fallidos, bloqueado_hasta FROM usuarios")
usuarios = cursor.fetchall()

if len(usuarios) == 0:
    print("❌ No hay usuarios en la base de datos!")
else:
    print(f"✅ Encontrados {len(usuarios)} usuario(s):\n")
    for user in usuarios:
        user_id, username, email, rol, activo, intentos, bloqueado = user
        print(f"  ID: {user_id}")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Rol: {rol}")
        print(f"  Activo: {'✅ Sí' if activo else '❌ No'}")
        print(f"  Intentos fallidos: {intentos}")
        print(f"  Bloqueado hasta: {bloqueado if bloqueado else 'No bloqueado'}")
        print()

# Verificar el hash de contraseña del admin
cursor.execute("SELECT password_hash FROM usuarios WHERE username='admin'")
result = cursor.fetchone()
if result:
    password_hash = result[0]
    print(f"Hash de contraseña del admin:")
    print(f"  {password_hash[:50]}..." if len(password_hash) > 50 else f"  {password_hash}")
    print(f"  Longitud del hash: {len(password_hash)}")

    # Verificar el formato del hash bcrypt
    if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
        print("  ✅ Formato bcrypt correcto")
    else:
        print("  ❌ Formato de hash incorrecto (no es bcrypt)")

conn.close()

print("\n" + "="*60)
print("Credenciales por defecto:")
print("  Username: admin")
print("  Password: admin123")
print("="*60)
