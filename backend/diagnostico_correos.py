#!/usr/bin/env python3
"""
Script de Diagnóstico y Prueba de Correos Diarios
=================================================

Este script verifica la configuración de correos y permite probar el envío.

IMPORTANTE: Para usar Gmail, necesitas:
1. Una "App Password" (no tu contraseña normal)
2. Verificación en 2 pasos activada
3. Generar App Password en: https://myaccount.google.com/apppasswords

Para Outlook/Office365:
- SMTP_SERVER: smtp.office365.com
- SMTP_PORT: 587
- Usar contraseña normal o App Password
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Agregar el directorio al path
sys.path.insert(0, os.path.dirname(__file__))

from core.email_sender import EmailSender
from core.excel_processor import ExcelProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verificar_configuracion():
    """Verifica que todas las variables de entorno estén configuradas"""

    print("\n" + "="*80)
    print("VERIFICACIÓN DE CONFIGURACIÓN DE CORREOS")
    print("="*80 + "\n")

    # Cargar variables de entorno
    load_dotenv()

    config = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
        'DESTINATARIOS': os.getenv('DESTINATARIOS')
    }

    # Verificar cada variable
    problemas = []

    print("📋 Variables de Entorno:")
    print("-" * 80)

    for key, value in config.items():
        if value:
            if key == 'EMAIL_PASSWORD':
                # Ocultar contraseña
                masked_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
                print(f"  ✅ {key}: {masked_value}")
            elif key == 'DESTINATARIOS':
                destinatarios = value.split(',')
                print(f"  ✅ {key}: {len(destinatarios)} destinatario(s)")
                for i, dest in enumerate(destinatarios, 1):
                    print(f"      {i}. {dest.strip()}")
            else:
                print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: NO CONFIGURADO")
            problemas.append(key)

    print("\n" + "="*80)

    if problemas:
        print("\n⚠️  PROBLEMAS ENCONTRADOS:\n")
        for problema in problemas:
            print(f"  ❌ Variable {problema} no está configurada")

        print("\n💡 SOLUCIÓN:")
        print("  1. Copia el archivo .env.example a .env")
        print("  2. Edita .env con tus credenciales reales")
        print("  3. Si usas Gmail, crea una 'App Password':")
        print("     https://myaccount.google.com/apppasswords")
        print("\n  Para GitHub Actions, configura los secretos en:")
        print("  https://github.com/TU_USUARIO/TU_REPO/settings/secrets/actions")
        print()
        return False

    return True


def crear_excel_prueba():
    """Crea un Excel de prueba para adjuntar"""

    print("\n📄 Generando Excel de prueba...")

    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"prueba_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

    # Crear datos de prueba
    facturas_prueba = [
        {
            'numero_factura': 'FEM001-PRUEBA',
            'fecha_factura': datetime.now().strftime('%Y-%m-%d'),
            'nit_comprador': '900123456',
            'nombre_comprador': 'CLIENTE DE PRUEBA S.A.S.',
            'codigo_producto': 'PROD-TEST-001',
            'nombre_producto': 'Producto de Prueba para Test de Email',
            'cantidad': 100,
            'precio_unitario': 5000,
            'valor_total': 500000,
            'descripcion': 'PRUEBA - PRODUCTO TERMINADO'
        },
        {
            'numero_factura': 'FEM002-PRUEBA',
            'fecha_factura': datetime.now().strftime('%Y-%m-%d'),
            'nit_comprador': '800987654',
            'nombre_comprador': 'OTRA EMPRESA DE PRUEBA LTDA',
            'codigo_producto': 'PROD-TEST-002',
            'nombre_producto': 'Segundo Producto de Prueba',
            'cantidad': 50,
            'precio_unitario': 10000,
            'valor_total': 500000,
            'descripcion': 'PRUEBA - MATERIA PRIMA'
        }
    ]

    try:
        processor = ExcelProcessor()
        processor.generar_excel(facturas_prueba, output_path)
        print(f"  ✅ Excel creado: {output_path}")
        return output_path
    except Exception as e:
        print(f"  ❌ Error creando Excel: {e}")
        return None


def probar_envio_correo(modo='test'):
    """
    Prueba el envío de correo

    Args:
        modo: 'test' para correo de prueba, 'real' para correo con datos reales
    """

    print("\n" + "="*80)
    print(f"PRUEBA DE ENVÍO DE CORREO - Modo: {modo.upper()}")
    print("="*80 + "\n")

    # Cargar configuración
    load_dotenv()

    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    destinatarios_str = os.getenv('DESTINATARIOS', '')
    destinatarios = [d.strip() for d in destinatarios_str.split(',') if d.strip()]

    if not all([email_username, email_password, destinatarios]):
        print("❌ Configuración incompleta. Ejecuta primero la verificación.")
        return False

    # Crear Excel de prueba
    excel_path = crear_excel_prueba()
    if not excel_path:
        print("❌ No se pudo crear el Excel de prueba")
        return False

    # Configurar EmailSender
    print(f"\n📧 Configurando envío:")
    print(f"  • Servidor SMTP: {smtp_server}:{smtp_port}")
    print(f"  • Usuario: {email_username}")
    print(f"  • Destinatarios: {len(destinatarios)}")
    for i, dest in enumerate(destinatarios, 1):
        print(f"      {i}. {dest}")

    try:
        email_sender = EmailSender(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=email_username,
            password=email_password
        )

        print("\n🚀 Enviando correo...")
        print("  (Esto puede tardar unos segundos...)\n")

        asunto = f"[PRUEBA] Correo de Prueba - Sistema CIPA - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        exito = email_sender.enviar_reporte(
            destinatarios=destinatarios,
            archivo_excel=excel_path,
            fecha_reporte=datetime.now(),
            asunto_personalizado=asunto
        )

        if exito:
            print("="*80)
            print("✅ ¡CORREO ENVIADO EXITOSAMENTE!")
            print("="*80)
            print("\n📬 Verifica tu bandeja de entrada:")
            for dest in destinatarios:
                print(f"  • {dest}")
            print("\n💡 Si no ves el correo:")
            print("  1. Revisa la carpeta de SPAM/Correo no deseado")
            print("  2. Espera unos minutos (puede haber demora)")
            print("  3. Verifica que la dirección de correo sea correcta")
            print()
            return True
        else:
            print("="*80)
            print("❌ ERROR AL ENVIAR CORREO")
            print("="*80)
            print("\n💡 Posibles causas:")
            print("  1. Contraseña incorrecta")
            print("  2. Gmail: necesitas usar 'App Password' (no contraseña normal)")
            print("  3. Servidor SMTP incorrecto o puerto bloqueado")
            print("  4. Firewall bloqueando la conexión")
            print()
            return False

    except Exception as e:
        print("="*80)
        print("❌ EXCEPCIÓN AL ENVIAR CORREO")
        print("="*80)
        print(f"\nError: {str(e)}")
        print("\n💡 Soluciones comunes:")

        error_str = str(e).lower()

        if 'authentication' in error_str or 'username' in error_str or 'password' in error_str:
            print("\n🔐 PROBLEMA DE AUTENTICACIÓN:")
            print("  • Para Gmail:")
            print("    1. Ve a https://myaccount.google.com/apppasswords")
            print("    2. Activa verificación en 2 pasos si no está activa")
            print("    3. Genera una 'App Password' para 'Correo'")
            print("    4. Usa esa contraseña en EMAIL_PASSWORD (no tu contraseña normal)")
            print("\n  • Para Outlook/Office365:")
            print("    - Servidor: smtp.office365.com")
            print("    - Puerto: 587")
            print("    - Puede requerir autenticación moderna")

        elif 'connection' in error_str or 'timeout' in error_str:
            print("\n🌐 PROBLEMA DE CONEXIÓN:")
            print("  • Verifica tu conexión a internet")
            print("  • El puerto 587 puede estar bloqueado por firewall")
            print("  • Intenta con puerto 465 (SSL) o 25 (si está permitido)")

        elif 'recipient' in error_str:
            print("\n📧 PROBLEMA CON DESTINATARIOS:")
            print("  • Verifica que los correos en DESTINATARIOS sean válidos")
            print("  • Asegúrate de separarlos con comas sin espacios extras")

        print()
        import traceback
        traceback.print_exc()
        return False


def mostrar_menu():
    """Muestra el menú de opciones"""

    print("\n" + "="*80)
    print("DIAGNÓSTICO DE CORREOS DIARIOS - Sistema CIPA")
    print("="*80)
    print("\nOpciones:")
    print("  1. Verificar configuración de correos")
    print("  2. Probar envío de correo (con Excel de prueba)")
    print("  3. Ver instrucciones para GitHub Actions")
    print("  4. Ver instrucciones para Gmail App Password")
    print("  5. Salir")
    print("\n" + "="*80)


def mostrar_instrucciones_github():
    """Muestra instrucciones para configurar GitHub Actions"""

    print("\n" + "="*80)
    print("CONFIGURACIÓN DE GITHUB ACTIONS")
    print("="*80)
    print("""
Para que los correos se envíen automáticamente desde GitHub Actions:

1. Ve a tu repositorio en GitHub
2. Click en "Settings" (Configuración)
3. En el menú lateral: "Secrets and variables" → "Actions"
4. Click en "New repository secret" para cada variable:

   Nombre del Secret          | Valor
   ─────────────────────────────────────────────────────────
   SMTP_SERVER               | smtp.gmail.com (o tu servidor)
   SMTP_PORT                 | 587
   EMAIL_USERNAME            | tu_email@gmail.com
   EMAIL_PASSWORD            | tu_app_password_aquí
   DESTINATARIOS             | email1@example.com,email2@example.com

5. También necesitas los secrets para la API:
   CONNI_KEY                 | tu_conni_key
   CONNI_TOKEN               | tu_conni_token

6. El workflow en .github/workflows/daily_process.yml se ejecutará:
   - Automáticamente todos los días a las 8:00 AM (hora Bogotá)
   - Manualmente desde la pestaña "Actions" → "Proceso Diario" → "Run workflow"

7. Para ver los logs:
   - Ve a la pestaña "Actions"
   - Click en la ejecución más reciente
   - Revisa los logs para ver si el correo se envió
    """)


def mostrar_instrucciones_gmail():
    """Muestra instrucciones para crear App Password en Gmail"""

    print("\n" + "="*80)
    print("CÓMO CREAR APP PASSWORD EN GMAIL")
    print("="*80)
    print("""
Gmail requiere una "App Password" para aplicaciones de terceros:

1. Ve a tu cuenta de Google: https://myaccount.google.com

2. En el menú lateral, busca "Seguridad"

3. Activa la "Verificación en 2 pasos" (si no está activada):
   - Es requisito para crear App Passwords
   - Sigue las instrucciones en pantalla

4. Una vez activada la verificación en 2 pasos:
   - Vuelve a "Seguridad"
   - Busca "Contraseñas de aplicaciones" o ve directo a:
     https://myaccount.google.com/apppasswords

5. Genera una nueva App Password:
   - Selecciona "Correo" como app
   - Selecciona "Otro" como dispositivo
   - Ponle un nombre: "Sistema CIPA" o similar
   - Click en "Generar"

6. Google te mostrará una contraseña de 16 caracteres
   - Ejemplo: "abcd efgh ijkl mnop"
   - ¡CÓPIALA AHORA! No la volverás a ver

7. Usa esa contraseña en EMAIL_PASSWORD
   - Puedes incluir o quitar los espacios, funciona igual
   - Esta es tu contraseña para el sistema, NO tu contraseña de Gmail normal

8. IMPORTANTE:
   - NUNCA uses tu contraseña normal de Gmail
   - Cada App Password es única y revocable
   - Si crees que se comprometió, revócala y crea una nueva

💡 Alternativa: Usar un servicio de correo empresarial
   - Outlook/Office365: smtp.office365.com:587
   - Amazon SES: email-smtp.us-east-1.amazonaws.com:587
   - SendGrid, Mailgun, etc.
    """)


def main():
    """Función principal del menú interactivo"""

    while True:
        mostrar_menu()

        try:
            opcion = input("\nSelecciona una opción (1-5): ").strip()

            if opcion == '1':
                if verificar_configuracion():
                    print("\n✅ Configuración correcta. Puedes probar el envío de correo (opción 2)")
                else:
                    print("\n⚠️  Corrige la configuración antes de continuar")

            elif opcion == '2':
                if verificar_configuracion():
                    confirmar = input("\n⚠️  Esto enviará un correo de prueba. ¿Continuar? (s/n): ").strip().lower()
                    if confirmar == 's':
                        probar_envio_correo('test')
                    else:
                        print("Operación cancelada")
                else:
                    print("\n❌ Primero configura las variables de entorno")

            elif opcion == '3':
                mostrar_instrucciones_github()

            elif opcion == '4':
                mostrar_instrucciones_gmail()

            elif opcion == '5':
                print("\n👋 ¡Hasta luego!\n")
                break

            else:
                print("\n❌ Opción inválida. Selecciona 1-5")

        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == '__main__':
    main()
