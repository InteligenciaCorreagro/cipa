# 📋 Instrucciones para Poblar Base de Datos (10-11 Noviembre)

## ✅ Lo que ya está listo

1. ✅ **Base de datos unificada** - Todos usan `data/notas_credito.db`
2. ✅ **Tabla facturas creada** - Con soporte para múltiples líneas
3. ✅ **Script de procesamiento** - `backend/scripts/procesar_y_guardar_facturas.py`
4. ✅ **Endpoints de API** - Para ver facturas, rechazadas y con notas
5. ✅ **Validación de notas** - NCE y NPA se aceptan correctamente ✅

---

## 🔧 Paso 1: Crear archivo .env

En la **raíz del proyecto** (`/home/user/cipa/`), crea el archivo `.env`:

```bash
# Copiar este contenido y reemplazar con tus credenciales reales

# ==========================================
# API SIESA (REQUERIDO)
# ==========================================
CONNI_KEY=tu_conni_key_aqui
CONNI_TOKEN=tu_conni_token_aqui

# ==========================================
# BASE DE DATOS
# ==========================================
DB_PATH=./data/notas_credito.db

# ==========================================
# JWT SECRET (para API REST)
# ==========================================
# Generar con: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=tu_jwt_secret_key_seguro_aqui

# ==========================================
# API Configuration
# ==========================================
API_PORT=5000
DEBUG=False

# ==========================================
# EMAIL (Opcional - para notificaciones)
# ==========================================
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_app
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
DESTINATARIOS=operativa@correagro.com,finanzas@correagro.com

# ==========================================
# TEMPLATE PATH
# ==========================================
TEMPLATE_PATH=./templates/plantilla.xlsx
```

**⚠️ IMPORTANTE:** Reemplaza los valores con tus credenciales reales:
- `CONNI_KEY` - Tu llave de API SIESA
- `CONNI_TOKEN` - Tu token de API SIESA
- `JWT_SECRET_KEY` - Genera uno nuevo (comando abajo)

---

## 🔑 Paso 2: Generar JWT Secret Key

Ejecuta este comando para generar una clave segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copia el resultado y pégalo en `JWT_SECRET_KEY` en el archivo `.env`

---

## 📊 Paso 3: Poblar Base de Datos (10-11 Noviembre)

Una vez configurado el `.env`, ejecuta:

```bash
cd /home/user/cipa

python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2025-11-10 \
  --fecha-fin 2025-11-11
```

### ¿Qué hace este script?

1. ✅ **Obtiene facturas** de la API SIESA para el 10 y 11 de noviembre
2. ✅ **Aplica reglas de negocio:**
   - Filtra tipos de inventario excluidos (DESCUENTO, VSMENOR, etc.)
   - Valida monto mínimo ($498,000)
   - Separa notas de crédito (NCE, NPA, etc.)
3. ✅ **Registra notas de crédito** en la tabla `notas_credito`
4. ✅ **Aplica notas pendientes** a facturas nuevas
5. ✅ **Guarda TODAS las líneas** en tabla `facturas`
6. ✅ **Marca facturas con notas** aplicadas (`descripcion_nota_aplicada`)
7. ✅ **Genera Excel** para operativa en `output/`

### Salida Esperada:

```
================================================================================
PROCESAMIENTO Y GUARDADO DE FACTURAS EN BD
================================================================================

Fecha inicio: 2025-11-10
Fecha fin: 2025-11-11
Base de datos: /home/user/cipa/data/notas_credito.db
Directorio de salida: ./output

================================================================================
PROCESANDO DÍA: 2025-11-10
================================================================================

Total de documentos obtenidos: 1,234
Resultados del filtrado:
  - Facturas válidas: 856
  - Notas crédito: 23        ← ✅ NCE8262, NPA2, etc.
  - Facturas rechazadas: 355

Registrando 23 notas crédito del día...
Notas crédito nuevas registradas: 23

Transformando facturas...
Facturas transformadas: 856

Procesando aplicación de notas crédito pendientes...
Total de aplicaciones realizadas: 47

Guardando facturas en la base de datos...
✅ Facturas guardadas en BD: 856 nuevas

Estadísticas del día:
  Facturas procesadas: 856
  Facturas guardadas en BD: 856
  Valor total: $1,250,000,000.00

Generando archivo Excel: facturas_20251110.xlsx
✅ Archivo generado: ./output/facturas_20251110.xlsx

================================================================================
PROCESANDO DÍA: 2025-11-11
================================================================================

[Similar output para el día 11]

================================================================================
RESUMEN FINAL DEL PROCESAMIENTO
================================================================================

Período procesado: 2025-11-10 a 2025-11-11
Días procesados: 2 / 2
Días con facturas: 2

Facturas:
  Total facturas procesadas: 1,712
  Total guardadas en BD: 1,712
  Valor total: $2,500,000,000.00

Notas de crédito:
  Notas únicas aplicadas: 45
  Total de aplicaciones: 94
  Valor total aplicado: $15,000,000.00

Archivos generados (2):

  2025-11-10:
    Archivo: facturas_20251110.xlsx
    Facturas: 856
    Aplicaciones: 47
    Valor: $1,250,000,000.00

  2025-11-11:
    Archivo: facturas_20251111.xlsx
    Facturas: 856
    Aplicaciones: 47
    Valor: $1,250,000,000.00

================================================================================
ESTADO ACTUAL DE NOTAS DE CRÉDITO EN BD
================================================================================
Notas pendientes: 12
Saldo pendiente total: $5,000,000.00
Notas aplicadas (histórico): 33
Total aplicaciones (histórico): 94
Monto total aplicado (histórico): $15,000,000.00

================================================================================
✅ PROCESO COMPLETADO EXITOSAMENTE
================================================================================
```

---

## 🔍 Paso 4: Verificar Datos en BD

### Verificar total de facturas guardadas:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.execute('SELECT COUNT(*) FROM facturas')
print(f'Total facturas: {cursor.fetchone()[0]}')
cursor = conn.execute('SELECT COUNT(*) FROM facturas WHERE tiene_nota_credito=1')
print(f'Facturas con notas: {cursor.fetchone()[0]}')
conn.close()
"
```

### Ver ejemplos de facturas con múltiples líneas:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.execute('''
    SELECT numero_factura, COUNT(*) as lineas
    FROM facturas
    GROUP BY numero_factura
    HAVING lineas > 1
    ORDER BY lineas DESC
    LIMIT 5
''')
print('Facturas con múltiples líneas:')
for row in cursor:
    print(f'  {row[0]}: {row[1]} líneas')
conn.close()
"
```

### Ver facturas con notas aplicadas:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.execute('''
    SELECT numero_factura, nombre_producto, descripcion_nota_aplicada
    FROM facturas
    WHERE tiene_nota_credito = 1
    LIMIT 5
''')
print('Facturas con notas aplicadas:')
for row in cursor:
    print(f'  {row[0]}: {row[1][:40]} - {row[2]}')
conn.close()
"
```

### Ver notas de crédito registradas:

```bash
cd backend
python scripts/consultar_notas.py
```

---

## 🚀 Paso 5: Iniciar API REST

```bash
cd /home/user/cipa/backend
python iniciar_api.py
```

**Salida esperada:**
```
============================================================
    API REST - Sistema de Notas de Crédito CIPA
============================================================

🔍 Verificando dependencias...
  ✓ flask
  ✓ flask_jwt_extended
  ✓ flask_cors
  ✓ bcrypt

✓ Todas las dependencias instaladas

🔍 Verificando base de datos...
✓ Base de datos encontrada: /home/user/cipa/data/notas_credito.db

🔍 Verificando configuración...
✓ .env encontrado
✓ JWT_SECRET_KEY configurado

============================================================
✓ Verificaciones completadas exitosamente
============================================================

 * Running on http://0.0.0.0:5000
```

---

## 🌐 Paso 6: Probar Endpoints en Dashboard

### 1. Ver Facturas Rechazadas

```
GET http://localhost:5000/api/facturas/rechazadas
```

Deberías ver facturas rechazadas con su `razon_rechazo`.

### 2. Ver Facturas con Notas Aplicadas

```
GET http://localhost:5000/api/facturas/con-notas
```

Deberías ver facturas con el campo `descripcion_nota_aplicada` poblado (ej: "Nota aplicada: NCE8262").

### 3. Ver Todas las Facturas

```
GET http://localhost:5000/api/facturas?fecha_desde=2025-11-10&fecha_hasta=2025-11-11
```

### 4. Ver Estadísticas

```
GET http://localhost:5000/api/facturas/estadisticas
```

---

## 📊 Datos Esperados

Después de poblar la BD del 10-11 de noviembre, deberías ver:

### Notas de Crédito Aceptadas:
- ✅ **NCE8262** (MASCOTAS - INV143005)
- ✅ **NPA2** con 4 líneas:
  - AVICULTURA (INV143001)
  - ENGORDE (INV143002)
  - OTRAS ESPECIES (INV143009)

### Facturas con Múltiples Líneas:
- Una factura como **FME12345** puede aparecer 4 veces (una por cada producto)
- Esto es **correcto** y refleja el comportamiento del Excel de operativa

### Facturas con Notas:
- Campo `tiene_nota_credito = 1`
- Campo `descripcion_nota_aplicada` poblado
- Ejemplo: `"Nota aplicada: NCE8262"` o `"Notas aplicadas: NCE8262, NPA2"`

---

## ❌ Solución de Problemas

### Error: "Faltan variables de entorno: CONNI_KEY y/o CONNI_TOKEN"

**Solución:** Verifica que el archivo `.env` existe en la raíz del proyecto y tiene las credenciales correctas.

```bash
# Verificar que existe
ls -la /home/user/cipa/.env

# Ver contenido (sin mostrar credenciales completas)
head -5 /home/user/cipa/.env
```

### Error: "Cannot connect to API (Error 500)"

**Solución:**
1. Verifica que `JWT_SECRET_KEY` está configurado en `.env`
2. Reinicia la API
3. Verifica logs de la API

### No aparecen notas en el proceso

**Solución:**
1. Verifica que las notas tienen tipos de inventario permitidos (INV143xxx)
2. Ejecuta el script de prueba:
   ```bash
   python backend/scripts/test_notas_validation.py
   ```
3. Revisa los logs del proceso para ver si las notas fueron rechazadas

---

## 📝 Resumen de Archivos Generados

Después del proceso tendrás:

```
/home/user/cipa/
├── data/
│   └── notas_credito.db          ← BD poblada con datos del 10-11
├── output/
│   ├── facturas_20251110.xlsx    ← Excel para operativa día 10
│   └── facturas_20251111.xlsx    ← Excel para operativa día 11
└── .env                          ← Configuración (¡no commitear!)
```

---

## ✅ Checklist Final

Antes de usar el dashboard, verifica:

- [ ] Archivo `.env` creado con credenciales reales
- [ ] Script de población ejecutado exitosamente
- [ ] BD tiene facturas del 10-11 de noviembre
- [ ] API REST está corriendo en puerto 5000
- [ ] Endpoints responden correctamente
- [ ] Dashboard puede conectarse a la API

---

## 🎯 Próximos Pasos

Una vez que la BD esté poblada y la API funcionando:

1. **Frontend:** Actualizar componentes de grillas para mostrar:
   - Facturas rechazadas con razón
   - Facturas con notas aplicadas con descripción
   - Filtros por fecha

2. **GitHub Actions:** Ya está configurado para usar la misma BD

3. **Proceso Diario:** El sistema ya puede ejecutarse automáticamente cada día

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs del proceso
2. Ejecuta el script de prueba de notas
3. Verifica que la API está corriendo
4. Revisa que el `.env` tiene las credenciales correctas
