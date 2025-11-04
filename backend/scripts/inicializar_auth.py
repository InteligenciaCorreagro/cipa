#!/usr/bin/env python3
"""
Script para inicializar el sistema de autenticación
Crea las tablas necesarias y el usuario admin por defecto
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'api'))

from auth import AuthManager

print("="*60)
print("INICIALIZANDO SISTEMA DE AUTENTICACIÓN")
print("="*60)
print()

# Ruta de la base de datos
DB_PATH = Path(__file__).parent / 'data' / 'notas_credito.db'
print(f"Base de datos: {DB_PATH}")
print(f"¿Existe? {DB_PATH.exists()}")
print()

# Inicializar AuthManager (esto crea las tablas y el usuario admin)
print("Inicializando AuthManager...")
auth_manager = AuthManager(db_path=str(DB_PATH))
print("✅ AuthManager inicializado")
print()

# Verificar que se crearon las tablas
import sqlite3
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tablas en la BD: {tables}")
print()

# Verificar usuario admin
cursor.execute("SELECT id, username, email, rol, activo FROM usuarios WHERE username='admin'")
usuario = cursor.fetchone()

if usuario:
    user_id, username, email, rol, activo = usuario
    print("✅ Usuario admin creado exitosamente:")
    print(f"   ID: {user_id}")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Rol: {rol}")
    print(f"   Activo: {'✅' if activo else '❌'}")
    print()
    print("="*60)
    print("CREDENCIALES DE ACCESO:")
    print("="*60)
    print("   Username: admin")
    print("   Password: admin123")
    print("="*60)
    print()
    print("⚠️  IMPORTANTE: Cambia la contraseña por defecto inmediatamente")
    print("              después del primer login!")
else:
    print("❌ Error: No se pudo crear el usuario admin")
    exit(1)

conn.close()

print()
print("✅ Sistema de autenticación inicializado correctamente")
print()
print("Ahora puedes iniciar la API con:")
print("  python api/app.py")
print()
