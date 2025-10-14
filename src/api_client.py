import requests
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SiesaAPIClient:
    """Cliente para interactuar con la API de SIESA"""
    
    BASE_URL = "https://siesaprod.cipa.com.co/produccion/v3/ejecutarconsulta"
    
    def __init__(self, conni_key: str, conni_token: str):
        self.headers = {
            "Connikey": conni_key,
            "conniToken": conni_token,
            "Content-Type": "application/json"
        }
    
    def obtener_facturas(self, fecha: datetime) -> List[Dict]:
        """
        Obtiene las facturas para una fecha específica
        
        Args:
            fecha: Fecha para consultar las facturas
            
        Returns:
            Lista de facturas en formato JSON
        """
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        params = {
            "idCompania": "37",
            "descripcion": "Api_Consulta_Fac_Correagro",
            "parametros": f"FECHA_INI='{fecha_str}'|FECHA_FIN='{fecha_str}'"
        }
        
        try:
            logger.info(f"Consultando facturas para la fecha: {fecha_str}")
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Se obtuvieron {len(data)} facturas")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al consultar la API: {e}")
            raise
        except ValueError as e:
            logger.error(f"Error al parsear JSON: {e}")
            raise