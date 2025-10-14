import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    """Gestiona el envío de correos electrónicos con archivos adjuntos"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def enviar_reporte(
        self,
        destinatarios: List[str],
        archivo_excel: str,
        fecha_reporte: datetime,
        asunto_personalizado: str = None
    ) -> bool:
        """
        Envía el reporte diario por correo electrónico
        
        Args:
            destinatarios: Lista de correos destinatarios
            archivo_excel: Ruta del archivo Excel a adjuntar
            fecha_reporte: Fecha del reporte
            asunto_personalizado: Asunto personalizado (opcional)
            
        Returns:
            True si el envío fue exitoso, False en caso contrario
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(destinatarios)
            
            # Asunto
            if asunto_personalizado:
                msg['Subject'] = asunto_personalizado
            else:
                fecha_str = fecha_reporte.strftime('%d/%m/%Y')
                msg['Subject'] = f'Reporte Diario de Facturas - {fecha_str}'
            
            # Cuerpo del correo
            body = self._generar_cuerpo_email(fecha_reporte)
            msg.attach(MIMEText(body, 'html'))
            
            # Adjuntar archivo Excel
            with open(archivo_excel, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = f"Facturas_{fecha_reporte.strftime('%Y%m%d')}.xlsx"
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
            # Enviar correo
            logger.info(f"Enviando correo a: {', '.join(destinatarios)}")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info("Correo enviado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar correo: {e}")
            return False
    
    def _generar_cuerpo_email(self, fecha_reporte: datetime) -> str:
        """Genera el cuerpo HTML del correo"""
        fecha_str = fecha_reporte.strftime('%d de %B de %Y')
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2c3e50;">Reporte Diario de Facturas</h2>
                <p>Estimado equipo de operaciones,</p>
                <p>Adjunto encontrarán el reporte de facturas correspondiente al día <strong>{fecha_str}</strong>.</p>
                <p>Este reporte ha sido generado automáticamente por el sistema.</p>
                <br>
                <p style="color: #7f8c8d; font-size: 12px;">
                    Este es un correo automático, por favor no responder.
                </p>
            </body>
        </html>
        """
        return html