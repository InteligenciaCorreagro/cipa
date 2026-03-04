import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from db import get_connection
import re

conn = get_connection()
cur = conn.cursor()
print("engine", conn.engine)

cur.execute("SELECT * FROM notas_credito WHERE numero_nota = ?", ("NCE8535",))
nota = cur.fetchone()
cur.fetchall()
print("nota", dict(nota) if nota else None)
nota_nombre = re.sub(r'\s+', ' ', (nota.get('nombre_producto') if nota else '')).strip().upper()
print("nota_nombre", nota_nombre)

cur.execute("SELECT * FROM facturas WHERE numero_factura = ?", ("FCE96137",))
rows = cur.fetchall()
print("facturas", [dict(r) for r in rows])
for r in rows:
    nombre = re.sub(r'\s+', ' ', (r.get('nombre_producto') or '')).strip().upper()
    print("factura_nombre", r.get('numero_factura'), r.get('codigo_producto'), nombre, nombre == nota_nombre)

try:
    cur.execute("SELECT * FROM notas_aplicadas WHERE numero_nota = ?", ("NCE8535",))
    print("aplicadas", [dict(r) for r in cur.fetchall()])
except Exception as exc:
    print("aplicadas_error", exc)

conn.close()
