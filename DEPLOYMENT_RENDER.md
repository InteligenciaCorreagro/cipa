# 🚀 Guía de Deployment en Render - Sistema CIPA

## 📋 Contenido

1. [Introducción](#introducción)
2. [Requisitos Previos](#requisitos-previos)
3. [Configuración Paso a Paso](#configuración-paso-a-paso)
4. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
5. [Configuración del Dominio](#configuración-del-dominio)
6. [Pruebas y Verificación](#pruebas-y-verificación)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Introducción

Esta guía te ayudará a desplegar el Sistema CIPA en Render de forma **completamente gratuita**. El sistema incluye:

- **Backend API** (Flask + Python) con autenticación JWT
- **Frontend** (React + TypeScript) con diseño moderno
- **Base de datos** SQLite con disco persistente

### ✨ Características del Plan Gratuito de Render

- ✅ 750 horas de ejecución al mes (suficiente para 1 servicio 24/7)
- ✅ 1 GB de disco persistente gratuito
- ✅ SSL/HTTPS automático
- ✅ Deploys automáticos desde GitHub
- ✅ Sin tarjeta de crédito requerida
- ⚠️ El servicio entra en suspensión después de 15 minutos de inactividad (se reactiva automáticamente en ~30 segundos)

---

## 📦 Requisitos Previos

1. **Cuenta de GitHub** con el repositorio del proyecto
2. **Cuenta de Render** (gratuita) - Regístrate en [render.com](https://render.com)
3. **Cuenta de GoDaddy** con el dominio `correagro.com`

---

## 🔧 Configuración Paso a Paso

### Paso 1: Preparar el Repositorio

1. Asegúrate de que todos los cambios estén commiteados y pusheados a GitHub:

```bash
git add .
git commit -m "🚀 Configuración para deployment en Render"
git push origin main
```

### Paso 2: Crear Servicios en Render

#### A. Backend API

1. **Accede a Render Dashboard**: https://dashboard.render.com
2. **Clic en "New +"** → **"Web Service"**
3. **Conectar GitHub**:
   - Autoriza Render para acceder a tu repositorio
   - Selecciona el repositorio `cipa`
4. **Configuración del Servicio**:
   - **Name**: `cipa-backend`
   - **Region**: `Ohio` (más cercano a Colombia)
   - **Branch**: `main` (o tu rama principal)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && python scripts/inicializar_auth.py || echo "Auth ya inicializado"
     ```
   - **Start Command**:
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 api.app:app
     ```
   - **Instance Type**: `Free`

5. **Variables de Entorno** (más detalles abajo):
   - Clic en "Advanced" → "Add Environment Variable"
   - Agregar las variables del Backend

6. **Agregar Disco Persistente**:
   - Clic en "Add Disk"
   - **Name**: `cipa-database`
   - **Mount Path**: `/opt/render/project/src/backend/data`
   - **Size**: `1 GB` (gratuito)

7. **Clic en "Create Web Service"**

⏱️ El deployment puede tardar 5-10 minutos. Una vez completado, obtendrás una URL como:
```
https://cipa-backend.onrender.com
```

#### B. Frontend (Static Site)

1. **Clic en "New +"** → **"Static Site"**
2. **Conectar al mismo repositorio** `cipa`
3. **Configuración del Servicio**:
   - **Name**: `cipa-frontend`
   - **Region**: `Ohio`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`

4. **Variables de Entorno** (ver sección abajo)

5. **Clic en "Create Static Site"**

⏱️ El build puede tardar 3-5 minutos. Obtendrás una URL como:
```
https://cipa-frontend.onrender.com
```

---

## 🔐 Configuración de Variables de Entorno

### Variables del Backend (cipa-backend)

En el dashboard de Render → **cipa-backend** → **Environment**:

```env
# JWT Secret (CRÍTICO - Generar uno único)
JWT_SECRET_KEY=<generar-secreto-aleatorio-seguro>

# API Configuration
API_PORT=5000
DEBUG=False
FLASK_ENV=production

# Database
DB_PATH=./data/notas_credito.db

# CORS (actualizar con URLs reales)
CORS_ORIGINS=https://cipa-frontend.onrender.com,https://correagro.com

# Python Version
PYTHON_VERSION=3.11.0
```

**🔑 Para generar un JWT_SECRET_KEY seguro:**

En tu terminal local:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copia el resultado y úsalo como `JWT_SECRET_KEY`.

### Variables del Frontend (cipa-frontend)

En el dashboard de Render → **cipa-frontend** → **Environment**:

```env
# URL del Backend (actualizar con la URL real de tu backend)
VITE_API_URL=https://cipa-backend.onrender.com

# Subpath (false para Render, true para dominio propio)
VITE_USE_SUBPATH=false

# Node Version
NODE_VERSION=18.17.0
```

---

## 🌐 Configuración del Dominio

Tienes **dos opciones** para usar el dominio `correagro.com/intranet/cipa`:

### Opción 1: Subdominio (Recomendada - Más Simple)

1. **En GoDaddy**:
   - Crear un subdominio: `cipa.correagro.com`
   - Agregar un registro CNAME:
     ```
     Tipo: CNAME
     Nombre: cipa
     Valor: cipa-frontend.onrender.com
     ```

2. **En Render** (cipa-frontend):
   - **Settings** → **Custom Domain**
   - Agregar: `cipa.correagro.com`
   - Seguir las instrucciones de verificación

3. **Usuarios accederán a**: `https://cipa.correagro.com`

### Opción 2: Subpath (Más Complejo - Requiere Proxy Reverso)

Para que funcione en `https://correagro.com/intranet/cipa`, necesitas configurar un **reverse proxy** en el servidor que aloja `correagro.com`.

**Ver archivo: [GODADDY_CONFIGURATION.md](./GODADDY_CONFIGURATION.md)** para instrucciones detalladas.

---

## ✅ Pruebas y Verificación

### 1. Verificar Backend

Abre en tu navegador:
```
https://cipa-backend.onrender.com/api/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T...",
  "version": "1.0.1",
  "jwt_configured": true
}
```

### 2. Verificar Frontend

Abre:
```
https://cipa-frontend.onrender.com
```

Deberías ver la pantalla de login.

### 3. Probar Login

**Credenciales por defecto**:
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANTE**: Cambia la contraseña inmediatamente después del primer login.

### 4. Verificar Conectividad

Después de hacer login, verifica que el dashboard carga las estadísticas correctamente.

---

## 🔍 Solución de Problemas

### ❌ Backend no inicia

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solución**: Verificar que `requirements.txt` esté completo:
```bash
Flask==3.0.0
flask-cors==4.0.0
flask-jwt-extended==4.6.0
Flask-Limiter==3.5.0
gunicorn==21.2.0
bcrypt==4.1.2
requests==2.31.0
openpyxl==3.1.2
python-dotenv==1.0.0
```

---

### ❌ Frontend no conecta al backend

**Error**: `Network Error` o `CORS Error`

**Solución 1**: Verificar `VITE_API_URL` en las variables de entorno del frontend:
```env
VITE_API_URL=https://cipa-backend.onrender.com
```

**Solución 2**: Verificar CORS en el backend. Editar `backend/api/app.py`:
```python
CORS(app, resources={r"/api/*": {
    "origins": ["https://cipa-frontend.onrender.com", "https://correagro.com"],
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Content-Type", "Authorization"]
}})
```

---

### ❌ Servicio suspendido (Cold Start)

**Síntoma**: Primera petición tarda ~30 segundos

**Explicación**: Los servicios gratuitos de Render entran en suspensión después de 15 minutos de inactividad.

**Soluciones**:

1. **Aceptar el delay** (solo en la primera petición)

2. **Usar un servicio de "keep-alive"** (gratis):
   - [UptimeRobot](https://uptimerobot.com/) - Ping cada 5 minutos
   - [Cron-job.org](https://cron-job.org/) - Ping programado

   Configurar para hacer ping a:
   ```
   https://cipa-backend.onrender.com/api/health
   ```

3. **Upgrade al plan Starter** ($7/mes) - sin suspensión

---

### ❌ Base de datos no persiste

**Problema**: Los datos se pierden en cada deploy

**Solución**: Verificar que el disco esté montado correctamente:

1. **En Render Dashboard** → **cipa-backend** → **Disks**
2. Verificar:
   ```
   Name: cipa-database
   Mount Path: /opt/render/project/src/backend/data
   ```

3. Verificar en logs que la BD se crea en la ruta correcta:
   ```bash
   # En los logs debería aparecer:
   Base de datos: /opt/render/project/src/backend/data/notas_credito.db
   ```

---

### ❌ Tokens JWT inválidos

**Error**: `Token inválido` o `JWT signature verification failed`

**Causa**: `JWT_SECRET_KEY` diferente entre deploys

**Solución**:
1. Generar un JWT_SECRET_KEY seguro:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

2. Configurarlo como **variable de entorno permanente** en Render (no en el código)

3. **NO cambiar** el JWT_SECRET_KEY una vez en producción (invalidará todas las sesiones activas)

---

### ❌ Error 403 en git push

**Problema**: No puedes pushear a la rama

**Solución**: Asegúrate de estar en la rama correcta:
```bash
git checkout claude/deploy-render-subdomain-setup-011CUzUPPSYeKVkb1rW91mtE
git add .
git commit -m "mensaje"
git push -u origin claude/deploy-render-subdomain-setup-011CUzUPPSYeKVkb1rW91mtE
```

---

## 📊 Monitoreo

### Logs en Tiempo Real

**Backend**:
```
Dashboard → cipa-backend → Logs
```

**Frontend**:
```
Dashboard → cipa-frontend → Deploy Logs
```

### Métricas

Render provee métricas básicas gratuitas:
- CPU usage
- Memory usage
- Request count
- Response times

---

## 🔄 Actualizaciones

Render hace **deploy automático** cuando pusheas a la rama `main`:

```bash
git add .
git commit -m "Actualización XYZ"
git push origin main
```

⏱️ El deploy tarda ~5 minutos en completarse.

---

## 🆘 Soporte

**Documentación de Render**: https://render.com/docs

**Community Forum**: https://community.render.com/

**Logs**: Siempre revisa los logs para diagnosticar problemas

---

## ✅ Checklist de Deployment

- [ ] Repositorio pusheado a GitHub
- [ ] Backend service creado en Render
- [ ] Variables de entorno del backend configuradas
- [ ] JWT_SECRET_KEY generado y configurado
- [ ] Disco persistente agregado (1GB)
- [ ] Backend desplegado exitosamente
- [ ] Frontend service creado en Render
- [ ] Variables de entorno del frontend configuradas
- [ ] Frontend desplegado exitosamente
- [ ] Endpoint `/api/health` responde correctamente
- [ ] Login funciona correctamente
- [ ] Dashboard carga estadísticas
- [ ] Dominio personalizado configurado (opcional)
- [ ] Keep-alive configurado (opcional)
- [ ] Contraseña de admin cambiada

---

## 🎉 ¡Listo!

Tu sistema CIPA ahora está desplegado en Render de forma gratuita con:

✅ SSL/HTTPS automático
✅ Deploys automáticos
✅ Base de datos persistente
✅ Autenticación segura JWT
✅ Monitoreo básico incluido

**URLs de acceso**:
- Backend: `https://cipa-backend.onrender.com`
- Frontend: `https://cipa-frontend.onrender.com`
- (O tu dominio personalizado)

---

**Última actualización**: 2025-11-10
