# Implementación: Sistema de Usuarios y Reportes Operativos

## 📋 Resumen de Implementación

Se implementaron las siguientes funcionalidades en el sistema CIPA:

### 1. ✅ Sistema de Guardado y Aplicación Automática de Notas
**Estado:** Ya implementado previamente en `backend/core/notas_credito_manager.py:670`

El sistema automáticamente:
- Registra notas de crédito en la base de datos
- Aplica notas pendientes a facturas que cumplen criterios (mismo cliente, mismo producto)
- Actualiza el saldo pendiente de las notas
- Marca las notas como APLICADA cuando su saldo llega a cero

### 2. 🔐 Backdoor para Creación de Usuarios con Vista

#### Backend API (backend/api/app.py)

**Nueva Ruta: POST /api/auth/register**
- Permite crear nuevos usuarios (solo administradores)
- Requiere autenticación JWT
- Valida permisos de rol
- Validaciones: username, password (mínimo 6 caracteres), rol válido

```bash
# Ejemplo de uso
curl -X POST http://localhost:2500/api/auth/register \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nuevo.usuario",
    "password": "password123",
    "email": "usuario@ejemplo.com",
    "rol": "viewer"
  }'
```

**Nueva Ruta: GET /api/auth/users**
- Lista todos los usuarios (solo administradores)
- Devuelve: id, username, email, rol, activo, ultimo_acceso, fecha_creacion

#### Frontend (frontend/src/pages/UserManagementPage.tsx)

Nueva página de gestión de usuarios con:
- Formulario para crear nuevos usuarios
- Selector de rol (Admin, Editor, Viewer)
- Tabla con lista de todos los usuarios
- Badges de colores por rol y estado
- Validaciones en tiempo real
- Solo accesible para usuarios con rol 'admin'

**Acceso:** http://localhost:5173/usuarios

### 3. 📊 Vista de Reporte Operativo

#### Backend API (backend/api/app.py)

**Nueva Ruta: GET /api/reporte/operativo**
- Obtiene datos equivalentes al reporte diario enviado a operativa
- Parámetro: `fecha` (opcional, por defecto ayer)
- Devuelve:
  - Notas de crédito del día
  - Aplicaciones de notas realizadas
  - Facturas rechazadas
  - Resumen general de notas (total, pendientes, aplicadas, saldo)

```bash
# Ejemplo de uso
curl -X GET "http://localhost:2500/api/reporte/operativo?fecha=2025-11-12" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

#### Frontend (frontend/src/pages/OperativeReportPage.tsx)

Nueva página de reporte operativo con:
- Selector de fecha para consultar reportes históricos
- 4 cards de resumen (Notas del día, Aplicaciones, Rechazadas, Saldo pendiente)
- 3 tabs con tablas detalladas:
  - **Notas de Crédito:** Número, fecha, cliente, producto, valores, estado
  - **Aplicaciones:** Nota aplicada, factura, valores, fecha de aplicación
  - **Facturas Rechazadas:** Número, cliente, producto, valor, razón de rechazo
- Card de resumen general del sistema
- Formato de moneda colombiana (COP)

**Acceso:** http://localhost:5173/reporte-operativo

### 4. 🧭 Navegación Actualizada

Actualizado el MainLayout (frontend/src/layouts/MainLayout.tsx):
- Nuevo menú: "Reporte Operativo" (todos los usuarios)
- Nuevo menú: "Gestión de Usuarios" (solo admins)
- Iconos: FileBarChart y Users (de lucide-react)
- Filtrado de menú por rol de usuario

## 🗂️ Archivos Modificados/Creados

### Backend
- ✅ `backend/api/app.py` - Agregadas 3 nuevas rutas API
  - POST /api/auth/register (línea 324)
  - GET /api/auth/users (línea 373)
  - GET /api/reporte/operativo (línea 418)

### Frontend
- ✅ `frontend/src/pages/UserManagementPage.tsx` - Nueva página (272 líneas)
- ✅ `frontend/src/pages/OperativeReportPage.tsx` - Nueva página (390 líneas)
- ✅ `frontend/src/App.tsx` - Agregadas rutas para nuevas páginas
- ✅ `frontend/src/layouts/MainLayout.tsx` - Actualizado menú de navegación

### Scripts
- ✅ `scripts/check_db_status.py` - Script para verificar estado de BD
- ✅ `scripts/view_db_schema.py` - Script para ver esquema de tablas
- ✅ `scripts/populate_historical_data.py` - Script para poblar datos históricos

## 🔑 Roles y Permisos

| Funcionalidad | Admin | Editor | Viewer |
|--------------|-------|--------|--------|
| Dashboard | ✅ | ✅ | ✅ |
| Consulta de Notas | ✅ | ✅ | ✅ |
| Reporte Operativo | ✅ | ✅ | ✅ |
| Gestión de Usuarios | ✅ | ❌ | ❌ |
| Crear Usuarios | ✅ | ❌ | ❌ |

## 📝 Credenciales por Defecto

```
Usuario: admin
Contraseña: admin123
Rol: admin
```

⚠️ **IMPORTANTE:** Cambiar la contraseña del usuario admin en producción.

## 🚀 Cómo Usar

### 1. Crear un Nuevo Usuario

1. Iniciar sesión como admin
2. Ir a "Gestión de Usuarios" en el menú lateral
3. Completar el formulario:
   - Usuario (requerido)
   - Email (opcional)
   - Contraseña (mínimo 6 caracteres)
   - Rol (Admin/Editor/Viewer)
4. Click en "Crear Usuario"

### 2. Ver Reporte Operativo

1. Ir a "Reporte Operativo" en el menú lateral
2. Seleccionar fecha (por defecto: ayer)
3. Click en "Consultar"
4. Revisar:
   - Cards de resumen
   - Tab "Notas de Crédito"
   - Tab "Aplicaciones"
   - Tab "Rechazadas"

### 3. Poblar Datos Históricos (Pendiente)

Para poblar datos del 10, 11, 12 de noviembre, necesitas:

1. Configurar credenciales de la API SIESA:
```bash
export CONNI_KEY="tu_key_aqui"
export CONNI_TOKEN="tu_token_aqui"
```

2. Ejecutar el script:
```bash
python3 scripts/populate_historical_data.py
```

**Nota:** Este script requiere acceso a las credenciales de GitHub Secrets que actualmente solo están disponibles en GitHub Actions.

## 📊 Base de Datos

### Tablas Relevantes

- `usuarios` - Usuarios del sistema con autenticación
- `notas_credito` - Notas de crédito registradas
- `aplicaciones_notas` - Aplicaciones de notas a facturas
- `facturas_rechazadas` - Facturas que no cumplen reglas de negocio

### Esquema de Notas

```sql
CREATE TABLE notas_credito (
    id INTEGER PRIMARY KEY,
    numero_nota TEXT NOT NULL,
    fecha_nota DATE NOT NULL,
    nit_cliente TEXT NOT NULL,
    nombre_cliente TEXT NOT NULL,
    codigo_producto TEXT NOT NULL,
    nombre_producto TEXT NOT NULL,
    valor_total REAL NOT NULL,
    cantidad REAL NOT NULL,
    saldo_pendiente REAL NOT NULL,
    cantidad_pendiente REAL NOT NULL,
    estado TEXT,  -- 'PENDIENTE' o 'APLICADA'
    fecha_registro TIMESTAMP,
    fecha_aplicacion_completa TIMESTAMP
);
```

## 🔄 Proceso Diario Automatizado

El sistema ejecuta automáticamente cada día a las 8:00 AM (hora Bogotá):

1. ✅ Obtiene facturas de la API SIESA
2. ✅ Filtra facturas según reglas de negocio
3. ✅ Registra notas de crédito nuevas
4. ✅ Aplica notas pendientes a facturas
5. ✅ Genera reportes Excel
6. ✅ Envía email a operativa
7. ✅ Guarda cambios en la base de datos
8. ✅ Hace commit al repositorio Git

## 🎯 Próximos Pasos

1. **Poblar Datos Históricos:** Ejecutar el script con las credenciales de la API para los días 10, 11, 12 de noviembre
2. **Testing:** Probar las nuevas funcionalidades en producción
3. **Seguridad:** Cambiar la contraseña del usuario admin
4. **Capacitación:** Entrenar a los usuarios en las nuevas funcionalidades

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python, Flask, SQLite, JWT, bcrypt
- **Frontend:** React, TypeScript, Tailwind CSS, shadcn/ui
- **API:** REST, autenticación JWT
- **Base de Datos:** SQLite con versionado en Git

## 📞 Soporte

Para cualquier duda o problema, revisar:
- Logs del backend en la consola
- Logs del frontend en la consola del navegador
- Base de datos en `data/notas_credito.db`
- GitHub Actions para el proceso automatizado

---

**Fecha de Implementación:** 2025-11-13
**Desarrollado por:** Claude (Anthropic)
