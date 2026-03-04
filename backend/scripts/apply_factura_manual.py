import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.notas_credito_manager import NotasCreditoManager
from db import get_connection

numero_factura = "FCE96137"

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT raw_payload, indice_linea FROM facturas WHERE numero_factura = ?", (numero_factura,))
rows = cur.fetchall()
conn.close()

facturas = []
for row in rows:
    payload = row.get("raw_payload") if isinstance(row, dict) else row[0]
    indice_linea = row.get("indice_linea") if isinstance(row, dict) else row[1]
    if not payload:
        continue
    data = json.loads(payload)
    data["_indice_linea"] = indice_linea
    facturas.append(data)

manager = NotasCreditoManager()
apps = manager.procesar_notas_para_facturas(facturas)
print("aplicaciones", apps)
