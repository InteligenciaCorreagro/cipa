# 🚀 Deployment en Render.com - Guía Completa

## ¡100% GRATIS! Sin Tarjeta de Crédito 💳

Esta guía te llevará paso a paso para desplegar CIPA en Render.com completamente **GRATIS** y configurarlo para el subpath `correagro.com/intranet/cipa`.

---

## 📋 Tabla de Contenidos

1. [¿Por qué Render?](#por-qué-render)
2. [Deployment Rápido](#deployment-rápido)
3. [Configuración Detallada](#configuración-detallada)
4. [Configuración de GoDaddy](#configuración-de-godaddy)
5. [Verificación](#verificación)
6. [Solución de Problemas](#solución-de-problemas)

---

## ✨ ¿Por qué Render?

✅ **100% gratis** sin tarjeta de crédito
✅ **750 horas/mes** de ejecución (suficiente para producción)
✅ **HTTPS automático** y renovación
✅ **Deploy desde GitHub** automático
✅ **Dockerfile support** nativo
✅ **Disco persistente** para SQLite gratis
✅ **Health checks** automáticos
✅ **Logs en tiempo real**

---

## 🚀 Deployment Rápido (5 Minutos)

### Paso 1: Crear Cuenta en Render

1. Ve a **[https://render.com](https://render.com)**
2. Click en **"Get Started for Free"**
3. Regístrate con tu cuenta de **GitHub** (recomendado)
4. Confirma tu email

### Paso 2: Crear Web Service

1. En el Dashboard de Render, click en **"New +"**
2. Selecciona **"Web Service"**
3. Click en **"Build and deploy from a Git repository"** → **"Next"**

### Paso 3: Conectar Repositorio

1. Si es tu primera vez, autoriza a Render para acceder a GitHub
2. Busca y selecciona el repositorio: **`InteligenciaCorreagro/cipa`**
3. Click en **"Connect"**

### Paso 4: Configurar el Servicio

Llena los campos con estos valores:

| Campo | Valor |
|-------|-------|
| **Name** | `cipa` (o el nombre que prefieras) |
| **Region** | `Oregon (US West)` (o el más cercano a ti) |
| **Branch** | `claude/deploy-railway-intranet-setup-011CUzK7LHYPqoX7JVpmDm4y` |
| **Root Directory** | (dejar vacío) |
| **Environment** | `Docker` |
| **Instance Type** | `Free` |

### Paso 5: Configurar Variables de Entorno

**Scroll down** hasta la sección **"Environment Variables"** y agrega estas variables:

#### Variables Obligatorias:

```bash
# 1. JWT Secret Key (generar primero)
JWT_SECRET_KEY = <GENERAR_VALOR_ALEATORIO>

# 2. Configuración de Subpath
BASE_PATH = /intranet/cipa
VITE_BASE_PATH = /intranet/cipa

# 3. Puerto (Render usa 10000)
PORT = 10000

# 4. Modo Producción
DEBUG = False
LOG_LEVEL = INFO
```

#### 🔐 Cómo generar JWT_SECRET_KEY:

**Opción A: En tu terminal local**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Opción B: Usar Render** (más fácil)
- En el campo `JWT_SECRET_KEY`, click en **"Generate"**
- Render creará un valor aleatorio seguro automáticamente

### Paso 6: Agregar Disco Persistente (Importante)

⚠️ **Para que la base de datos SQLite persista entre deployments:**

1. Scroll down hasta **"Persistent Disks"**
2. Click en **"Add Disk"**
3. Configurar:
   - **Name:** `cipa-data`
   - **Mount Path:** `/app/backend/data`
   - **Size:** `1 GB` (gratis)
4. Click **"Add"**

### Paso 7: Crear Servicio

1. Click en **"Create Web Service"** al final de la página
2. Render comenzará a construir tu aplicación automáticamente

⏳ **El primer build tomará ~8-12 minutos**. Verás:
- ✅ Clonando repositorio
- ✅ Building frontend (React + Vite)
- ✅ Building backend (Python + Flask)
- ✅ Creando imagen Docker
- ✅ Deployando...

### Paso 8: Verificar Deployment

Una vez completado el build (verás "Live" en verde):

1. Copia la URL de tu servicio: `https://cipa-XXXX.onrender.com`
2. Prueba el health check:
   ```
   https://cipa-XXXX.onrender.com/intranet/cipa/api/health
   ```
3. Deberías ver:
   ```json
   {
     "status": "healthy",
     "timestamp": "2025-11-10T...",
     "version": "1.0.1",
     "base_path": "/intranet/cipa"
   }
   ```

✅ **¡Tu aplicación está en vivo!**

---

## 🌐 Configuración de GoDaddy

Ahora que tu aplicación está en Render, necesitas configurar tu dominio `correagro.com`.

### ⚠️ IMPORTANTE: Limitaciones de GoDaddy

**GoDaddy NO soporta subpaths** (`/intranet/cipa`) de forma nativa. Tienes 3 opciones:

---

### **OPCIÓN 1: Usar Subdominio** ⭐ **RECOMENDADO**

**En lugar de:** `correagro.com/intranet/cipa`
**Usar:** `intranet.correagro.com` o `cipa.correagro.com`

#### Ventajas:
- ✅ Configuración súper simple (5 minutos)
- ✅ No requiere servicios adicionales
- ✅ Mejor performance
- ✅ Más profesional

#### Pasos en GoDaddy:

1. **Inicia sesión en GoDaddy** → Ve a **"My Products"**
2. **Encuentra** `correagro.com` → Click en **"DNS"**
3. **Agregar registro CNAME:**
   - Click en **"Add"** o **"Add Record"**
   - **Type:** `CNAME`
   - **Name:** `intranet` (o `cipa`)
   - **Value:** `cipa-XXXX.onrender.com.` (⚠️ **con el punto al final**)
   - **TTL:** `1 Hour`
4. **Guardar** → Esperar 5-15 minutos para propagación DNS

5. **En Render Dashboard:**
   - Ve a tu servicio → **Settings** → **Custom Domains**
   - Click en **"Add Custom Domain"**
   - Ingresar: `intranet.correagro.com`
   - Render verificará automáticamente el DNS
   - HTTPS se configurará automáticamente (gratis)

6. **Actualizar variables de entorno en Render:**
   ```bash
   BASE_PATH = /
   VITE_BASE_PATH = /
   ```

7. **Redeployar:** Settings → **"Manual Deploy"** → **"Deploy latest commit"**

✅ **Listo! Accede en:** `https://intranet.correagro.com`

---

### **OPCIÓN 2: Forwarding (Redirección Simple)**

Si **DEBES** mantener la ruta visible como `correagro.com/intranet/cipa`:

⚠️ **Limitación:** La URL cambiará en el navegador a tu URL de Render.

#### Pasos:

1. **GoDaddy** → Dominios → `correagro.com` → **"Forwarding"**
2. Click en **"Add Forwarding"**
3. Configurar:
   - **Forward from:** `http://correagro.com/intranet/cipa`
   - **Forward to:** `https://cipa-XXXX.onrender.com/intranet/cipa`
   - **Forward type:** `301 (Permanent Redirect)`
   - **Settings:** Forward only
4. Guardar

⚠️ Cuando alguien acceda a `correagro.com/intranet/cipa`, será redirigido y verá la URL de Render en el navegador.

---

### **OPCIÓN 3: Cloudflare Workers** (Subpath Transparente)

Para mantener `correagro.com/intranet/cipa` sin que cambie la URL:

Esta opción requiere **Cloudflare** (gratuito) como proxy reverso.

#### Pasos:

1. **Crear cuenta en Cloudflare** → [https://cloudflare.com](https://cloudflare.com)
2. **Add a Site** → Ingresar `correagro.com`
3. **Seleccionar plan Free** → Click **"Continue"**
4. Cloudflare te mostrará los **nameservers**
5. **Cambiar nameservers en GoDaddy:**
   - GoDaddy → Dominios → `correagro.com` → **"Manage DNS"**
   - En "Nameservers" → Click **"Change"**
   - Seleccionar **"Custom"**
   - Ingresar los nameservers de Cloudflare (ejemplo: `bob.ns.cloudflare.com`)
   - Guardar y esperar 24h para propagación

6. **Crear Cloudflare Worker:**
   - Cloudflare Dashboard → **Workers & Pages** → **"Create Application"**
   - **"Create Worker"** → Nombre: `cipa-proxy`
   - **"Deploy"** → Luego **"Edit Code"**

7. **Pegar este código:**

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)

  // Si la ruta comienza con /intranet/cipa
  if (url.pathname.startsWith('/intranet/cipa')) {
    // Proxy a Render
    const renderUrl = 'https://cipa-XXXX.onrender.com' + url.pathname + url.search

    // Crear nueva request
    const modifiedRequest = new Request(renderUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: 'follow'
    })

    // Fetch desde Render
    const response = await fetch(modifiedRequest)

    // Retornar respuesta
    return response
  }

  // Para otras rutas, continuar normal
  return fetch(request)
}
```

⚠️ **Reemplazar:** `cipa-XXXX.onrender.com` con tu URL real de Render.

8. **Deploy el Worker** → **"Save and Deploy"**

9. **Configurar Route:**
   - Workers → Tu worker → **"Triggers"** → **"Add Route"**
   - **Route:** `correagro.com/intranet/cipa/*`
   - **Zone:** `correagro.com`
   - Guardar

✅ **Listo!** Ahora `https://correagro.com/intranet/cipa` funcionará sin cambiar la URL.

---

## 📚 Paso a Paso para GoDaddy - Capturas

### Configurar CNAME (Opción 1 - Subdominio):

```
1. GoDaddy.com → Login
2. "My Products" → Domains → correagro.com
3. Click en los 3 puntos "..." → "Manage DNS"
4. Scroll down → Sección "Records"
5. Click "Add" o "Add Record"
6. Llenar:
   - Type: CNAME
   - Name: intranet
   - Value: cipa-XXXX.onrender.com.
   - TTL: 1 Hour
7. Click "Save"
8. Esperar 5-15 minutos
```

---

## ✅ Verificación Final

### 1. Verificar Health Check

```bash
curl https://intranet.correagro.com/api/health

# O si usaste subpath:
curl https://correagro.com/intranet/cipa/api/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T...",
  "version": "1.0.1",
  "base_path": "/intranet/cipa"
}
```

### 2. Acceder a la Interfaz

- Abre tu navegador
- Ve a: `https://intranet.correagro.com` (o tu URL configurada)
- Deberías ver la página de login de CIPA

### 3. Crear Usuario Administrador

**Opción A: Desde Render Shell**

1. Render Dashboard → Tu servicio → **"Shell"** (tab superior)
2. Ejecutar:
   ```bash
   cd /app/backend
   python scripts/inicializar_auth.py
   ```

**Opción B: Manualmente**

Sigue las instrucciones en `backend/scripts/inicializar_auth.py`

---

## 🔧 Configuración Avanzada (Opcional)

### Auto-Deploy desde GitHub

✅ **Ya está configurado!** Cada vez que hagas `git push`, Render automáticamente:
1. Detecta el nuevo commit
2. Construye la nueva imagen Docker
3. Deploya la nueva versión
4. Mantiene zero-downtime

### Notificaciones de Deploy

1. Render Dashboard → Tu servicio → **Settings**
2. **"Deploy Notifications"**
3. Agregar Webhook de Slack/Discord (opcional)

### Ver Logs en Tiempo Real

1. Render Dashboard → Tu servicio → **"Logs"** (tab superior)
2. Verás todos los logs del servidor en tiempo real

### Configurar Alertas

1. Render Dashboard → Tu servicio → **Settings** → **"Health Check Path"**
2. Ya configurado: `/intranet/cipa/api/health`
3. Render te notificará si la app cae

---

## 🐛 Solución de Problemas

### ❌ Build Failed: "Error during build"

**Causa:** Dependencias faltantes o error en Dockerfile

**Solución:**
1. Render Dashboard → **Logs** → Revisar error específico
2. Verificar que todas las dependencias estén en `requirements.txt`
3. Asegurarse de que el Dockerfile sea correcto

### ❌ "Service Unavailable" o "502 Bad Gateway"

**Causa:** La aplicación no está respondiendo en el puerto correcto

**Solución:**
1. Verificar que `PORT=10000` esté configurado en Environment Variables
2. Verificar logs: ¿La app inició correctamente?
3. Verificar health check path

### ❌ "Token inválido" en Frontend

**Causa:** JWT_SECRET_KEY no configurado o cambió

**Solución:**
1. Verificar que `JWT_SECRET_KEY` esté en Environment Variables
2. Si lo cambiaste, todos los usuarios deben volver a loguearse
3. Limpiar localStorage: F12 → Application → Local Storage → Clear

### ❌ Base de datos se resetea en cada deploy

**Causa:** No configuraste Persistent Disk

**Solución:**
1. Render Dashboard → Tu servicio → **Settings**
2. Scroll down → **"Disks"** → **"Add Disk"**
3. Mount path: `/app/backend/data`
4. Size: 1 GB
5. Redeploy

### ❌ DNS no resuelve (Opción 1 - Subdominio)

**Causa:** Propagación DNS toma tiempo

**Solución:**
1. Esperar 15-30 minutos
2. Verificar con: `nslookup intranet.correagro.com`
3. Verificar que agregaste el punto final: `cipa-XXXX.onrender.com.`

### ❌ Render dice "Deploy took too long"

**Causa:** El build es muy lento (red, dependencias)

**Solución:**
1. Esto es normal en el primer deploy
2. Esperar hasta 15 minutos
3. Si falla, Render reintentará automáticamente

---

## 📊 Monitoreo y Métricas

### En Render Dashboard puedes ver:

- **Metrics:** CPU, memoria, ancho de banda
- **Logs:** En tiempo real
- **Deploy History:** Todos los deploys anteriores
- **Health Checks:** Uptime y disponibilidad

### Límites del Plan Free:

- ✅ 750 horas/mes (suficiente para 24/7)
- ✅ 512 MB RAM
- ✅ 1 GB disco persistente
- ✅ HTTPS ilimitado
- ⚠️ Sleep después de 15 min de inactividad (primer request demora ~30s)

**Para evitar el sleep:**
- Configura un ping cada 10 min desde un servicio externo (UptimeRobot, etc.)
- O actualiza a plan Starter ($7/mes) para no-sleep

---

## 🔐 Seguridad en Producción

### ✅ Ya Implementado:

- JWT con Access + Refresh tokens
- Password hashing con bcrypt
- Rate limiting en login
- HTTPS automático por Render
- CORS configurado
- Usuario no-root en Docker
- Health checks

### 🔒 Recomendaciones Adicionales:

1. **Rotar JWT_SECRET_KEY cada 3-6 meses**
2. **Hacer backups regulares de la BD:**
   - Render Shell → `cp /app/backend/data/notas_credito.db /tmp/backup.db`
   - Download del backup
3. **Monitorear logs regularmente** para detectar accesos sospechosos
4. **Configurar 2FA** para tu cuenta de Render
5. **No compartir credenciales** de admin

---

## 🎉 ¡Felicitaciones!

Tu aplicación CIPA está ahora en producción en Render, completamente **GRATIS** y con:

- ✅ HTTPS automático
- ✅ Auto-deploy desde GitHub
- ✅ Base de datos persistente
- ✅ Health checks automáticos
- ✅ Logs en tiempo real
- ✅ Dominio personalizado

---

## 📞 Soporte

Si tienes problemas:

1. Revisa la sección de [Solución de Problemas](#solución-de-problemas)
2. Consulta logs en Render Dashboard
3. Revisa [Documentación de Render](https://render.com/docs)
4. Contacta a soporte de Render (muy responsivos)

---

**¡Disfruta de CIPA en producción! 🚀**
