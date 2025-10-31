# Colección de Postman - API CIPA

Esta carpeta contiene la colección completa de Postman para probar la API REST de Notas de Crédito.

## 📁 Archivos

- `CIPA_API_Collection.postman_collection.json` - Colección completa con todos los endpoints
- `CIPA_API_Environment.postman_environment.json` - Variables de entorno
- `README.md` - Este archivo

## 🚀 Instrucciones de Importación

### Método 1: Importar directamente

1. Abrir Postman
2. Click en **Import** (botón superior izquierdo)
3. Arrastrar los dos archivos JSON a la ventana de importación:
   - `CIPA_API_Collection.postman_collection.json`
   - `CIPA_API_Environment.postman_environment.json`
4. Click en **Import**

### Método 2: Desde archivo

1. Abrir Postman
2. Click en **Import** > **Upload Files**
3. Seleccionar ambos archivos JSON
4. Click en **Import**

## 🔧 Configuración

### 1. Seleccionar Environment

Después de importar, seleccionar el environment **"CIPA API - Local"** en el selector de environments (esquina superior derecha).

### 2. Iniciar la API

```bash
# Asegurarse de que la API esté corriendo
cd /home/user/cipa
python api/app.py
```

La API debe estar corriendo en `http://localhost:5000`

### 3. Primer Request - Login

1. Ir a la carpeta **"Autenticación"**
2. Ejecutar el request **"Login"**
3. Los tokens se guardarán automáticamente en las variables de entorno

✅ **¡Ya puedes usar todos los demás endpoints!**

## 📚 Estructura de la Colección

```
CIPA - API Notas de Crédito/
├── Autenticación/
│   ├── Login                    (POST /api/auth/login)
│   ├── Refresh Token            (POST /api/auth/refresh)
│   ├── Logout                   (POST /api/auth/logout)
│   └── Cambiar Contraseña       (POST /api/auth/change-password)
│
├── Notas de Crédito/
│   ├── Listar Todas las Notas   (GET /api/notas)
│   ├── Listar Notas PENDIENTES  (GET /api/notas?estado=PENDIENTE)
│   ├── Listar Notas APLICADAS   (GET /api/notas?estado=APLICADA)
│   ├── Filtrar por NIT Cliente  (GET /api/notas?nit_cliente=...)
│   ├── Filtrar por Fechas       (GET /api/notas?fecha_desde=...&fecha_hasta=...)
│   ├── Filtros Combinados       (GET /api/notas?estado=...&nit_cliente=...)
│   ├── Obtener Nota por ID      (GET /api/notas/:id)
│   ├── Notas por Estado         (GET /api/notas/por-estado)
│   └── Estadísticas Generales   (GET /api/notas/estadisticas)
│
├── Aplicaciones/
│   └── Obtener Aplicaciones     (GET /api/aplicaciones/:numero_nota)
│
├── Archivo/
│   └── Estadísticas del Archivo (GET /api/archivo/estadisticas)
│
└── Health Check/
    └── Health Check             (GET /api/health)
```

## 🔑 Autenticación

### Credenciales por Defecto

```
Username: admin
Password: admin123
```

⚠️ **IMPORTANTE:** Cambiar la contraseña después del primer login usando el endpoint "Cambiar Contraseña"

### Flujo de Autenticación

1. **Login** → Obtiene `access_token` y `refresh_token`
2. Usar `access_token` en todos los requests (se agrega automáticamente)
3. Cuando expire (1 hora), usar **Refresh Token** para obtener nuevo `access_token`
4. **Logout** para cerrar sesión

### Variables Automáticas

Los siguientes valores se guardan automáticamente después del login:

- `access_token` - Token de acceso (válido 1 hora)
- `refresh_token` - Token de renovación (válido 30 días)
- `user_id` - ID del usuario
- `username` - Nombre de usuario
- `user_rol` - Rol del usuario (admin, editor, viewer)

## 📋 Ejemplos de Uso

### 1. Login y Consultar Estadísticas

```
1. Ejecutar: Autenticación > Login
2. Ejecutar: Notas de Crédito > Estadísticas Generales
```

### 2. Listar Notas Pendientes de un Cliente

```
1. Ejecutar: Autenticación > Login
2. Editar: Notas de Crédito > Filtros Combinados
   - Cambiar nit_cliente por el deseado
3. Ejecutar el request
```

### 3. Ver Detalles de una Nota Específica

```
1. Ejecutar: Autenticación > Login
2. Editar: Notas de Crédito > Obtener Nota por ID
   - Cambiar el ID en la URL (ej: /api/notas/5)
3. Ejecutar el request
```

### 4. Ver Aplicaciones de una Nota

```
1. Ejecutar: Autenticación > Login
2. Editar: Aplicaciones > Obtener Aplicaciones
   - Cambiar el número de nota (ej: NME4906)
3. Ejecutar el request
```

## 🎯 Parámetros de Query Disponibles

### GET /api/notas

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `estado` | string | Filtrar por estado | PENDIENTE, PARCIAL, APLICADA |
| `nit_cliente` | string | Filtrar por NIT | 890912426 |
| `fecha_desde` | date | Fecha inicio | 2025-10-01 |
| `fecha_hasta` | date | Fecha fin | 2025-10-31 |
| `limite` | integer | Máximo resultados | 50 (default: 100) |
| `offset` | integer | Paginación | 0 (default: 0) |

**Ejemplos:**

```
# Solo pendientes
GET /api/notas?estado=PENDIENTE

# Cliente específico
GET /api/notas?nit_cliente=890912426

# Rango de fechas
GET /api/notas?fecha_desde=2025-10-01&fecha_hasta=2025-10-31

# Combinado con paginación
GET /api/notas?estado=PENDIENTE&nit_cliente=890912426&limite=20&offset=0
```

## 🔍 Tests Automáticos

La colección incluye tests automáticos que se ejecutan después de cada request:

### Login
- ✅ Guarda automáticamente `access_token` y `refresh_token`
- ✅ Guarda información del usuario
- ✅ Muestra logs en la consola de Postman

### Refresh Token
- ✅ Actualiza automáticamente el `access_token`

Para ver los logs:
1. Abrir la consola de Postman (View > Show Postman Console)
2. Ejecutar cualquier request
3. Ver los logs en la consola

## 🛠️ Personalización

### Cambiar URL Base

Si la API está en otro puerto o servidor:

1. Ir a Environments
2. Seleccionar "CIPA API - Local"
3. Editar `base_url`
4. Guardar

### Crear Environment de Producción

1. Duplicar "CIPA API - Local"
2. Renombrar a "CIPA API - Production"
3. Cambiar `base_url` a la URL de producción
4. Guardar

## 📊 Respuestas Esperadas

### Login Exitoso (200)
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

### Listar Notas (200)
```json
{
  "notas": [
    {
      "id": 1,
      "numero_nota": "NME4906",
      "fecha_nota": "2025-10-27",
      "nit_cliente": "890912426",
      "nombre_cliente": "PEREZ Y CARDONA S.A.S.",
      "valor_total": -500000.0,
      "saldo_pendiente": -500000.0,
      "estado": "PENDIENTE",
      ...
    }
  ],
  "total": 93,
  "limite": 50,
  "offset": 0,
  "total_paginas": 2
}
```

### Estadísticas (200)
```json
{
  "total_notas": 93,
  "por_estado": {
    "PENDIENTE": {
      "cantidad": 88,
      "saldo": -24223463.0
    }
  },
  "total_aplicaciones": 127,
  "valor_total_pendiente": -25723463.0
}
```

## ⚠️ Errores Comunes

### 401 Unauthorized
- **Causa:** Token inválido o expirado
- **Solución:** Ejecutar "Login" nuevamente o "Refresh Token"

### 404 Not Found
- **Causa:** Endpoint incorrecto o recurso no existe
- **Solución:** Verificar la URL

### 429 Too Many Requests
- **Causa:** Límite de rate limiting excedido
- **Solución:** Esperar unos segundos y reintentar

### 500 Internal Server Error
- **Causa:** Error en el servidor
- **Solución:** Verificar logs de la API

## 🎓 Tips

1. **Usa la carpeta Run** - Puedes ejecutar toda la colección de una vez:
   - Click derecho en "CIPA - API Notas de Crédito"
   - Seleccionar "Run folder"

2. **Guarda ejemplos** - Después de ejecutar un request exitoso:
   - Click en "Save Response"
   - Click en "Save as Example"

3. **Variables dinámicas** - Puedes usar variables de Postman:
   ```
   {{$timestamp}}  - Timestamp actual
   {{$randomInt}}  - Número aleatorio
   ```

4. **Organiza en Workspace** - Crea un workspace dedicado para CIPA

## 📞 Soporte

Si encuentras algún problema:

1. Verificar que la API esté corriendo (`http://localhost:5000/api/health`)
2. Verificar que el environment esté seleccionado
3. Verificar los logs de Postman Console
4. Verificar los logs de la API

## 📝 Changelog

### v1.0.0 - 2025-10-31
- ✨ Colección inicial con todos los endpoints
- ✨ Environment con variables automáticas
- ✨ Tests automáticos para guardar tokens
- ✨ Documentación completa de cada endpoint

---

**Autor:** Sistema CIPA
**Fecha:** 31 de Octubre 2025
**Versión:** 1.0.0
