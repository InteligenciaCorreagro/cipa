# API REST - Sistema de Notas de Crédito CIPA

API RESTful para consulta y gestión de notas de crédito con autenticación JWT y seguridad reforzada.

## 🚀 Características

- ✅ Autenticación JWT con refresh tokens
- ✅ Rate limiting por IP
- ✅ Bloqueo temporal después de intentos fallidos
- ✅ Hash bcrypt para contraseñas
- ✅ Registro de intentos de login
- ✅ Consulta de notas por estado
- ✅ Estadísticas y reportes
- ✅ CORS configurado
- ✅ Endpoints documentados

## 📦 Instalación

### 1. Instalar dependencias

```bash
cd api
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

Editar `.env`:

```env
# IMPORTANTE: Cambiar en producción
JWT_SECRET_KEY=tu-clave-secreta-muy-segura-y-aleatoria

# Puerto de la API
API_PORT=5000

# Modo debug (solo desarrollo)
DEBUG=False
```

### 3. Inicializar base de datos

La API inicializa automáticamente las tablas de autenticación al arrancar.

**Usuario por defecto:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANTE:** Cambiar la contraseña inmediatamente usando el endpoint `/api/auth/change-password`

## 🏃 Ejecutar API

```bash
python api/app.py
```

La API estará disponible en `http://localhost:5000`

## 📚 Endpoints

### Autenticación

#### `POST /api/auth/login`

Autenticación de usuario.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "usuario": {
    "id": 1,
    "username": "admin",
    "email": "admin@cipa.com",
    "rol": "admin"
  }
}
```

#### `POST /api/auth/refresh`

Renovar access token usando refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### `POST /api/auth/logout`

Cerrar sesión.

**Headers:**
```
Authorization: Bearer <access_token>
```

#### `POST /api/auth/change-password`

Cambiar contraseña del usuario actual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "nueva_contraseña": "mi-nueva-contraseña-segura"
}
```

---

### Notas de Crédito

Todos los endpoints requieren autenticación (header `Authorization: Bearer <token>`)

#### `GET /api/notas`

Listar notas con filtros opcionales.

**Query Parameters:**
- `estado`: PENDIENTE, PARCIAL, APLICADA
- `nit_cliente`: Filtrar por NIT
- `fecha_desde`: YYYY-MM-DD
- `fecha_hasta`: YYYY-MM-DD
- `limite`: Máximo de resultados (default: 100)
- `offset`: Paginación (default: 0)

**Ejemplo:**
```
GET /api/notas?estado=PENDIENTE&limite=50&offset=0
```

**Response:**
```json
{
  "notas": [
    {
      "id": 1,
      "numero_nota": "NME4906",
      "fecha_nota": "2025-10-27",
      "nit_cliente": "890912426",
      "nombre_cliente": "PEREZ Y CARDONA S.A.S.",
      "codigo_producto": "",
      "nombre_producto": "PRODUCTO EJEMPLO",
      "tipo_inventario": "VENTA",
      "valor_total": -500000.0,
      "saldo_pendiente": -500000.0,
      "estado": "PENDIENTE",
      "fecha_registro": "2025-10-28 18:19:51"
    }
  ],
  "total": 93,
  "limite": 50,
  "offset": 0,
  "total_paginas": 2
}
```

#### `GET /api/notas/<id>`

Obtener detalles de una nota específica incluyendo sus aplicaciones.

**Response:**
```json
{
  "nota": {
    "id": 1,
    "numero_nota": "NME4906",
    ...
  },
  "aplicaciones": [
    {
      "id": 1,
      "numero_factura": "FV12345",
      "valor_aplicado": -100000.0,
      "fecha_aplicacion": "2025-10-28 10:30:00"
    }
  ]
}
```

#### `GET /api/notas/por-estado`

Obtener resumen de notas agrupadas por estado.

**Response:**
```json
{
  "estados": [
    {
      "estado": "PENDIENTE",
      "cantidad": 93,
      "saldo_total": -24223463.0
    },
    {
      "estado": "PARCIAL",
      "cantidad": 5,
      "saldo_total": -1500000.0
    }
  ]
}
```

#### `GET /api/notas/estadisticas`

Obtener estadísticas generales del sistema.

**Response:**
```json
{
  "total_notas": 93,
  "por_estado": {
    "PENDIENTE": {
      "cantidad": 88,
      "saldo": -24223463.0
    },
    "PARCIAL": {
      "cantidad": 5,
      "saldo": -1500000.0
    }
  },
  "total_aplicaciones": 127,
  "valor_total_pendiente": -25723463.0
}
```

#### `GET /api/aplicaciones/<numero_nota>`

Obtener todas las aplicaciones de una nota específica.

**Ejemplo:**
```
GET /api/aplicaciones/NME4906
```

**Response:**
```json
{
  "aplicaciones": [
    {
      "id": 1,
      "numero_factura": "FV12345",
      "fecha_factura": "2025-10-20",
      "nit_cliente": "890912426",
      "codigo_producto": "PROD001",
      "valor_aplicado": -100000.0,
      "cantidad_aplicada": -100000.0,
      "fecha_aplicacion": "2025-10-28 10:30:00"
    }
  ]
}
```

---

### Archivo

#### `GET /api/archivo/estadisticas`

Obtener estadísticas del archivo de notas aplicadas.

**Response:**
```json
{
  "total_notas_archivadas": 250,
  "total_aplicaciones_archivadas": 1500,
  "ultimo_archivado": "2025-10-30 12:00:00",
  "total_operaciones_archivado": 5,
  "tamano_archivo_mb": 12.5
}
```

---

### Health Check

#### `GET /api/health`

Verificar estado de la API (no requiere autenticación).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T16:00:00",
  "version": "1.0.0"
}
```

## 🔐 Seguridad

### Rate Limiting

- **Login**: 5 intentos por minuto por IP
- **Endpoints generales**: 50 requests por hora, 200 por día
- **Endpoints de notas**: 100 requests por minuto

### Bloqueo de Usuarios

- Después de 5 intentos fallidos, el usuario se bloquea por 15 minutos
- Los intentos se resetean después de un login exitoso

### Tokens JWT

- **Access Token**: Válido por 1 hora
- **Refresh Token**: Válido por 30 días

### Headers de Seguridad

Siempre incluir el token en las peticiones:

```
Authorization: Bearer <access_token>
```

## 📝 Ejemplos de Uso

### Python

```python
import requests

# Login
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})

tokens = response.json()
access_token = tokens['access_token']

# Consultar notas pendientes
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(
    'http://localhost:5000/api/notas',
    params={'estado': 'PENDIENTE', 'limite': 10},
    headers=headers
)

notas = response.json()
print(f"Total notas pendientes: {notas['total']}")
```

### cURL

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Consultar notas (reemplazar TOKEN)
curl -X GET "http://localhost:5000/api/notas?estado=PENDIENTE" \
  -H "Authorization: Bearer TOKEN"
```

### JavaScript

```javascript
// Login
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});

const { access_token } = await response.json();

// Consultar notas
const notasResponse = await fetch('http://localhost:5000/api/notas?estado=PENDIENTE', {
  headers: {'Authorization': `Bearer ${access_token}`}
});

const notas = await notasResponse.json();
console.log(notas);
```

## 🛠️ Mantenimiento

### Crear Nuevo Usuario

```python
from api.auth import AuthManager

auth = AuthManager()
auth.crear_usuario(
    username='usuario1',
    password='contraseña_segura',
    email='usuario1@cipa.com',
    rol='viewer'  # opciones: admin, editor, viewer
)
```

### Cambiar Rol de Usuario

Conectarse a la base de datos y ejecutar:

```sql
UPDATE usuarios SET rol = 'admin' WHERE username = 'usuario1';
```

### Desbloquear Usuario

```sql
UPDATE usuarios
SET bloqueado_hasta = NULL, intentos_fallidos = 0
WHERE username = 'usuario1';
```

## 📊 Monitoreo

### Ver Intentos de Login

```sql
SELECT * FROM intentos_login
WHERE fecha >= datetime('now', '-1 day')
ORDER BY fecha DESC;
```

### Ver Sesiones Activas

```sql
SELECT s.*, u.username
FROM sesiones s
JOIN usuarios u ON s.user_id = u.id
WHERE s.activa = 1
  AND s.fecha_expiracion > datetime('now')
ORDER BY s.fecha_creacion DESC;
```

## 🐛 Troubleshooting

### Error: "Token inválido"
- Verificar que el token no haya expirado
- Usar el endpoint `/api/auth/refresh` para obtener un nuevo token

### Error: "Usuario bloqueado"
- Esperar 15 minutos o desbloquear manualmente en la BD

### Error: "Rate limit exceeded"
- Reducir frecuencia de peticiones
- Contactar al administrador para ajustar límites

## 📄 Licencia

Uso interno de CIPA - Todos los derechos reservados
