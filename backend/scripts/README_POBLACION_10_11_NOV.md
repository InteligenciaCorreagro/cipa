# Instrucciones: Población de Datos 10-11 Noviembre 2025

## Estado Actual

✅ **Base de datos preparada:**
- Tabla `facturas` recreada con campo `nota_aplicada`
- Scripts de población creados y listos

## Requisitos

Para ejecutar los scripts necesitas configurar las credenciales del API SIESA en el archivo `.env`:

```bash
cd /home/user/cipa/backend
```

Crea el archivo `.env` con el siguiente contenido:

```env
CONNI_KEY=tu_conni_key_aqui
CONNI_TOKEN=tu_conni_token_aqui
```

## Scripts Disponibles

### 1. Poblar Facturas (10-11 noviembre)

```bash
python scripts/poblar_facturas_10_11_nov.py
```

**Qué hace:**
- Trae facturas del **10 y 11 de noviembre 2025**
- Guarda **TODAS las líneas** de cada factura (ej: FME123 con 4 líneas = 4 registros)
- Aplica **reglas de negocio idénticas al Excel de operativa:**
  - ✓ Monto mínimo $498,000 por factura COMPLETA (suma de todas las líneas)
  - ✓ Excluye 24 tipos de inventario específicos
- Cada línea tiene:
  - Todos los campos del API SIESA (f_prefijo, f_nrodocto, f_fecha, etc.)
  - Campo `nota_aplicada` (NULL inicialmente, se actualiza cuando se aplica nota)

### 2. Poblar Notas de Crédito (10-11 noviembre)

```bash
python scripts/poblar_notas_10_11_nov.py
```

**Qué hace:**
- Trae notas de crédito del **10 y 11 de noviembre 2025**
- Filtra documentos con prefijo 'N' (notas de crédito)
- Guarda cada línea de nota como registro separado
- Estado inicial: **PENDIENTE**

## Orden de Ejecución

```bash
cd /home/user/cipa/backend

# 1. Poblar facturas
python scripts/poblar_facturas_10_11_nov.py

# 2. Poblar notas de crédito
python scripts/poblar_notas_10_11_nov.py
```

## Verificación

Después de ejecutar los scripts, puedes verificar los datos:

```bash
# Ver estadísticas de facturas
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.cursor()

print('\\n=== FACTURAS ===')
cursor.execute('SELECT COUNT(*) FROM facturas')
print(f'Total líneas: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(DISTINCT numero_factura) FROM facturas')
print(f'Facturas únicas: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM facturas WHERE es_valida = 1')
print(f'Líneas válidas: {cursor.fetchone()[0]}')

print('\\n=== NOTAS DE CRÉDITO ===')
cursor.execute('SELECT COUNT(*) FROM notas_credito')
print(f'Total notas: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(DISTINCT numero_nota) FROM notas_credito')
print(f'Notas únicas: {cursor.fetchone()[0]}')

conn.close()
"
```

## Importante

- **Las facturas guardadas coinciden EXACTAMENTE con el Excel de operativa**
- Cada línea de factura se guarda por separado
- El campo `nota_aplicada` estará NULL hasta que se aplique una nota
- Para actualizar `nota_aplicada`, necesitarás un script que relacione notas con facturas

## Próximos Pasos

1. Configurar `.env` con credenciales
2. Ejecutar scripts de población
3. Verificar datos
4. Implementar lógica para actualizar `nota_aplicada` cuando se apliquen notas
5. Sincronizar con GitHub Actions (la base de datos debe estar en el repo o en un storage compartido)
