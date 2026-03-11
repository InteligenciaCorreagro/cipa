import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from db import get_mysql_config

TABLES = [
    'facturas',
    'facturas_rechazadas',
    'notas_credito',
    'notas_pendientes',
    'aplicaciones_notas',
    'notas_aplicadas',
    'log_motivos_no_aplicacion',
    'audit_logs',
]


def clear_mysql():
    try:
        import mysql.connector as mc
    except Exception as exc:
        print(f"mysql_skip {exc}")
        return

    try:
        cfg = get_mysql_config()
        conn = mc.connect(**cfg)
        cur = conn.cursor()
        for table in TABLES:
            try:
                cur.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        conn.close()
        print("mysql_ok")
    except Exception as exc:
        print(f"mysql_skip {exc}")


if __name__ == '__main__':
    clear_mysql()
