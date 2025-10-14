import requests
from datetime import datetime, timedelta
from typing import List, Dict
import logging
import json

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
            
            # Intentar parsear la respuesta
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Si falla, intentar parsear el texto como JSON
                logger.warning("Respuesta no es JSON válido, intentando parsear texto")
                data = json.loads(response.text)
            
            # Verificar si la respuesta es una lista
            if isinstance(data, list):
                logger.info(f"Se obtuvieron {len(data)} facturas")
                return data
            
            # Si es un diccionario, buscar la lista dentro
            elif isinstance(data, dict):
                # Intentar diferentes claves comunes
                for key in ['data', 'facturas', 'result', 'rows']:
                    if key in data and isinstance(data[key], list):
                        logger.info(f"Se obtuvieron {len(data[key])} facturas desde clave '{key}'")
                        return data[key]
                
                # Si el diccionario tiene una sola clave, devolver su valor
                if len(data) == 1:
                    value = list(data.values())[0]
                    if isinstance(value, list):
                        logger.info(f"Se obtuvieron {len(value)} facturas")
                        return value
                
                logger.error(f"Estructura de respuesta no reconocida: {list(data.keys())}")
                raise ValueError("Estructura de respuesta no reconocida")
            
            # Si es un string, intentar parsearlo
            elif isinstance(data, str):
                logger.warning("Respuesta es string, intentando parsear")
                parsed_data = json.loads(data)
                if isinstance(parsed_data, list):
                    logger.info(f"Se obtuvieron {len(parsed_data)} facturas")
                    return parsed_data
                else:
                    return self.obtener_facturas_from_dict(parsed_data)
            
            else:
                logger.error(f"Tipo de respuesta no esperado: {type(data)}")
                raise ValueError(f"Tipo de respuesta no esperado: {type(data)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al consultar la API: {e}")
            logger.error(f"URL: {response.url if 'response' in locals() else 'N/A'}")
            logger.error(f"Status: {response.status_code if 'response' in locals() else 'N/A'}")
            raise
        except ValueError as e:
            logger.error(f"Error al procesar respuesta: {e}")
            # Imprimir los primeros 500 caracteres de la respuesta para debug
            if 'response' in locals():
                logger.error(f"Respuesta (primeros 500 chars): {response.text[:500]}")
            raise
    
    def obtener_facturas_from_dict(self, data: dict) -> List[Dict]:
        """Helper method para extraer facturas de un diccionario"""
        for key in ['data', 'facturas', 'result', 'rows']:
            if key in data and isinstance(data[key], list):
                logger.info(f"Se obtuvieron {len(data[key])} facturas desde clave '{key}'")
                return data[key]
        
        # Si hay una sola clave, devolver su valor
        if len(data) == 1:
            value = list(data.values())[0]
            if isinstance(value, list):
                logger.info(f"Se obtuvieron {len(value)} facturas")
                return value
        
        logger.error(f"No se encontró lista de facturas en: {list(data.keys())}")
        raise ValueError("No se encontró lista de facturas en la respuesta")