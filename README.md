# Sistema de Gestión de Facturas con Reglas de Negocio

Sistema automatizado para procesamiento de facturas desde la API de SIESA con validación de reglas de negocio, gestión de notas crédito y generación de reportes.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Reglas de Negocio](#reglas-de-negocio)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Base de Datos](#base-de-datos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Flujo de Procesamiento](#flujo-de-procesamiento)
- [Logging y Auditoría](#logging-y-auditoría)

## ✨ Características

### Funcionalidades Principales

1. **Obtención Automática de Facturas**: Integración con API de SIESA
2. **Validación de Reglas de Negocio**:
   - Filtrado por tipo de inventario
   - Validación de monto mínimo ($498,000 COP)
   - Identificación automática de notas crédito
3. **Gestión de Notas Crédito**:
   - Persistencia en base de datos SQLite
   - Aplicación automática a facturas por cliente y producto
   - Validación de montos y cantidades
   - Historial completo de aplicaciones
4. **Generación de Reportes**:
   - Excel con facturas válidas
   - Reporte de facturas rechazadas
   - Reporte de notas crédito y aplicaciones
5. **Envío Automático por Email**
6. **Ejecución Programada**: GitHub Actions para ejecución diaria

## 🏗️ Arquitectura

### Componentes del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                       MAIN PROCESS                          │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  API Client  │ │   Business   │ │    Notas     │
    │   (SIESA)    │ │    Rules     │ │   Crédito    │
    │              │ │  Validator   │ │   Manager    │
    └──────────────┘ └──────────────┘ └──────────────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │    Excel     │ │    Email     │ │   SQLite     │
    │  Processor   │ │   Sender     │ │   Database   │
    └──────────────┘ └──────────────┘ └──────────────┘
```

### Módulos

#### 1. **api_client.py**
- Conexión con API de SIESA
- Manejo de autenticación
- Parseo de respuestas JSON

#### 2. **business_rules.py**
- Validación de tipos de inventario excluidos
- Validación de monto mínimo
- Identificación de notas crédito
- Separación y filtrado de facturas

#### 3. **notas_credito_manager.py**
- Gestión de base de datos SQLite
- Registro de notas crédito
- Aplicación automática a facturas
- Generación de reportes de notas

#### 4. **excel_processor.py**
- Transformación de datos API → Excel
- Generación de archivo Excel formateado
- Cálculos de precios y cantidades

#### 5. **email_sender.py**
- Envío de emails con adjuntos
- Plantillas HTML personalizadas

## 📏 Reglas de Negocio

### 1. Tipos de Inventario Excluidos

Las facturas con los siguientes códigos de tipo de inventario **NO se procesan**:

```
VSMENORCC    VS4205101    INVMEDICAD   INV1430051
VS42100501   VS420515     VS42051003   VS420510
VSMENOR      INVFLETEPT   VSMENOR5%    VS42505090
INVFLETGEN   INV144542    INV144554    VSMAY-MECC
VSMAY-MECP   VSMAY-GEN    DESCESPEC    DESCUENTO
INV144562    VS425050     VS41200822   INV1460
VS41200819
```

### 2. Monto Mínimo

- **Valor mínimo**: $498,000 COP
- Facturas con valor inferior son **rechazadas automáticamente**
- Se genera reporte de facturas rechazadas para auditoría

### 3. Notas Crédito

#### Identificación
- Prefijo: Cualquier factura con prefijo que inicie con **"N"**
- Se procesan separadamente de las facturas regulares

#### Aplicación
Las notas crédito se aplican a facturas cumpliendo estas condiciones:

1. **Mismo Cliente** (NIT debe coincidir exactamente)
2. **Mismo Producto** (código de producto debe coincidir)
3. **Validaciones de Monto**:
   - Valor aplicado ≤ Valor de la factura
   - Cantidad aplicada ≤ Cantidad de la factura
   - Saldo de nota ≥ Valor a aplicar

#### Persistencia
- Las notas se almacenan en base de datos SQLite
- Si no se pueden aplicar hoy, quedan pendientes para facturas futuras
- Historial completo de todas las aplicaciones

## 🚀 Instalación

### Requisitos Previos

- Python 3.11+
- pip
- Git

### Pasos de Instalación

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd cipa

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear directorios necesarios
mkdir -p data output templates
```

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# API SIESA
CONNI_KEY=your_conni_key
CONNI_TOKEN=your_conni_token

# Email Configuration
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Destinatarios (separados por coma)
DESTINATARIOS=email1@company.com,email2@company.com

# Optional
TEMPLATE_PATH=./templates/plantilla.xlsx
DB_PATH=./data/notas_credito.db
```

### GitHub Secrets

Para ejecución automática en GitHub Actions, configurar los siguientes secrets:

1. Ir a Settings → Secrets and variables → Actions
2. Agregar cada variable del `.env` como secret

## 📖 Uso

### Ejecución Manual

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar proceso
python main.py
```

### Ejecución Automática

El sistema se ejecuta automáticamente todos los días a las 8:00 AM (hora de Bogotá) mediante GitHub Actions.

Para ejecutar manualmente desde GitHub:
1. Ir a Actions tab
2. Seleccionar "Reporte Diario de Facturas"
3. Click en "Run workflow"

## 💾 Base de Datos

### Estructura SQLite

#### Tabla: `notas_credito`

```sql
CREATE TABLE notas_credito (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_nota TEXT NOT NULL UNIQUE,
    fecha_nota DATE NOT NULL,
    nit_cliente TEXT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    valor_total REAL NOT NULL,
    cantidad REAL NOT NULL,
    saldo_pendiente REAL NOT NULL,
    cantidad_pendiente REAL NOT NULL,
    estado TEXT DEFAULT 'PENDIENTE',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aplicacion_completa TIMESTAMP NULL
);
```

#### Tabla: `aplicaciones_notas`

```sql
CREATE TABLE aplicaciones_notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_nota INTEGER NOT NULL,
    numero_nota TEXT NOT NULL,
    numero_factura TEXT NOT NULL,
    fecha_factura DATE NOT NULL,
    nit_cliente TEXT NOT NULL,
    codigo_producto TEXT NOT NULL,
    valor_aplicado REAL NOT NULL,
    cantidad_aplicada REAL NOT NULL,
    fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_nota) REFERENCES notas_credito(id)
);
```

### Consultas Útiles

```python
from src.notas_credito_manager import NotasCreditoManager

manager = NotasCreditoManager()

# Obtener resumen
resumen = manager.obtener_resumen_notas()
print(f"Notas pendientes: {resumen['notas_pendientes']}")
print(f"Saldo pendiente: ${resumen['saldo_pendiente_total']:,.2f}")

# Ver historial de una nota
historial = manager.obtener_historial_nota('N001234')
for app in historial:
    print(f"Aplicada a factura: {app['numero_factura']}")
    print(f"Valor: ${app['valor_aplicado']:,.2f}")
```

## 📁 Estructura del Proyecto

```
cipa/
├── .github/
│   └── workflows/
│       └── daily_report.yml      # GitHub Actions workflow
├── config/
│   └── config.py                 # Configuraciones adicionales
├── data/
│   └── notas_credito.db          # Base de datos SQLite
├── output/                        # Archivos generados
│   ├── facturas_YYYYMMDD.xlsx
│   ├── facturas_rechazadas_YYYYMMDD.txt
│   └── reporte_notas_credito_YYYYMMDD.txt
├── src/
│   ├── api_client.py             # Cliente API SIESA
│   ├── business_rules.py         # Validador de reglas de negocio
│   ├── email_sender.py           # Envío de correos
│   ├── excel_processor.py        # Procesamiento de Excel
│   └── notas_credito_manager.py  # Gestor de notas crédito
├── templates/
│   └── plantilla.xlsx            # Plantilla Excel (opcional)
├── .env                           # Variables de entorno (no en git)
├── .gitignore
├── main.py                        # Proceso principal
├── README.md                      # Este archivo
└── requirements.txt               # Dependencias Python
```

## 🔄 Flujo de Procesamiento

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────┐
│  1. OBTENER FACTURAS DE LA API                              │
│     - Consultar API SIESA con fecha del día anterior        │
│     - Parsear respuesta JSON                                │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. APLICAR REGLAS DE NEGOCIO                               │
│     - Identificar notas crédito (prefijo 'N')               │
│     - Filtrar tipos de inventario excluidos                 │
│     - Validar monto mínimo ($498,000)                       │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. GESTIONAR NOTAS CRÉDITO                                 │
│     - Registrar nuevas notas en BD                          │
│     - Buscar notas pendientes                               │
│     - Aplicar a facturas (mismo cliente + producto)         │
│     - Actualizar saldos                                     │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. TRANSFORMAR Y GENERAR REPORTES                          │
│     - Transformar facturas válidas                          │
│     - Generar Excel principal                               │
│     - Generar reporte de rechazos                           │
│     - Generar reporte de notas crédito                      │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. ENVIAR CORREO                                           │
│     - Adjuntar Excel de facturas                            │
│     - Incluir resumen en cuerpo                             │
└─────────────────────────────────────────────────────────────┘
```

### Ejemplo de Log de Ejecución

```
2025-10-26 08:00:01 - INFO - ============================================================
2025-10-26 08:00:01 - INFO - Iniciando proceso para: 2025-10-25
2025-10-26 08:00:01 - INFO - ============================================================
2025-10-26 08:00:02 - INFO - Total de documentos obtenidos de la API: 156
2025-10-26 08:00:02 - INFO - 
============================================================
2025-10-26 08:00:02 - INFO - RESULTADOS DEL FILTRADO:
2025-10-26 08:00:02 - INFO -   - Facturas válidas: 132
2025-10-26 08:00:02 - INFO -   - Notas crédito: 8
2025-10-26 08:00:02 - INFO -   - Facturas rechazadas: 16
2025-10-26 08:00:02 - INFO - ============================================================
2025-10-26 08:00:03 - INFO - Notas crédito nuevas registradas: 8
2025-10-26 08:00:04 - INFO - Nota N00456 aplicada a factura F12345: $1,250,000.00
2025-10-26 08:00:04 - INFO - 
============================================================
2025-10-26 08:00:04 - INFO - APLICACIONES DE NOTAS CRÉDITO:
2025-10-26 08:00:04 - INFO -   Total de aplicaciones realizadas: 5
2025-10-26 08:00:04 - INFO - ============================================================
2025-10-26 08:00:05 - INFO - Excel generado exitosamente
2025-10-26 08:00:06 - INFO - Correo enviado exitosamente
2025-10-26 08:00:06 - INFO - 
============================================================
2025-10-26 08:00:06 - INFO - PROCESO COMPLETADO EXITOSAMENTE
2025-10-26 08:00:06 - INFO - ============================================================
```

## 📊 Logging y Auditoría

### Archivos Generados

1. **facturas_YYYYMMDD.xlsx**: Facturas válidas procesadas
2. **facturas_rechazadas_YYYYMMDD.txt**: Detalle de facturas rechazadas
3. **reporte_notas_credito_YYYYMMDD.txt**: Resumen y aplicaciones de notas

### Métricas Registradas

- Total de facturas obtenidas
- Facturas válidas vs rechazadas
- Razones de rechazo
- Notas crédito identificadas y registradas
- Aplicaciones realizadas
- Saldos pendientes
- Tiempos de ejecución

## 🔧 Mantenimiento

### Limpieza de Base de Datos

```python
# Eliminar notas aplicadas hace más de 6 meses
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('./data/notas_credito.db')
cursor = conn.cursor()

fecha_limite = datetime.now() - timedelta(days=180)
cursor.execute('''
    DELETE FROM aplicaciones_notas 
    WHERE fecha_aplicacion < ?
''', (fecha_limite,))

conn.commit()
conn.close()
```

### Respaldo de Base de Datos

```bash
# Crear respaldo
cp ./data/notas_credito.db ./data/backup_notas_credito_$(date +%Y%m%d).db

# O programar con cron (Linux)
0 2 * * 0 cp /path/to/cipa/data/notas_credito.db /path/to/backup/notas_$(date +\%Y\%m\%d).db
```

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto es propiedad de COMPAÑÍA INDUSTRIAL DE PRODUCTOS AGROPECUARIOS S.A.

## 📧 Contacto

Para soporte o consultas, contactar al equipo de TI.

---

**Versión**: 2.0  
**Última Actualización**: Octubre 2025  
**Autor**: Equipo de Desarrollo CIPA
