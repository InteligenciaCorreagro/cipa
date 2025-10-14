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
            
            # Parsear respuesta JSON
            data = response.json()
            
            # Verificar estructura de respuesta SIESA
            if isinstance(data, dict):
                # Verificar si hay error en la respuesta
                if 'codigo' in data and data['codigo'] != 0:
                    logger.error(f"Error en API: {data.get('mensaje', 'Error desconocido')}")
                    raise ValueError(f"Error en API: {data.get('mensaje', 'Error desconocido')}")
                
                # Extraer facturas de la estructura SIESA
                if 'detalle' in data and isinstance(data['detalle'], dict):
                    detalle = data['detalle']
                    
                    # Buscar en Table (estructura SIESA común)
                    if 'Table' in detalle and isinstance(detalle['Table'], list):
                        facturas = detalle['Table']
                        logger.info(f"Se obtuvieron {len(facturas)} facturas")
                        return facturas
                    
                    # Buscar en table (lowercase)
                    if 'table' in detalle and isinstance(detalle['table'], list):
                        facturas = detalle['table']
                        logger.info(f"Se obtuvieron {len(facturas)} facturas")
                        return facturas
                    
                    # Si detalle tiene una lista directa
                    for key in detalle.keys():
                        if isinstance(detalle[key], list):
                            facturas = detalle[key]
                            logger.info(f"Se obtuvieron {len(facturas)} facturas desde clave '{key}'")
                            return facturas
                
                # Buscar directamente en las claves principales
                for key in ['data', 'facturas', 'result', 'rows', 'Table', 'table']:
                    if key in data and isinstance(data[key], list):
                        facturas = data[key]
                        logger.info(f"Se obtuvieron {len(facturas)} facturas desde clave '{key}'")
                        return facturas
                
                # Log de estructura no reconocida
                logger.error(f"Estructura de respuesta no reconocida")
                logger.error(f"Claves principales: {list(data.keys())}")
                if 'detalle' in data:
                    logger.error(f"Claves en 'detalle': {list(data['detalle'].keys()) if isinstance(data['detalle'], dict) else type(data['detalle'])}")
                logger.error(f"Respuesta completa: {json.dumps(data, indent=2)[:1000]}")
                raise ValueError("No se encontraron facturas en la estructura de respuesta")
            
            # Si la respuesta es una lista directamente
            elif isinstance(data, list):
                logger.info(f"Se obtuvieron {len(data)} facturas")
                return data
            
            else:
                logger.error(f"Tipo de respuesta no esperado: {type(data)}")
                raise ValueError(f"Tipo de respuesta no esperado: {type(data)}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al consultar la API: {e}")
            if 'response' in locals():
                logger.error(f"URL: {response.url}")
                logger.error(f"Status: {response.status_code}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON: {e}")
            if 'response' in locals():
                logger.error(f"Respuesta (primeros 500 chars): {response.text[:500]}")
            raise
        except ValueError as e:
            logger.error(f"Error al procesar respuesta: {e}")
            raise