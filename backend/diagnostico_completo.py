#!/usr/bin/env python3
"""
Diagnóstico Completo del Problema de Token JWT
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Cambiar al directorio backend si existe
if Path('backend').exists():
    os.chdir('backend')
    sys.path.insert(0, str(Path.cwd()))

from dotenv import load_dotenv
load_dotenv()

# Colores
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_colored(message, color=RESET):
    print(f"{color}{message}{RESET}")


def verificar_configuracion_jwt():
    """Verifica la configuración JWT actual"""
    print_colored("\n" + "="*60, BLUE)
    print_colored("1. VERIFICANDO CONFIGURACIÓN JWT", BLUE)
    print_colored("="*60, BLUE)
    
    jwt_secret = os.getenv('JWT_SECRET_KEY', 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION')
    
    print_colored(f"\n🔑 JWT_SECRET_KEY:", BLUE)
    print_colored(f"  Valor: {jwt_secret[:40]}...", YELLOW)
    print_colored(f"  Longitud: {len(jwt_secret)} caracteres", YELLOW)
    
    if jwt_secret == 'CHANGE-THIS-SECRET-KEY-IN-PRODUCTION':
        print_colored(f"  ⚠️  USANDO SECRET POR DEFECTO", YELLOW)
    else:
        print_colored(f"  ✅ Secret personalizado", GREEN)
    
    return jwt_secret


def test_generar_token(jwt_secret):
    """Genera un token de prueba"""
    print_colored("\n" + "="*60, BLUE)
    print_colored("2. GENERANDO TOKEN DE PRUEBA", BLUE)
    print_colored("="*60, BLUE)
    
    try:
        from flask_jwt_extended import create_access_token, JWTManager
        from flask import Flask
        
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = jwt_secret
        
        jwt_manager = JWTManager(app)
        
        with app.app_context():
            token = create_access_token(
                identity=1,
                additional_claims={
                    'username': 'admin',
                    'rol': 'admin'
                }
            )
            
            print_colored(f"\n✅ Token generado exitosamente:", GREEN)
            print_colored(f"\n{token}", YELLOW)
            print_colored(f"\n📋 Para Postman:", BLUE)
            print_colored(f"Authorization: Bearer {token}", YELLOW)
            
            return token
            
    except Exception as e:
        print_colored(f"\n❌ Error al generar token:", RED)
        print_colored(f"  {str(e)}", RED)
        import traceback
        traceback.print_exc()
        return None


def test_decodificar_token_login(jwt_secret):
    """Decodifica el token que obtuviste del login"""
    print_colored("\n" + "="*60, BLUE)
    print_colored("3. DECODIFICANDO TOKEN DEL LOGIN", BLUE)
    print_colored("="*60, BLUE)
    
    # Token que obtuviste del login
    token_login = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2MjI4NDcyOCwianRpIjoiZWQyMzU4NDUtZDFkMS00ZDU1LWI3ZGUtNTRiZTVjNWE2OTE5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNzYyMjg0NzI4LCJjc3JmIjoiNTMyNDFmM2UtYjZmZS00ZGVhLWExNmMtMzllMzQ1Y2Y3ZTU3IiwiZXhwIjoxNzYyMjg4MzI4LCJ1c2VybmFtZSI6ImFkbWluIiwicm9sIjoiYWRtaW4ifQ.2WJvUKaZSgbAJgtxNWZFt3k7IhXdqs0oWm80w03Wky0"
    
    print_colored(f"\n📋 Token del login:", BLUE)
    print_colored(f"  {token_login[:50]}...", YELLOW)
    
    try:
        from flask_jwt_extended import decode_token
        from flask import Flask
        
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = jwt_secret
        
        with app.app_context():
            decoded = decode_token(token_login)
            
            print_colored(f"\n✅ Token decodificado exitosamente:", GREEN)
            print_colored(f"  Usuario ID: {decoded['sub']}", GREEN)
            print_colored(f"  Username: {decoded.get('username', 'N/A')}", GREEN)
            print_colored(f"  Rol: {decoded.get('rol', 'N/A')}", GREEN)
            
            # Verificar expiración
            exp = decoded['exp']
            exp_dt = datetime.fromtimestamp(exp)
            now_dt = datetime.now()
            
            print_colored(f"\n⏰ Expiración:", BLUE)
            print_colored(f"  Expira: {exp_dt.strftime('%Y-%m-%d %H:%M:%S')}", YELLOW)
            print_colored(f"  Ahora:  {now_dt.strftime('%Y-%m-%d %H:%M:%S')}", YELLOW)
            
            if now_dt > exp_dt:
                print_colored(f"\n  ❌ TOKEN EXPIRADO", RED)
                diff = (now_dt - exp_dt).total_seconds()
                print_colored(f"  Expiró hace {diff/60:.1f} minutos", RED)
                return False
            else:
                diff = (exp_dt - now_dt).total_seconds()
                print_colored(f"\n  ✅ Válido por {diff/60:.1f} minutos más", GREEN)
                return True
            
    except Exception as e:
        print_colored(f"\n❌ Error al decodificar:", RED)
        print_colored(f"  {str(e)}", RED)
        
        if "Signature verification failed" in str(e):
            print_colored(f"\n🔴 PROBLEMA CRÍTICO:", RED)
            print_colored(f"  El token fue generado con un JWT_SECRET_KEY diferente", RED)
            print_colored(f"  al que está usando el backend ahora", RED)
        
        return False


def test_validacion_backend():
    """Prueba la validación del backend directamente"""
    print_colored("\n" + "="*60, BLUE)
    print_colored("4. PROBANDO VALIDACIÓN DEL BACKEND", BLUE)
    print_colored("="*60, BLUE)
    
    try:
        import requests
        
        # Primero hacer login
        print_colored(f"\n📤 Haciendo login...", BLUE)
        
        response_login = requests.post(
            'http://localhost:2500/api/auth/login',
            json={
                'username': 'admin',
                'password': 'admin123'
            },
            timeout=5
        )
        
        if response_login.status_code != 200:
            print_colored(f"\n❌ Login falló:", RED)
            print_colored(f"  Status: {response_login.status_code}", RED)
            print_colored(f"  Respuesta: {response_login.text}", RED)
            return
        
        data = response_login.json()
        token = data['access_token']
        
        print_colored(f"\n✅ Login exitoso", GREEN)
        print_colored(f"  Token obtenido: {token[:50]}...", YELLOW)
        
        # Probar endpoint protegido
        print_colored(f"\n📤 Probando endpoint protegido...", BLUE)
        
        response_stats = requests.get(
            'http://localhost:2500/api/notas/estadisticas',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            timeout=5
        )
        
        print_colored(f"\n📥 Respuesta:", BLUE)
        print_colored(f"  Status: {response_stats.status_code}", YELLOW)
        
        if response_stats.status_code == 200:
            print_colored(f"\n✅ ¡TOKEN VÁLIDO! Endpoint respondió correctamente", GREEN)
            print_colored(f"  Respuesta: {response_stats.json()}", GREEN)
        elif response_stats.status_code == 401:
            print_colored(f"\n❌ TOKEN INVÁLIDO", RED)
            print_colored(f"  Respuesta: {response_stats.text}", RED)
        else:
            print_colored(f"\n⚠️  Respuesta inesperada: {response_stats.status_code}", YELLOW)
            print_colored(f"  Respuesta: {response_stats.text}", YELLOW)
        
    except requests.exceptions.ConnectionError:
        print_colored(f"\n❌ No se puede conectar al backend", RED)
        print_colored(f"  ¿Está corriendo en http://localhost:2500?", YELLOW)
    except Exception as e:
        print_colored(f"\n❌ Error:", RED)
        print_colored(f"  {str(e)}", RED)


def verificar_archivo_app_py():
    """Verifica el contenido del archivo app.py"""
    print_colored("\n" + "="*60, BLUE)
    print_colored("5. VERIFICANDO ARCHIVO app.py", BLUE)
    print_colored("="*60, BLUE)
    
    app_path = Path('api/app.py')
    
    if not app_path.exists():
        print_colored(f"\n❌ Archivo api/app.py no encontrado", RED)
        return
    
    print_colored(f"\n✅ Archivo encontrado: {app_path}", GREEN)
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Buscar configuración JWT
    if "app.config['JWT_SECRET_KEY']" in content:
        print_colored(f"\n✅ Configuración JWT encontrada en app.py", GREEN)
        
        # Extraer la línea
        for line in content.split('\n'):
            if "JWT_SECRET_KEY" in line and "app.config" in line:
                print_colored(f"  {line.strip()}", YELLOW)
    else:
        print_colored(f"\n❌ No se encontró configuración JWT en app.py", RED)
    
    # Verificar imports
    if "from flask_jwt_extended import" in content:
        print_colored(f"\n✅ Imports de JWT encontrados", GREEN)
    else:
        print_colored(f"\n❌ Imports de JWT no encontrados", RED)
    
    # Verificar decoradores @jwt_required
    jwt_required_count = content.count('@jwt_required')
    print_colored(f"\n📊 Endpoints protegidos: {jwt_required_count}", BLUE)


def main():
    print_colored("\n" + "="*60, BLUE)
    print_colored("  DIAGNÓSTICO COMPLETO - TOKEN JWT", BLUE)
    print_colored("="*60, BLUE)
    
    # 1. Verificar configuración
    jwt_secret = verificar_configuracion_jwt()
    
    # 2. Generar token de prueba
    token_nuevo = test_generar_token(jwt_secret)
    
    # 3. Decodificar token del login
    token_valido = test_decodificar_token_login(jwt_secret)
    
    # 4. Verificar archivo app.py
    verificar_archivo_app_py()
    
    # 5. Probar con el backend real
    test_validacion_backend()
    
    # Resumen
    print_colored("\n" + "="*60, BLUE)
    print_colored("  RESUMEN DEL DIAGNÓSTICO", BLUE)
    print_colored("="*60, BLUE)
    
    if token_valido:
        print_colored(f"\n✅ El token del login es VÁLIDO", GREEN)
        print_colored(f"  Problema probablemente en el código del backend", YELLOW)
    else:
        print_colored(f"\n❌ El token del login NO es válido", RED)
        print_colored(f"  Necesitas hacer login nuevamente", YELLOW)
    
    print_colored(f"\n📝 Recomendaciones:", BLUE)
    print_colored(f"  1. Reinicia el backend completamente", YELLOW)
    print_colored(f"  2. Haz login de nuevo en Postman", YELLOW)
    print_colored(f"  3. Usa el token recién generado", YELLOW)
    print_colored(f"  4. Si sigue fallando, hay un problema en app.py", YELLOW)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n❌ Diagnóstico interrumpido", RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n\n❌ Error inesperado: {e}", RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)
