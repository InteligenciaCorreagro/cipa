import argparse
import os
import shutil
from datetime import datetime, timedelta


def crear_backup(db_path: str, backup_dir: str):
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(backup_dir, f'notas_credito_{timestamp}.db')
    shutil.copy2(db_path, dest)
    return dest


def limpiar_backups(backup_dir: str, dias: int):
    if not os.path.exists(backup_dir):
        return []
    limite = datetime.utcnow() - timedelta(days=dias)
    eliminados = []
    for name in os.listdir(backup_dir):
        path = os.path.join(backup_dir, name)
        if os.path.isfile(path):
            mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
            if mtime < limite:
                os.remove(path)
                eliminados.append(name)
    return eliminados


def listar_backups(backup_dir: str):
    if not os.path.exists(backup_dir):
        return []
    archivos = []
    for name in sorted(os.listdir(backup_dir)):
        path = os.path.join(backup_dir, name)
        if os.path.isfile(path):
            archivos.append({
                'nombre': name,
                'tamaño': os.path.getsize(path),
                'fecha': datetime.utcfromtimestamp(os.path.getmtime(path)).isoformat()
            })
    return archivos


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd', required=True)

    crear_parser = subparsers.add_parser('crear')
    crear_parser.add_argument('--db-path', required=True)
    crear_parser.add_argument('--backup-dir', required=True)

    limpiar_parser = subparsers.add_parser('limpiar')
    limpiar_parser.add_argument('--backup-dir', required=True)
    limpiar_parser.add_argument('--dias', type=int, required=True)

    listar_parser = subparsers.add_parser('listar')
    listar_parser.add_argument('--backup-dir', required=True)

    args = parser.parse_args()

    if args.cmd == 'crear':
        archivo = crear_backup(args.db_path, args.backup_dir)
        print(archivo)
    elif args.cmd == 'limpiar':
        eliminados = limpiar_backups(args.backup_dir, args.dias)
        for name in eliminados:
            print(name)
    elif args.cmd == 'listar':
        for info in listar_backups(args.backup_dir):
            print(f"{info['nombre']} {info['tamaño']} {info['fecha']}")


if __name__ == '__main__':
    main()
