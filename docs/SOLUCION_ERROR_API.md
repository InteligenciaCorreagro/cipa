# 🔧 Solución: Error 400 Bad Request API SIESA

## ❌ Error Actual

```
400 Client Error: Bad Request for url:
https://siesaprod.cipa.com.co/produccion/v3/ejecutarconsulta?...
parametros=FECHA_INI='2025-11-10'|FECHA_FIN='2025-11-10'
```

## 🎯 Problema Identificado

Estás usando fechas del año **2025**, pero deberías usar **2024**. La API de SIESA rechaza consultas para fechas futuras.

---

## ✅ Solución Rápida

### Usar el año correcto (2024)

```bash
python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2024-11-10 \
  --fecha-fin 2024-11-11
```

**Nota:** Cambia `2025` por `2024` en las fechas.

---

## 🔍 Verificar Conexión con la API

Antes de procesar, puedes verificar que la conexión funciona:

```bash
python backend/scripts/test_api_connection.py
```

**Este script probará:**
- ✅ Credenciales configuradas correctamente
- ✅ Conexión con la API de SIESA
- ✅ Diferentes fechas para ver cuáles tienen datos
- ✅ Muestra ejemplos de documentos obtenidos

**Salida esperada:**
```
================================================================================
TEST DE CONEXIÓN API SIESA
================================================================================

✅ Credenciales encontradas
   CONNI_KEY: 123abc456d...
   CONNI_TOKEN: xyz789def0...

================================================================================
PROBANDO DIFERENTES FECHAS
================================================================================

📅 Probando: Ayer (2024-11-11)
--------------------------------------------------------------------------------
   ✅ Éxito: 1,234 documentos obtenidos

   Ejemplo de documento:
      Prefijo: FME
      Número: 12345
      Cliente: CLIENTE EJEMPLO S.A.S.
      Producto: PRODUCTO EJEMPLO
      Valor: $850,000.00
      Tipo Inv: INV143002

📅 Probando: 10 Nov 2024 (2024-11-10)
--------------------------------------------------------------------------------
   ✅ Éxito: 1,156 documentos obtenidos
   ...
```

---

## 🐛 Otros Errores Posibles

### Error: "Faltan variables de entorno"

**Solución:** Verifica que el archivo `.env` existe y tiene las credenciales:

```bash
# Verificar que existe
ls -la .env

# Ver primeras líneas (sin mostrar credenciales completas)
head -3 .env
```

El `.env` debe tener:
```
CONNI_KEY=tu_key_aqui
CONNI_TOKEN=tu_token_aqui
DB_PATH=./data/notas_credito.db
```

### Error 401 Unauthorized

**Problema:** Credenciales incorrectas o expiradas.

**Solución:**
1. Verifica que `CONNI_KEY` y `CONNI_TOKEN` son correctos
2. Contacta al equipo de SIESA para renovar acceso

### Error 400 Bad Request (después de corregir fecha)

**Posibles causas:**
1. La API no tiene datos para esas fechas específicas
2. Formato de parámetros incorrecto
3. Permiso de API limitado

**Solución:** Prueba con fechas más recientes (ayer, hace 3 días)

### Sin documentos obtenidos

**Mensaje:** `⚠️ No hay documentos para esta fecha`

**Posible causa:** Esa fecha no tiene facturas registradas en SIESA.

**Solución:** Prueba con fechas diferentes o verifica con el equipo de finanzas.

---

## 📊 Comandos Útiles

### 1. Probar conexión API
```bash
python backend/scripts/test_api_connection.py
```

### 2. Procesar fechas específicas
```bash
python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2024-11-10 \
  --fecha-fin 2024-11-11
```

### 3. Procesar solo un día
```bash
python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2024-11-10 \
  --fecha-fin 2024-11-10
```

### 4. Procesar última semana
```bash
python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2024-11-04 \
  --fecha-fin 2024-11-10
```

### 5. Ver notas registradas
```bash
cd backend
python scripts/consultar_notas.py
```

### 6. Verificar facturas en BD
```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.execute('SELECT COUNT(*) FROM facturas')
print(f'Total facturas en BD: {cursor.fetchone()[0]}')
conn.close()
"
```

---

## 🎯 Ejemplo Completo: Poblar BD del 10-11 Noviembre 2024

### Paso 1: Verificar conexión
```bash
python backend/scripts/test_api_connection.py
```

### Paso 2: Si la conexión funciona, procesar
```bash
python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2024-11-10 \
  --fecha-fin 2024-11-11
```

### Paso 3: Verificar resultados
```bash
# Ver facturas guardadas
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')

# Total facturas
cursor = conn.execute('SELECT COUNT(*) FROM facturas')
print(f'✅ Total facturas: {cursor.fetchone()[0]}')

# Facturas con notas
cursor = conn.execute('SELECT COUNT(*) FROM facturas WHERE tiene_nota_credito=1')
print(f'✅ Facturas con notas: {cursor.fetchone()[0]}')

# Notas registradas
cursor = conn.execute('SELECT COUNT(*) FROM notas_credito')
print(f'✅ Notas registradas: {cursor.fetchone()[0]}')

conn.close()
"

# Ver archivos Excel generados
ls -lh output/facturas_202411*.xlsx
```

---

## 📝 Salida Esperada Correcta

Cuando todo funciona correctamente, deberías ver:

```
================================================================================
PROCESAMIENTO Y GUARDADO DE FACTURAS EN BD
================================================================================

Fecha inicio: 2024-11-10
Fecha fin: 2024-11-11
Base de datos: data/notas_credito.db

================================================================================
PROCESANDO DÍA: 2024-11-10
================================================================================

Total de documentos obtenidos: 1,234
Resultados del filtrado:
  - Facturas válidas: 856
  - Notas crédito: 23        ← ✅ Incluye NCE8262, NPA2, etc.
  - Facturas rechazadas: 355

Registrando 23 notas crédito del día...
Notas crédito nuevas registradas: 23

Procesando aplicación de notas crédito pendientes...
Total de aplicaciones realizadas: 47

Guardando facturas en la base de datos...
✅ Facturas guardadas en BD: 856 nuevas

Generando archivo Excel: facturas_20241110.xlsx
✅ Archivo generado: ./output/facturas_20241110.xlsx

================================================================================
RESUMEN FINAL
================================================================================

Facturas:
  Total facturas procesadas: 1,712
  Total guardadas en BD: 1,712

Notas de crédito:
  Notas únicas aplicadas: 45
  Total de aplicaciones: 94

✅ PROCESO COMPLETADO EXITOSAMENTE
```

---

## 🆘 Si Nada Funciona

1. **Verifica credenciales:**
   ```bash
   cat .env | grep CONNI
   ```

2. **Prueba conexión básica:**
   ```bash
   python backend/scripts/test_api_connection.py
   ```

3. **Verifica que la API de SIESA está disponible:**
   - URL: https://siesaprod.cipa.com.co/produccion/v3/ejecutarconsulta
   - Contacta al equipo de IT/SIESA

4. **Revisa logs del proceso** para detalles específicos del error

5. **Contacta soporte** con:
   - Output completo del script
   - Fechas que estás intentando procesar
   - Mensaje de error completo
