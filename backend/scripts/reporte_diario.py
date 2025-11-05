#!/usr/bin/env python3
"""
Reporte Diario desde Base de Datos
Genera y envía reportes consultando únicamente la base de datos SQLite
No requiere procesar facturas desde la API
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from core.notas_credito_manager import NotasCreditoManager
from core.email_sender import EmailSender

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generar_reporte_html(manager: NotasCreditoManager, dias: int = 7) -> str:
    """
    Genera un reporte HTML completo del estado del sistema
    
    Args:
        manager: Gestor de notas crédito
        dias: Días hacia atrás para estadísticas
        
    Returns:
        HTML del reporte
    """
    # Obtener datos
    resumen_notas = manager.obtener_resumen_notas()
    resumen_rechazos = manager.obtener_resumen_rechazos(dias=dias)
    tipos_nuevos = manager.obtener_tipos_inventario_nuevos(dias=30)
    
    # Fecha del reporte
    fecha_reporte = datetime.now().strftime('%d de %B de %Y')
    
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 5px;
            }}
            .summary-box {{
                background-color: #ecf0f1;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 15px 0;
            }}
            .alert-box {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 15px 0;
            }}
            .success-box {{
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 15px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th {{
                background-color: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .metric {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #7f8c8d;
                font-size: 12px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>📊 Reporte del Sistema de Gestión de Facturas</h1>
        <p><strong>Fecha:</strong> {fecha_reporte}</p>
        <p><strong>Período analizado:</strong> Últimos {dias} días</p>
        
        <h2>📋 Estado de Notas Crédito</h2>
        <div class="summary-box">
            <table style="border: none;">
                <tr>
                    <td style="border: none;"><strong>Notas crédito pendientes:</strong></td>
                    <td style="border: none;" class="metric">{resumen_notas.get('notas_pendientes', 0)}</td>
                </tr>
                <tr>
                    <td style="border: none;"><strong>Saldo pendiente total:</strong></td>
                    <td style="border: none;" class="metric">${resumen_notas.get('saldo_pendiente_total', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="border: none;"><strong>Notas aplicadas (histórico):</strong></td>
                    <td style="border: none;">{resumen_notas.get('notas_aplicadas', 0)}</td>
                </tr>
                <tr>
                    <td style="border: none;"><strong>Total aplicaciones:</strong></td>
                    <td style="border: none;">{resumen_notas.get('total_aplicaciones', 0)}</td>
                </tr>
                <tr>
                    <td style="border: none;"><strong>Monto total aplicado:</strong></td>
                    <td style="border: none;">${resumen_notas.get('monto_total_aplicado', 0):,.2f}</td>
                </tr>
            </table>
        </div>
        
        <h2>❌ Facturas Rechazadas (Últimos {dias} días)</h2>
        <div class="summary-box">
            <table style="border: none;">
                <tr>
                    <td style="border: none;"><strong>Total facturas rechazadas:</strong></td>
                    <td style="border: none;" class="metric">{resumen_rechazos.get('total_rechazos', 0)}</td>
                </tr>
                <tr>
                    <td style="border: none;"><strong>Valor total rechazado:</strong></td>
                    <td style="border: none;" class="metric">${resumen_rechazos.get('valor_total_rechazado', 0):,.2f}</td>
                </tr>
            </table>
        </div>
    """
    
    # Rechazos por razón
    por_razon = resumen_rechazos.get('por_razon', [])
    if por_razon:
        html += """
        <h3>Rechazos por Razón</h3>
        <table>
            <tr>
                <th>Razón</th>
                <th>Cantidad</th>
                <th>Valor Total</th>
            </tr>
        """
        for item in por_razon:
            html += f"""
            <tr>
                <td>{item['razon']}</td>
                <td>{item['cantidad']}</td>
                <td>${item['valor']:,.2f}</td>
            </tr>
            """
        html += "</table>"
    
    # Tipos más rechazados
    tipos_rechazados = resumen_rechazos.get('tipos_mas_rechazados', [])
    if tipos_rechazados:
        html += """
        <h3>Tipos de Inventario Más Rechazados</h3>
        <table>
            <tr>
                <th>Tipo de Inventario</th>
                <th>Cantidad</th>
            </tr>
        """
        for item in tipos_rechazados:
            html += f"""
            <tr>
                <td>{item['tipo']}</td>
                <td>{item['cantidad']}</td>
            </tr>
            """
        html += "</table>"
    
    # Tipos nuevos detectados
    if tipos_nuevos:
        html += f"""
        <h2>⚠️ Tipos de Inventario Nuevos Detectados</h2>
        <div class="alert-box">
            <p><strong>Se detectaron {len(tipos_nuevos)} tipos de inventario nuevos en los últimos 30 días.</strong></p>
            <p>Considere revisar si deben agregarse a la lista de excluidos.</p>
        </div>
        <table>
            <tr>
                <th>Código</th>
                <th>Descripción</th>
                <th>Total Facturas</th>
                <th>Primera Detección</th>
            </tr>
        """
        for tipo in tipos_nuevos:
            fecha = tipo['primera_deteccion'][:10] if tipo.get('primera_deteccion') else 'N/A'
            html += f"""
            <tr>
                <td><strong>{tipo['codigo_tipo']}</strong></td>
                <td>{tipo.get('descripcion', 'N/A')}</td>
                <td>{tipo['total_facturas']}</td>
                <td>{fecha}</td>
            </tr>
            """
        html += "</table>"
    else:
        html += """
        <h2>✅ Tipos de Inventario</h2>
        <div class="success-box">
            <p><strong>No se detectaron tipos de inventario nuevos en los últimos 30 días.</strong></p>
        </div>
        """
    
    html += """
        <div class="footer">
            <p>Este es un reporte automático generado por el Sistema de Gestión de Facturas CIPA.</p>
            <p>Por favor no responder a este correo.</p>
        </div>
    </body>
    </html>
    """
    
    return html

def main():
    """Función principal del reporte diario"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Configuración
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
        EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
        DESTINATARIOS = os.getenv('DESTINATARIOS').split(',')
        DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')
        
        # Validar configuración
        if not all([EMAIL_USERNAME, EMAIL_PASSWORD]):
            raise ValueError("Faltan variables de entorno de email requeridas")
        
        logger.info(f"{'='*60}")
        logger.info(f"Generando reporte diario desde base de datos")
        logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}")
        
        # Verificar que existe la base de datos
        if not os.path.exists(DB_PATH):
            logger.error(f"Base de datos no encontrada: {DB_PATH}")
            logger.error("Ejecute el proceso principal al menos una vez para crear la BD")
            return
        
        # Inicializar gestor de notas
        manager = NotasCreditoManager(DB_PATH)
        
        # Generar reporte HTML
        logger.info("Generando reporte HTML...")
        html_reporte = generar_reporte_html(manager, dias=7)
        
        # Guardar reporte HTML en archivo
        fecha_str = datetime.now().strftime('%Y%m%d')
        reporte_path = os.path.join('./output', f'reporte_diario_{fecha_str}.html')
        os.makedirs('./output', exist_ok=True)
        
        with open(reporte_path, 'w', encoding='utf-8') as f:
            f.write(html_reporte)
        
        logger.info(f"Reporte HTML generado: {reporte_path}")
        
        # Enviar correo
        email_sender = EmailSender(
            SMTP_SERVER,
            SMTP_PORT,
            EMAIL_USERNAME,
            EMAIL_PASSWORD
        )
        
        # Crear mensaje
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['To'] = ', '.join(DESTINATARIOS)
        msg['Subject'] = f'Reporte Diario del Sistema - {datetime.now().strftime("%d/%m/%Y")}'
        
        msg.attach(MIMEText(html_reporte, 'html'))
        
        # Enviar
        logger.info(f"Enviando reporte a: {', '.join(DESTINATARIOS)}")
        
        import smtplib
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info("✅ Reporte enviado exitosamente")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error en el proceso de reporte: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
