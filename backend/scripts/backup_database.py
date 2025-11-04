#!/usr/bin/env python3
"""
Script de Backup de Base de Datos
Realiza respaldo de la base de datos SQLite con compresión y limpieza de backups antiguos
"""
import os
import sys
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def crear_backup(db_path: str, backup_dir: str = './backups', comprimir: bool = True) -> str:
    """
    Crea un backup de la base de datos
    
    Args:
        db_path: Ruta de la base de datos
        backup_dir: Directorio donde guardar backups
        comprimir: Si se debe comprimir el backup con gzip
        
    Returns:
        Ruta del archivo de backup creado
    """
    try:
        # Verificar que existe la BD
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        # Crear directorio de backups si no existe
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nombre del archivo de backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"notas_credito_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copiar base de datos
        logger.info(f"Creando backup de {db_path}...")
        shutil.copy2(db_path, backup_path)
        
        # Obtener tamaño
        size_bytes = os.path.getsize(backup_path)
        size_mb = size_bytes / (1024 * 1024)
        
        logger.info(f"Backup creado: {backup_path} ({size_mb:.2f} MB)")
        
        # Comprimir si se solicita
        if comprimir:
            compressed_path = backup_path + '.gz'
            
            logger.info(f"Comprimiendo backup...")
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Eliminar archivo sin comprimir
            os.remove(backup_path)
            
            # Obtener tamaño comprimido
            compressed_size_bytes = os.path.getsize(compressed_path)
            compressed_size_mb = compressed_size_bytes / (1024 * 1024)
            ratio = (1 - compressed_size_bytes / size_bytes) * 100
            
            logger.info(f"Backup comprimido: {compressed_path} ({compressed_size_mb:.2f} MB)")
            logger.info(f"Ratio de compresión: {ratio:.1f}%")
            
            return compressed_path
        
        return backup_path
        
    except Exception as e:
        logger.error(f"Error al crear backup: {e}")
        raise

def limpiar_backups_antiguos(backup_dir: str = './backups', dias_mantener: int = 30):
    """
    Elimina backups más antiguos que el número de días especificado
    
    Args:
        backup_dir: Directorio de backups
        dias_mantener: Días de backups a mantener
    """
    try:
        if not os.path.exists(backup_dir):
            logger.warning(f"Directorio de backups no existe: {backup_dir}")
            return
        
        fecha_limite = datetime.now() - timedelta(days=dias_mantener)
        eliminados = 0
        espacio_liberado = 0
        
        logger.info(f"Limpiando backups anteriores a {fecha_limite.strftime('%Y-%m-%d')}...")
        
        # Buscar archivos de backup
        for archivo in os.listdir(backup_dir):
            if not archivo.startswith('notas_credito_backup_'):
                continue
            
            ruta_completa = os.path.join(backup_dir, archivo)
            
            # Obtener fecha de modificación
            fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
            
            if fecha_mod < fecha_limite:
                size = os.path.getsize(ruta_completa)
                os.remove(ruta_completa)
                eliminados += 1
                espacio_liberado += size
                logger.info(f"  Eliminado: {archivo}")
        
        if eliminados > 0:
            espacio_mb = espacio_liberado / (1024 * 1024)
            logger.info(f"Total eliminados: {eliminados} backups ({espacio_mb:.2f} MB liberados)")
        else:
            logger.info("No hay backups antiguos para eliminar")
            
    except Exception as e:
        logger.error(f"Error al limpiar backups antiguos: {e}")

def listar_backups(backup_dir: str = './backups'):
    """
    Lista todos los backups disponibles
    
    Args:
        backup_dir: Directorio de backups
    """
    try:
        if not os.path.exists(backup_dir):
            logger.warning(f"Directorio de backups no existe: {backup_dir}")
            return
        
        # Buscar archivos de backup
        backups = []
        for archivo in os.listdir(backup_dir):
            if archivo.startswith('notas_credito_backup_'):
                ruta_completa = os.path.join(backup_dir, archivo)
                size = os.path.getsize(ruta_completa)
                fecha_mod = datetime.fromtimestamp(os.path.getmtime(ruta_completa))
                
                backups.append({
                    'nombre': archivo,
                    'ruta': ruta_completa,
                    'size': size,
                    'fecha': fecha_mod
                })
        
        # Ordenar por fecha (más reciente primero)
        backups.sort(key=lambda x: x['fecha'], reverse=True)
        
        if not backups:
            logger.info("No hay backups disponibles")
            return
        
        logger.info(f"\nBackups disponibles ({len(backups)}):")
        logger.info("-" * 80)
        
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            fecha_str = backup['fecha'].strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"{backup['nombre']:50} {size_mb:>8.2f} MB  {fecha_str}")
        
        # Espacio total
        espacio_total = sum(b['size'] for b in backups) / (1024 * 1024)
        logger.info("-" * 80)
        logger.info(f"Espacio total usado: {espacio_total:.2f} MB")
        
    except Exception as e:
        logger.error(f"Error al listar backups: {e}")

def restaurar_backup(backup_path: str, db_path: str):
    """
    Restaura una base de datos desde un backup
    
    Args:
        backup_path: Ruta del archivo de backup
        db_path: Ruta donde restaurar la base de datos
    """
    try:
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup no encontrado: {backup_path}")
        
        # Hacer backup de la BD actual antes de restaurar
        if os.path.exists(db_path):
            backup_actual = db_path + '.before_restore'
            logger.info(f"Guardando BD actual en: {backup_actual}")
            shutil.copy2(db_path, backup_actual)
        
        logger.info(f"Restaurando desde: {backup_path}")
        
        # Si está comprimido, descomprimir
        if backup_path.endswith('.gz'):
            logger.info("Descomprimiendo backup...")
            with gzip.open(backup_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, db_path)
        
        logger.info(f"✅ Base de datos restaurada exitosamente: {db_path}")
        
    except Exception as e:
        logger.error(f"Error al restaurar backup: {e}")
        raise

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Gestión de backups de base de datos SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Crear backup
  python backup_database.py crear
  
  # Crear backup sin comprimir
  python backup_database.py crear --no-comprimir
  
  # Listar backups
  python backup_database.py listar
  
  # Limpiar backups antiguos (mantener últimos 30 días)
  python backup_database.py limpiar
  
  # Limpiar backups antiguos (mantener últimos 90 días)
  python backup_database.py limpiar --dias 90
  
  # Restaurar backup específico
  python backup_database.py restaurar --backup ./backups/notas_credito_backup_20251027_120000.db.gz
        """
    )
    
    parser.add_argument(
        'accion',
        choices=['crear', 'listar', 'limpiar', 'restaurar'],
        help='Acción a realizar'
    )
    
    parser.add_argument(
        '--db-path',
        default='./data/notas_credito.db',
        help='Ruta de la base de datos (default: ./data/notas_credito.db)'
    )
    
    parser.add_argument(
        '--backup-dir',
        default='./backups',
        help='Directorio de backups (default: ./backups)'
    )
    
    parser.add_argument(
        '--no-comprimir',
        action='store_true',
        help='No comprimir el backup'
    )
    
    parser.add_argument(
        '--dias',
        type=int,
        default=30,
        help='Días de backups a mantener al limpiar (default: 30)'
    )
    
    parser.add_argument(
        '--backup',
        help='Ruta del backup a restaurar'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("="*60)
        logger.info(f"GESTIÓN DE BACKUPS - {args.accion.upper()}")
        logger.info("="*60 + "\n")
        
        if args.accion == 'crear':
            backup_path = crear_backup(
                args.db_path,
                args.backup_dir,
                comprimir=not args.no_comprimir
            )
            logger.info(f"\n✅ Backup creado exitosamente: {backup_path}")
            
        elif args.accion == 'listar':
            listar_backups(args.backup_dir)
            
        elif args.accion == 'limpiar':
            limpiar_backups_antiguos(args.backup_dir, args.dias)
            logger.info(f"\n✅ Limpieza completada")
            
        elif args.accion == 'restaurar':
            if not args.backup:
                logger.error("Debe especificar --backup con la ruta del backup a restaurar")
                return 1
            
            restaurar_backup(args.backup, args.db_path)
        
        logger.info("\n" + "="*60)
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
