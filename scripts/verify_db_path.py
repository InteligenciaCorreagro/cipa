#!/usr/bin/env python3
"""
Script para verificar que todos los componentes usen la misma base de datos
"""
import os
import sys
from pathlib import Path

def main():
    """Verificar configuración de base de datos"""

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"\n{'='*60}")
    print(f"🔍 VERIFICACIÓN DE CONFIGURACIÓN DE BASE DE DATOS")
    print(f"{'='*60}\n")

    print(f"📁 Directorio del proyecto: {project_root}")

    # Verificar que exista data/notas_credito.db
    db_path = project_root / 'data' / 'notas_credito.db'

    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"✅ Base de datos encontrada: {db_path}")
        print(f"   Tamaño: {size_mb:.2f} MB")
    else:
        print(f"❌ Base de datos NO encontrada en: {db_path}")
        print(f"   La base de datos se creará automáticamente al ejecutar el proceso.")

    # Verificar que NO exista backend/data/notas_credito.db
    old_db_path = project_root / 'backend' / 'data' / 'notas_credito.db'

    if old_db_path.exists():
        print(f"\n⚠️  ADVERTENCIA: Encontrada base de datos duplicada en:")
        print(f"   {old_db_path}")
        print(f"   Esta NO se debería usar. Elimínala con:")
        print(f"   rm {old_db_path}")
    else:
        print(f"\n✅ No hay bases de datos duplicadas en backend/data/")

    # Verificar variables de entorno
    print(f"\n{'='*60}")
    print(f"📝 VARIABLES DE ENTORNO")
    print(f"{'='*60}\n")

    from dotenv import load_dotenv
    load_dotenv()

    db_path_env = os.getenv('DB_PATH')

    if db_path_env:
        print(f"✅ DB_PATH configurado: {db_path_env}")

        if db_path_env == './data/notas_credito.db':
            print(f"   ✅ Ruta correcta")
        elif 'backend/data' in db_path_env:
            print(f"   ❌ ERROR: Apunta a backend/data/")
            print(f"   Cambia en .env a: DB_PATH=./data/notas_credito.db")
        else:
            print(f"   ⚠️  Ruta personalizada detectada")
    else:
        print(f"⚠️  DB_PATH no configurado en .env")
        print(f"   Se usará el valor por defecto: ./data/notas_credito.db")

    # Verificar .env existe
    env_file = project_root / '.env'
    if env_file.exists():
        print(f"\n✅ Archivo .env encontrado")
    else:
        print(f"\n⚠️  Archivo .env NO encontrado")
        print(f"   Crea uno copiando .env.example:")
        print(f"   cp .env.example .env")

    print(f"\n{'='*60}")
    print(f"📋 RESUMEN")
    print(f"{'='*60}\n")

    issues = []

    if not db_path.exists():
        issues.append("Base de datos no existe (se creará automáticamente)")

    if old_db_path.exists():
        issues.append("⚠️  Base de datos duplicada en backend/data/")

    if not env_file.exists():
        issues.append("Archivo .env no existe")

    if db_path_env and 'backend/data' in db_path_env:
        issues.append("❌ DB_PATH apunta a ubicación incorrecta")

    if issues:
        print(f"⚠️  Problemas encontrados:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"✅ Configuración correcta!")
        print(f"   Todos los componentes usarán: {db_path}")

    print(f"\n{'='*60}\n")

    return 0 if not any('❌' in i for i in issues) else 1

if __name__ == '__main__':
    sys.exit(main())
