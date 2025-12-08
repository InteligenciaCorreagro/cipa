# CIPA - Sistema de Gestión de Notas Crédito

Sistema para gestión y aplicación automática de notas crédito a facturas.

## Estructura del Proyecto

```
cipa/
├── backend/
│   ├── api/            # API REST (Flask)
│   │   ├── app.py      # Endpoints principales
│   │   └── auth.py     # Autenticación JWT
│   ├── core/           # Lógica de negocio
│   │   ├── api_client.py           # Cliente API externa
│   │   ├── business_rules.py       # Reglas de negocio
│   │   ├── email_sender.py         # Envío de correos
│   │   ├── excel_processor.py      # Procesamiento Excel
│   │   └── notas_credito_manager.py # Gestión de notas
│   ├── config/         # Configuración
│   └── main.py         # Proceso principal
├── frontend/           # Dashboard React + Vite
├── data/               # Base de datos SQLite
└── .github/workflows/  # GitHub Actions
```

## Base de Datos

### Tablas Principales

**facturas** - Líneas de facturas válidas
- `numero_linea` - Identificador de línea (ej: fem2020)
- `producto`, `codigo_producto` - Datos del producto
- `cantidad_original`, `precio_unitario`, `valor_total` - Valores originales
- `nota_aplicada` - Si tiene nota aplicada (0/1)
- `descuento_cantidad`, `descuento_valor` - Descuentos aplicados
- `cantidad_restante`, `valor_restante` - Saldos después de nota

**facturas_rechazadas** - Facturas que no cumplen reglas
- `razon_rechazo` - Razón del rechazo

**notas_credito** - Notas de crédito válidas
- `saldo_pendiente`, `cantidad_pendiente` - Saldos por aplicar
- `estado` - PENDIENTE, PARCIAL, APLICADA

**usuarios** - Usuarios del dashboard

## Reglas de Aplicación de Notas

Una nota se puede aplicar a una factura SOLO si:

1. **Cantidad nota <= Cantidad factura**
2. **Valor nota <= Valor factura**

Ejemplo:
- Factura: cantidad=25, valor=$100,000
- Nota: cantidad=24, valor=$96,000 -> Se aplica
- Nota: cantidad=24, valor=$101,000 -> NO se aplica (valor excede)

Después de aplicar:
- Factura queda con cantidad_restante=1, valor_restante=$4,000

## Instalación

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### API
```bash
cd backend/api
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Variables de Entorno

```env
# API Externa
CONNI_KEY=tu_key
CONNI_TOKEN=tu_token

# Base de datos
DB_PATH=./data/notas_credito.db

# JWT
JWT_SECRET_KEY=tu_secret_key

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=tu_email
EMAIL_PASSWORD=tu_password
DESTINATARIOS=email1@ejemplo.com,email2@ejemplo.com
```

## API Endpoints

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/logout` - Cerrar sesión
- `POST /api/auth/refresh` - Renovar token

### Facturas
- `GET /api/facturas` - Listar facturas
- `GET /api/facturas/:id` - Detalle factura
- `GET /api/facturas/estadisticas` - Estadísticas
- `GET /api/facturas/rechazadas` - Facturas rechazadas

### Notas Crédito
- `GET /api/notas` - Listar notas
- `GET /api/notas/:id` - Detalle nota
- `GET /api/notas/estadisticas` - Estadísticas

### Dashboard
- `GET /api/dashboard` - Datos del dashboard
- `GET /api/reporte/operativo` - Reporte diario

## Credenciales por defecto

- Usuario: `admin`
- Password: `admin123`

**Importante:** Cambiar la contraseña en producción.
