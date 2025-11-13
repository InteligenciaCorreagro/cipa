# Guía de Configuración - Sistema CIPA

## ✅ Cambios Implementados

### 1. Unificación de Base de Datos
**Problema resuelto:** La API usaba `backend/data/notas_credito.db` mientras que GitHub Actions usaba `data/notas_credito.db`

**Solución:** Todos los componentes ahora usan la misma base de datos:
- **Ubicación:** `/home/user/cipa/data/notas_credito.db` (raíz del proyecto)
- **Componentes actualizados:**
  - API REST (`backend/api/app.py`)
  - AuthManager (`backend/api/auth.py`)
  - GitHub Actions (`.github/workflows/daily_process.yml`)
  - Scripts de backend

### 2. Tabla de Facturas con Líneas Completas
**Nueva funcionalidad:** Guardar todas las líneas de facturas igual que el Excel de operativa

**Características:**
- ✅ Una factura puede tener múltiples líneas (ej: FME123 con 4 productos diferentes)
- ✅ Campo `descripcion_nota_aplicada` muestra qué nota se aplicó
- ✅ Campo `tiene_nota_credito` (1/0) para filtrar fácilmente
- ✅ Constraint `UNIQUE(numero_factura, codigo_producto, fecha_proceso)` permite líneas

**Schema de tabla facturas:**
```sql
CREATE TABLE facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_factura TEXT NOT NULL,
    fecha_factura DATE NOT NULL,
    nit_cliente TEXT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    tipo_inventario TEXT,
    valor_total REAL NOT NULL,
    cantidad REAL NOT NULL,
    valor_transado REAL DEFAULT 0,
    cantidad_transada REAL DEFAULT 0,
    descripcion_nota_aplicada TEXT,          -- "Nota aplicada: NC123" o NULL
    estado TEXT DEFAULT 'VALIDA',
    tiene_nota_credito INTEGER DEFAULT 0,    -- 1 si tiene nota, 0 si no
    es_valida INTEGER DEFAULT 1,
    razon_invalidez TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_proceso DATE NOT NULL,
    UNIQUE(numero_factura, codigo_producto, fecha_proceso)
)
```

## 🔧 Configuración Requerida

### Paso 1: Crear archivo .env

Crea el archivo `.env` en la raíz del proyecto (`/home/user/cipa/.env`):

```bash
# API SIESA (requerido para obtener facturas y notas)
CONNI_KEY=tu_conni_key_aqui
CONNI_TOKEN=tu_conni_token_aqui

# Base de datos (ruta relativa al proyecto raíz)
DB_PATH=./data/notas_credito.db

# JWT Secret para API REST (generar uno único)
# Generar con: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=tu_jwt_secret_key_seguro_aqui

# API Configuration
API_PORT=5000
DEBUG=False

# Email (opcional, para notificaciones)
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_app
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
DESTINATARIOS=operativa@correagro.com,finanzas@correagro.com

# Template path
TEMPLATE_PATH=./templates/plantilla.xlsx
```

### Paso 2: Generar JWT Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copia el resultado y úsalo como `JWT_SECRET_KEY` en el `.env`

## 📊 Poblar Base de Datos (10-11 Noviembre)

Una vez configurado el `.env`, ejecuta:

```bash
# Desde el directorio raíz del proyecto
cd /home/user/cipa

# Procesar y guardar facturas del 10-11 de noviembre
python backend/scripts/procesar_y_guardar_facturas.py \
  --fecha-inicio 2025-11-10 \
  --fecha-fin 2025-11-11
```

**Lo que hace este script:**
1. ✅ Obtiene facturas de la API SIESA para cada día
2. ✅ Aplica reglas de negocio (filtra tipos de inventario excluidos)
3. ✅ Separa notas de crédito de facturas válidas
4. ✅ Registra notas de crédito en la BD
5. ✅ Aplica notas pendientes a facturas nuevas
6. ✅ **Guarda TODAS las líneas de facturas en la tabla `facturas`**
7. ✅ Marca facturas con notas aplicadas (`descripcion_nota_aplicada`)
8. ✅ Genera Excel para operativa en `output/`

**Ejemplo de salida:**
```
PROCESANDO DÍA: 2025-11-10
Total de documentos obtenidos: 1,234
Facturas válidas: 856
Notas crédito: 23
Facturas rechazadas: 355

Aplicaciones realizadas: 47
Facturas con descripción de notas: 47

✅ Facturas guardadas en BD: 856 nuevas
✅ Archivo generado: output/facturas_20251110.xlsx
```

## 🚀 Iniciar API REST

```bash
cd /home/user/cipa/backend
python iniciar_api.py
```

La API estará disponible en: `http://localhost:5000`

**Endpoints disponibles:**
- `POST /api/auth/login` - Autenticación
- `GET /api/notas` - Listar notas de crédito
- `GET /api/notas/pendientes` - Notas pendientes
- `GET /api/notas/aplicadas` - Notas aplicadas
- `GET /api/facturas` - Listar facturas (con filtros)
- `GET /api/facturas/con-notas` - Facturas que tienen notas aplicadas
- `GET /api/dashboard/stats` - Estadísticas para dashboard

## 📋 Consultar Datos

### Ver facturas guardadas en BD

```bash
cd /home/user/cipa

# Ver total de facturas
python -c "import sqlite3; conn = sqlite3.connect('data/notas_credito.db'); print('Total facturas:', conn.execute('SELECT COUNT(*) FROM facturas').fetchone()[0]); conn.close()"

# Ver facturas con notas aplicadas
python -c "import sqlite3; conn = sqlite3.connect('data/notas_credito.db'); print('Facturas con notas:', conn.execute('SELECT COUNT(*) FROM facturas WHERE tiene_nota_credito=1').fetchone()[0]); conn.close()"

# Ver ejemplo de facturas con múltiples líneas
python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.execute('''
    SELECT numero_factura, COUNT(*) as lineas
    FROM facturas
    GROUP BY numero_factura
    HAVING lineas > 1
    LIMIT 5
''')
print('Facturas con múltiples líneas:')
for row in cursor:
    print(f'  {row[0]}: {row[1]} líneas')
conn.close()
"
```

### Ver notas de crédito

```bash
cd /home/user/cipa/backend
python scripts/consultar_notas.py
```

## 🔍 Verificar Configuración

### Verificar que todo use la misma BD

```bash
# Ver archivos de base de datos en el proyecto
find /home/user/cipa -name "notas_credito.db" -exec ls -lh {} \;

# Debería mostrar solo:
# /home/user/cipa/data/notas_credito.db

# Si aparece backend/data/notas_credito.db, es una BD antigua que puede eliminarse
```

### Verificar tabla facturas

```bash
cd /home/user/cipa

python -c "
import sqlite3
conn = sqlite3.connect('data/notas_credito.db')
cursor = conn.execute('PRAGMA table_info(facturas)')
print('Columnas de tabla facturas:')
for row in cursor:
    print(f'  {row[1]} ({row[2]})')
conn.close()
"
```

Debe mostrar las columnas incluyendo:
- `descripcion_nota_aplicada`
- `tiene_nota_credito`
- `fecha_proceso`

## 📝 Estructura del Proyecto

```
/home/user/cipa/
├── data/
│   └── notas_credito.db          # ✅ BD ÚNICA del sistema
├── backend/
│   ├── api/
│   │   ├── app.py                # ✅ Actualizado: usa BD raíz
│   │   └── auth.py               # ✅ Actualizado: usa BD raíz
│   ├── scripts/
│   │   ├── crear_tabla_facturas.py        # ✅ Actualizado
│   │   └── procesar_y_guardar_facturas.py # ✅ NUEVO
│   ├── core/
│   │   └── notas_credito_manager.py
│   └── main.py                   # Proceso principal
├── .github/
│   └── workflows/
│       └── daily_process.yml     # ✅ Usa BD raíz
├── output/                        # Archivos Excel generados
└── .env                          # ⚠️ CREAR ESTE ARCHIVO

```

## ⚙️ GitHub Actions

La configuración de GitHub Actions ya está actualizada para usar la misma BD.

**Variables secretas requeridas en GitHub:**
- `CONNI_KEY`
- `CONNI_TOKEN`
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`
- `SMTP_SERVER`
- `SMTP_PORT`
- `DESTINATARIOS`

**Variable de entorno en workflow:**
- `DB_PATH: ./data/notas_credito.db`

## 🐛 Solución de Problemas

### Error: No module named 'flask' / 'openpyxl'

```bash
pip install -r backend/requirements.txt
```

### Error: Cannot connect to API (Error 500)

1. Verificar que el `.env` exista y tenga `JWT_SECRET_KEY`
2. Verificar que la BD exista: `ls -lh data/notas_credito.db`
3. Revisar logs de la API

### Error: Faltan variables de entorno

1. Verificar que `.env` esté en la raíz del proyecto
2. Verificar que contenga `CONNI_KEY` y `CONNI_TOKEN`

### Dashboard muestra "Error 500"

1. Verificar que la API esté corriendo: `curl http://localhost:5000/api/health`
2. Verificar que la BD tenga datos
3. Verificar logs de la API

## 📚 Próximos Pasos

1. ✅ Configurar `.env` con credenciales reales
2. ✅ Ejecutar script para poblar BD del 10-11 de noviembre
3. ✅ Iniciar API REST
4. ✅ Verificar dashboard en navegador
5. ✅ Configurar GitHub Actions secrets si aún no están
6. ✅ Probar proceso automático diario

## 🎯 Resumen de Beneficios

### Antes:
- ❌ Dos bases de datos diferentes (inconsistencia)
- ❌ Facturas solo en Excel, no en BD
- ❌ Sin información de qué nota se aplicó
- ❌ No se guardaban líneas completas de facturas

### Después:
- ✅ Una sola BD para todo el sistema
- ✅ Facturas guardadas con todas sus líneas
- ✅ Campo `descripcion_nota_aplicada` muestra qué nota
- ✅ Fácil consultar facturas con/sin notas
- ✅ Dashboard puede mostrar datos reales de BD
- ✅ Historial completo de facturas procesadas

