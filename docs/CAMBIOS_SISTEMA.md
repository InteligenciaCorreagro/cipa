# Resumen de Cambios al Sistema - 31 de Octubre 2025

## 🎯 Objetivos Completados

1. ✅ Agregar validación de tipos de inventario en notas de crédito
2. ✅ Implementar sistema de archivado para controlar tamaño de BD
3. ✅ Crear API REST para consultar notas por estado
4. ✅ Implementar API de autenticación con seguridad reforzada

---

## 📋 Cambios Realizados

### 1. Validación de Tipos de Inventario en Notas de Crédito

#### **Problema Identificado**
Las notas de crédito con tipos de inventario inválidos (DESCESPEC, DESCUENTO) no se filtraban correctamente porque se separaban por prefijo ANTES de validar el tipo.

#### **Solución Implementada**

**A. Migración de Base de Datos**
- ✅ Agregado campo `tipo_inventario` a tabla `notas_credito`
- ✅ Script de migración: `migrar_agregar_tipo_inventario.py`
- ✅ Backup automático antes de migración

**B. Actualización de Código**

**Archivo:** `src/notas_credito_manager.py`
- ✅ Líneas 169-171: Extracción de tipo de inventario de la API
- ✅ Líneas 185-193: Inclusión de tipo en INSERT de notas

**Archivo:** `src/business_rules.py`
- ✅ Líneas 208-220: Validación de tipo en notas de crédito
- ✅ Rechazo automático de notas con tipos excluidos

**C. Scripts de Limpieza**

**`limpiar_notas_invalidas.py`**
- Busca y elimina notas con tipos de inventario inválidos
- Soporta modo `--dry-run` para previsualización
- Identifica notas sin tipo con nombres sospechosos
- Genera reportes detallados

**Resultado Actual:**
- 37 notas encontradas con "DESCUENTO" en el nombre (sin tipo asignado)
- Total: $-24,223,463.00
- Pendiente de decisión: ¿Eliminar estas notas?

---

### 2. Sistema de Archivado de Notas Aplicadas

#### **Problema**
La base de datos puede crecer indefinidamente con notas completamente aplicadas, causando:
- Aumento de tamaño en GitHub
- Saturación de GitHub Actions artifacts
- Lentitud en consultas

#### **Solución Implementada**

**Módulo:** `src/archivador_notas.py`

**Características:**
- ✅ Base de datos separada para archivo (`data/archivo_notas.db`)
- ✅ Archivado automático de notas APLICADAS después de N días
- ✅ Tabla de metadata para auditoría
- ✅ Cálculo de espacio liberado
- ✅ Función de restauración de notas archivadas

**Estructura de Archivo:**
```
data/archivo_notas.db
├── notas_archivadas
├── aplicaciones_archivadas
└── metadata_archivado
```

**Script:** `archivar_notas.py`

```bash
# Ver estadísticas del archivo
python3 archivar_notas.py --stats

# Modo dry-run (sin cambios)
python3 archivar_notas.py --dry-run --dias-min 30

# Archivar notas aplicadas hace más de 30 días
python3 archivar_notas.py --dias-min 30
```

**Beneficios:**
- 📉 Reduce tamaño de BD principal
- 🚀 Mejora rendimiento de consultas
- 📦 Control de artifacts en GitHub Actions
- 📊 Mantiene historial completo en archivo

---

### 3. API REST para Consultas de Notas

#### **Tecnologías**
- Flask 3.0
- Flask-JWT-Extended (autenticación)
- Flask-Limiter (rate limiting)
- Flask-CORS (CORS)
- bcrypt (hash de contraseñas)

#### **Endpoints Implementados**

**Autenticación:**
- `POST /api/auth/login` - Login con JWT
- `POST /api/auth/refresh` - Renovar token
- `POST /api/auth/logout` - Cerrar sesión
- `POST /api/auth/change-password` - Cambiar contraseña

**Notas:**
- `GET /api/notas` - Listar con filtros (estado, NIT, fechas)
- `GET /api/notas/<id>` - Detalles de nota específica
- `GET /api/notas/por-estado` - Agrupadas por estado
- `GET /api/notas/estadisticas` - Estadísticas generales
- `GET /api/aplicaciones/<numero_nota>` - Aplicaciones de nota

**Archivo:**
- `GET /api/archivo/estadisticas` - Stats del archivo

**Health:**
- `GET /api/health` - Health check

#### **Seguridad Implementada**

**1. Autenticación JWT**
- Access Token: 1 hora de validez
- Refresh Token: 30 días de validez
- Tokens firmados con clave secreta configurable

**2. Hash de Contraseñas**
- bcrypt con salt automático
- No se almacenan contraseñas en texto plano

**3. Rate Limiting**
- Login: 5 intentos/minuto por IP
- Endpoints generales: 50 req/hora, 200 req/día
- Endpoints de notas: 100 req/minuto

**4. Bloqueo de Usuarios**
- Bloqueo temporal de 15 minutos después de 5 intentos fallidos
- Contador de intentos fallidos
- Registro de todos los intentos de login

**5. Auditoría**
- Tabla `intentos_login` con timestamp, IP, resultado
- Tabla `sesiones` para tracking de tokens activos
- Registro de último acceso por usuario

#### **Usuario por Defecto**
```
Username: admin
Password: admin123
```

⚠️ **IMPORTANTE:** Cambiar contraseña inmediatamente usando `/api/auth/change-password`

#### **Configuración**

**Archivo:** `.env` (crear desde `.env.example`)

```env
# JWT Secret Key - CAMBIAR EN PRODUCCIÓN
JWT_SECRET_KEY=tu-clave-secreta-muy-segura

# Puerto de la API
API_PORT=5000

# Modo debug
DEBUG=False
```

#### **Ejecutar API**

```bash
# Instalar dependencias
pip install -r api/requirements.txt

# Ejecutar
python api/app.py
```

**URL:** `http://localhost:5000`

#### **Ejemplo de Uso**

```python
import requests

# Login
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
access_token = response.json()['access_token']

# Consultar notas pendientes
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(
    'http://localhost:5000/api/notas',
    params={'estado': 'PENDIENTE', 'limite': 10},
    headers=headers
)
print(response.json())
```

---

## 📁 Estructura de Archivos Nuevos/Modificados

### Nuevos Archivos

```
.
├── api/
│   ├── __init__.py               # Package init
│   ├── app.py                    # API REST principal
│   ├── auth.py                   # Gestor de autenticación
│   ├── requirements.txt          # Dependencias de la API
│   └── README.md                 # Documentación de la API
├── src/
│   └── archivador_notas.py       # Sistema de archivado
├── migrar_agregar_tipo_inventario.py   # Migración de BD
├── limpiar_notas_invalidas.py          # Limpieza de notas
├── archivar_notas.py                   # Script de archivado
├── .env.example                        # Ejemplo de configuración
└── CAMBIOS_SISTEMA.md                  # Este archivo
```

### Archivos Modificados

```
src/notas_credito_manager.py    # Agregar tipo_inventario
src/business_rules.py           # Validar tipos en notas
.gitignore                      # Ignorar archivo y .env
```

---

## 🗄️ Cambios en Base de Datos

### Tabla `notas_credito`
```sql
ALTER TABLE notas_credito ADD COLUMN tipo_inventario TEXT;
CREATE INDEX idx_notas_tipo_inventario ON notas_credito(tipo_inventario);
```

### Nuevas Tablas de Autenticación

```sql
-- Usuarios
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    email TEXT,
    rol TEXT DEFAULT 'viewer',
    activo INTEGER DEFAULT 1,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP,
    ultimo_acceso TIMESTAMP,
    fecha_creacion TIMESTAMP
);

-- Sesiones
CREATE TABLE sesiones (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    token_jti TEXT UNIQUE,
    refresh_jti TEXT UNIQUE,
    ip_address TEXT,
    user_agent TEXT,
    fecha_creacion TIMESTAMP,
    fecha_expiracion TIMESTAMP,
    activa INTEGER DEFAULT 1
);

-- Intentos de login
CREATE TABLE intentos_login (
    id INTEGER PRIMARY KEY,
    username TEXT,
    ip_address TEXT,
    exitoso INTEGER,
    razon_fallo TEXT,
    fecha TIMESTAMP
);
```

### Nueva Base de Datos: `archivo_notas.db`

```sql
-- Notas archivadas
CREATE TABLE notas_archivadas (
    -- Misma estructura que notas_credito
    -- + fecha_archivado
);

-- Aplicaciones archivadas
CREATE TABLE aplicaciones_archivadas (
    -- Misma estructura que aplicaciones_notas
    -- + fecha_archivado
);

-- Metadata
CREATE TABLE metadata_archivado (
    id INTEGER PRIMARY KEY,
    fecha_archivado TIMESTAMP,
    notas_archivadas INTEGER,
    aplicaciones_archivadas INTEGER,
    espacio_liberado_bytes INTEGER,
    notas_restantes INTEGER
);
```

---

## 🚀 Próximos Pasos Recomendados

### Inmediatos

1. **Cambiar contraseña del admin**
   ```bash
   curl -X POST http://localhost:5000/api/auth/change-password \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"nueva_contraseña": "nueva-contraseña-segura"}'
   ```

2. **Configurar JWT_SECRET_KEY en producción**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   # Copiar resultado a .env
   ```

3. **Decidir sobre las 37 notas con DESCUENTO**
   - Revisar: `python3 limpiar_notas_invalidas.py --dry-run`
   - Eliminar si es apropiado: `python3 limpiar_notas_invalidas.py`

### Mantenimiento

4. **Configurar archivado automático (cron)**
   ```bash
   # Ejecutar mensualmente
   0 2 1 * * cd /home/user/cipa && python3 archivar_notas.py --dias-min 30
   ```

5. **Crear usuarios adicionales**
   ```python
   from api.auth import AuthManager
   auth = AuthManager()
   auth.crear_usuario('usuario', 'contraseña', 'email@cipa.com', 'viewer')
   ```

6. **Monitoreo de intentos de login**
   ```sql
   SELECT username, COUNT(*) as intentos_fallidos
   FROM intentos_login
   WHERE exitoso = 0 AND fecha > datetime('now', '-1 day')
   GROUP BY username
   ORDER BY intentos_fallidos DESC;
   ```

### Mejoras Futuras

7. **Agregar endpoint para crear notas manualmente**
8. **Implementar paginación en más endpoints**
9. **Agregar webhooks para notificaciones**
10. **Dashboard web para visualización**

---

## 📊 Estadísticas del Sistema

### Estado Actual

- **Notas en BD principal:** 93
- **Notas con tipo inválido:** 37 (pendiente decisión)
- **Notas archivadas:** 0 (sistema recién implementado)
- **Usuarios creados:** 1 (admin)

### Métricas de Seguridad

- **Rate limiting:** Activo
- **Bloqueo temporal:** Activo (5 intentos, 15 min)
- **Hash de contraseñas:** bcrypt
- **Tokens JWT:** Activos (1h access, 30d refresh)

---

## 🐛 Troubleshooting

### API no inicia
- Verificar que `JWT_SECRET_KEY` está configurado en `.env`
- Verificar que el puerto 5000 está disponible
- Instalar dependencias: `pip install -r api/requirements.txt`

### Error "Token inválido"
- Token expirado: usar `/api/auth/refresh`
- Token malformado: verificar header `Authorization: Bearer <token>`

### Usuario bloqueado
- Esperar 15 minutos
- O desbloquear manualmente:
  ```sql
  UPDATE usuarios SET bloqueado_hasta = NULL, intentos_fallidos = 0 WHERE username = 'user';
  ```

---

## 📝 Documentación Adicional

- **API REST:** Ver `api/README.md` para documentación completa de endpoints
- **Archivado:** Ver código en `src/archivador_notas.py` para detalles técnicos
- **Autenticación:** Ver código en `api/auth.py` para lógica de seguridad

---

## ✅ Checklist de Deployment

- [ ] Cambiar contraseña de admin
- [ ] Configurar JWT_SECRET_KEY en .env
- [ ] Revisar y eliminar notas inválidas si es necesario
- [ ] Configurar cron para archivado automático
- [ ] Crear usuarios adicionales según necesidad
- [ ] Configurar CORS en api/app.py para dominio específico
- [ ] Configurar proxy reverso (nginx) si es necesario
- [ ] Configurar SSL/TLS para HTTPS
- [ ] Configurar backup automático de BD
- [ ] Documentar procedimientos operativos

---

**Fecha de Cambios:** 31 de Octubre 2025
**Autor:** Claude
**Versión del Sistema:** 2.0
