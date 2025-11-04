#!/usr/bin/env python3
"""
Script de Verificación de Configuración
Valida que todos los componentes están correctamente configurados antes de ejecutar el proceso principal
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

def print_header(text):
    """Imprime encabezado con formato"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_check(condition, message):
    """Imprime resultado de verificación"""
    status = "✅" if condition else "❌"
    print(f"{status} {message}")
    return condition

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno requeridas estén configuradas"""
    print_header("VERIFICACIÓN DE VARIABLES DE ENTORNO")
    
    # Cargar .env
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("   Copie .env.example a .env y configure los valores")
        return False
    
    print("✅ Archivo .env encontrado")
    load_dotenv()
    
    # Variables requeridas
    variables_requeridas = {
        'CONNI_KEY': 'Clave de API SIESA',
        'CONNI_TOKEN': 'Token de API SIESA',
        'EMAIL_USERNAME': 'Usuario de correo',
        'EMAIL_PASSWORD': 'Contraseña de correo',
        'DESTINATARIOS': 'Lista de destinatarios'
    }
    
    todas_ok = True
    for var, descripcion in variables_requeridas.items():
        valor = os.getenv(var)
        if valor:
            print(f"✅ {descripcion} ({var}): {'*' * min(len(valor), 10)}")
        else:
            print(f"❌ {descripcion} ({var}): NO CONFIGURADO")
            todas_ok = False
    
    # Variables opcionales
    print("\nVariables opcionales:")
    print(f"  SMTP_SERVER: {os.getenv('SMTP_SERVER', 'smtp.gmail.com (default)')}")
    print(f"  SMTP_PORT: {os.getenv('SMTP_PORT', '587 (default)')}")
    print(f"  DB_PATH: {os.getenv('DB_PATH', './data/notas_credito.db (default)')}")
    
    return todas_ok

def verificar_dependencias():
    """Verifica que todas las dependencias Python estén instaladas"""
    print_header("VERIFICACIÓN DE DEPENDENCIAS")
    
    dependencias = {
        'requests': 'requests',
        'openpyxl': 'openpyxl',
        'dotenv': 'python-dotenv'
    }
    
    todas_ok = True
    for modulo, paquete in dependencias.items():
        try:
            __import__(modulo)
            print(f"✅ {paquete}")
        except ImportError:
            print(f"❌ {paquete} - NO INSTALADO")
            todas_ok = False
    
    if not todas_ok:
        print("\nPara instalar dependencias faltantes:")
        print("  pip install -r requirements.txt")
    
    return todas_ok

def verificar_estructura_directorios():
    """Verifica que exista la estructura de directorios necesaria"""
    print_header("VERIFICACIÓN DE ESTRUCTURA DE DIRECTORIOS")
    
    directorios = ['data', 'output', 'src', 'templates']
    
    todas_ok = True
    for directorio in directorios:
        existe = os.path.exists(directorio)
        print_check(existe, f"Directorio '{directorio}/'")
        
        if not existe:
            print(f"   Creando directorio '{directorio}/'...")
            os.makedirs(directorio, exist_ok=True)
            todas_ok = True  # No es crítico, lo creamos
    
    return todas_ok

def verificar_modulos():
    """Verifica que todos los módulos del sistema existan"""
    print_header("VERIFICACIÓN DE MÓDULOS DEL SISTEMA")
    
    modulos = [
        'src/api_client.py',
        'src/business_rules.py',
        'src/notas_credito_manager.py',
        'src/excel_processor.py',
        'src/email_sender.py'
    ]
    
    todas_ok = True
    for modulo in modulos:
        existe = os.path.exists(modulo)
        print_check(existe, modulo)
        todas_ok = todas_ok and existe
    
    return todas_ok

def probar_api():
    """Prueba la conexión con la API de SIESA"""
    print_header("PRUEBA DE CONEXIÓN API SIESA")
    
    load_dotenv()
    conni_key = os.getenv('CONNI_KEY')
    conni_token = os.getenv('CONNI_TOKEN')
    
    if not conni_key or not conni_token:
        print("❌ Credenciales de API no configuradas")
        return False
    
    try:
        import requests
        from datetime import datetime, timedelta
        
        # Probar con fecha de ayer
        fecha = datetime.now() - timedelta(days=1)
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        url = "https://siesaprod.cipa.com.co/produccion/v3/ejecutarconsulta"
        headers = {
            "Connikey": conni_key,
            "conniToken": conni_token,
            "Content-Type": "application/json"
        }
        params = {
            "idCompania": "37",
            "descripcion": "Api_Consulta_Fac_Correagro",
            "parametros": f"FECHA_INI='{fecha_str}'|FECHA_FIN='{fecha_str}'"
        }
        
        print(f"Probando conexión para fecha: {fecha_str}...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Conexión exitosa (Status: {response.status_code})")
            
            data = response.json()
            print(f"✅ Respuesta JSON válida")
            
            # Intentar contar facturas
            if isinstance(data, dict) and 'detalle' in data:
                print("✅ Estructura de respuesta reconocida")
                return True
            elif isinstance(data, list):
                print(f"✅ {len(data)} registros en respuesta")
                return True
            else:
                print("⚠️  Estructura de respuesta diferente a lo esperado")
                return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - No se pudo conectar en 10 segundos")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - Verificar red/firewall")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def probar_email():
    """Prueba la conexión SMTP"""
    print_header("PRUEBA DE CONEXIÓN EMAIL")
    
    load_dotenv()
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not username or not password:
        print("❌ Credenciales de email no configuradas")
        return False
    
    try:
        import smtplib
        
        print(f"Probando conexión a {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            print("✅ Conexión establecida")
            
            server.starttls()
            print("✅ TLS iniciado")
            
            server.login(username, password)
            print("✅ Autenticación exitosa")
            
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación")
        print("   Si usa Gmail, asegúrese de usar 'Contraseña de Aplicación'")
        print("   Ver: https://support.google.com/accounts/answer/185833")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def probar_base_datos():
    """Prueba la creación y acceso a la base de datos"""
    print_header("PRUEBA DE BASE DE DATOS")
    
    load_dotenv()
    db_path = os.getenv('DB_PATH', './data/notas_credito.db')
    
    try:
        import sqlite3
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Probar conexión
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conexión a BD exitosa: {db_path}")
        
        # Verificar si ya hay datos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        if tablas:
            print(f"✅ Base de datos ya inicializada ({len(tablas)} tablas)")
            
            # Contar notas
            cursor.execute("SELECT COUNT(*) FROM notas_credito")
            total_notas = cursor.fetchone()[0]
            print(f"   - Notas crédito registradas: {total_notas}")
            
            cursor.execute("SELECT COUNT(*) FROM aplicaciones_notas")
            total_aplicaciones = cursor.fetchone()[0]
            print(f"   - Aplicaciones registradas: {total_aplicaciones}")
        else:
            print("⚠️  Base de datos vacía (se inicializará en primera ejecución)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("\n" + "="*60)
    print("  VERIFICACIÓN DE CONFIGURACIÓN DEL SISTEMA")
    print("  Sistema de Gestión de Facturas v2.0")
    print("="*60)
    
    resultados = {
        'Variables de Entorno': verificar_variables_entorno(),
        'Dependencias Python': verificar_dependencias(),
        'Estructura de Directorios': verificar_estructura_directorios(),
        'Módulos del Sistema': verificar_modulos(),
        'Base de Datos': probar_base_datos(),
    }
    
    # Pruebas de conectividad (opcionales)
    print("\n" + "="*60)
    print("  PRUEBAS DE CONECTIVIDAD (Opcional)")
    print("="*60)
    
    respuesta = input("\n¿Desea probar la conexión con la API SIESA? (s/N): ").lower()
    if respuesta == 's':
        resultados['Conexión API'] = probar_api()
    
    respuesta = input("\n¿Desea probar la conexión SMTP de email? (s/N): ").lower()
    if respuesta == 's':
        resultados['Conexión Email'] = probar_email()
    
    # Resumen
    print_header("RESUMEN DE VERIFICACIÓN")
    
    exitosas = sum(1 for v in resultados.values() if v)
    total = len(resultados)
    
    for nombre, resultado in resultados.items():
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{status} - {nombre}")
    
    print(f"\nTotal: {exitosas}/{total} verificaciones pasaron")
    
    if exitosas == total:
        print("\n🎉 ¡SISTEMA LISTO PARA EJECUTAR!")
        print("\nPróximos pasos:")
        print("  1. Ejecutar: python test_sistema.py")
        print("  2. Si los tests pasan, ejecutar: python main.py")
        return 0
    else:
        print(f"\n⚠️  {total - exitosas} verificación(es) fallaron")
        print("\nPor favor corrija los errores antes de ejecutar el sistema")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación cancelada por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
