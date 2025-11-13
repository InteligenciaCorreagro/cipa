#!/usr/bin/env python3
"""
Script mejorado para iniciar la API con verificaciones

Uso:
    python iniciar_api.py
"""

import sys
import subprocess
from pathlib import Path

# Colores para terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_colored(message, color=RESET):
    print(f"{color}{message}{RESET}")

def verificar_dependencias():
    """Verifica que las dependencias estén instaladas"""
    print_colored("\n🔍 Verificando dependencias...", BLUE)

    dependencias = [
        'flask', 'flask_jwt_extended', 'flask_limiter',
        'flask_cors', 'bcrypt', 'dotenv'
    ]

    faltantes = []
    for dep in dependencias:
        try:
            __import__(dep)
            print_colored(f"  ✓ {dep}", GREEN)
        except ImportError:
            faltantes.append(dep)
            print_colored(f"  ✗ {dep} - FALTA", RED)

    if faltantes:
        print_colored("\n❌ Faltan dependencias. Instalar con:", RED)
        print_colored("   pip install -r api/requirements.txt\n", YELLOW)
        return False

    print_colored("✓ Todas las dependencias instaladas\n", GREEN)
    return True

def verificar_base_datos():
    """Verifica que la base de datos exista"""
    print_colored("🔍 Verificando base de datos...", BLUE)

    # Usar la misma ruta que el resto del sistema (raíz del proyecto)
    import os
    project_root = Path(__file__).parent.parent
    db_path = Path(os.getenv('DB_PATH', str(project_root / 'data' / 'notas_credito.db')))

    if not db_path.exists():
        print_colored(f"⚠️  Base de datos no encontrada en: {db_path}", YELLOW)
        print_colored("   Se creará automáticamente al iniciar la API", YELLOW)
    else:
        print_colored(f"✓ Base de datos encontrada: {db_path}", GREEN)

    print()

def verificar_env():
    """Verifica configuración de .env"""
    print_colored("🔍 Verificando configuración...", BLUE)

    env_path = Path(__file__).parent / '.env'

    if not env_path.exists():
        print_colored("⚠️  Archivo .env no encontrado", YELLOW)
        print_colored("   Usar configuración por defecto", YELLOW)
        print_colored("   Recomendado: crear .env desde .env.example", YELLOW)
    else:
        print_colored(f"✓ Archivo .env encontrado", GREEN)

        # Verificar JWT_SECRET_KEY
        with open(env_path, 'r') as f:
            contenido = f.read()
            if 'CHANGE-THIS-SECRET-KEY' in contenido:
                print_colored("⚠️  JWT_SECRET_KEY usa valor por defecto", YELLOW)
                print_colored("   Cambiar en producción!", YELLOW)

    print()

def main():
    print_colored("="*60, BLUE)
    print_colored("    API REST - Sistema de Notas de Crédito CIPA", BLUE)
    print_colored("="*60, BLUE)

    # Verificaciones
    if not verificar_dependencias():
        sys.exit(1)

    verificar_base_datos()
    verificar_env()

    # Iniciar API
    print_colored("="*60, GREEN)
    print_colored("🚀 Iniciando API...", GREEN)
    print_colored("="*60, GREEN)
    print()
    print_colored("📍 URL: http://localhost:5000", BLUE)
    print_colored("📚 Health check: http://localhost:5000/api/health", BLUE)
    print_colored("📖 Docs: api/README.md", BLUE)
    print()
    print_colored("Presiona CTRL+C para detener", YELLOW)
    print_colored("="*60, BLUE)
    print()

    # Ejecutar API
    try:
        subprocess.run([sys.executable, 'api/app.py'])
    except KeyboardInterrupt:
        print_colored("\n\n🛑 API detenida por el usuario", YELLOW)
        sys.exit(0)

if __name__ == '__main__':
    main()
