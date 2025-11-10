# 🚀 Guía de Deployment - CIPA en Render.com

Esta guía te llevará paso a paso para desplegar la aplicación CIPA en Render.com de forma **100% GRATUITA** (sin tarjeta de crédito) y configurarla para que funcione en el subpath `correagro.com/intranet/cipa` o subdominio.

---

## 📋 Tabla de Contenidos

1. [¿Por qué Render?](#por-qué-render)
2. [Deployment Paso a Paso](#deployment-paso-a-paso)
3. [Configuración de Dominio](#configuración-de-dominio)
4. [Verificación](#verificación)
5. [Medidas de Seguridad](#medidas-de-seguridad)
6. [Solución de Problemas](#solución-de-problemas)

---

## ✨ ¿Por qué Render?

- ✅ **100% gratis** sin tarjeta de crédito
- ✅ **750 horas/mes** de ejecución gratis
- ✅ **HTTPS automático** y renovación
- ✅ **Deploy desde GitHub** automático
- ✅ **Dockerfile support** nativo
- ✅ **Disco persistente** para SQLite (1GB gratis)
- ✅ **Mejor que Railway** para cuentas gratuitas

---

## 🚂 Deployment Paso a Paso

### Paso 1: Crear Cuenta en Render

1. Ve a [https://render.com](https://render.com)
2. Click en **"Get Started for Free"**
3. Regístrate con tu cuenta de **GitHub** (recomendado)
4. Confirma tu email
5. **¡No se requiere tarjeta de crédito!** ✅

---

### Paso 2: Crear Web Service

1. En tu Render Dashboard, click en **"New +"** (esquina superior derecha)
2. Selecciona **"Web Service"**
3. Click en **"Build and deploy from a Git repository"**
4. Click **"Next"**

---

### Paso 3: Conectar Repositorio de GitHub

1. **Primera vez:** Render pedirá permiso para acceder a GitHub
   - Click **"Connect GitHub"**
   - Autoriza a Render

2. **Seleccionar repositorio:**
   - Busca: `InteligenciaCorreagro/cipa`
   - Click en **"Connect"** junto al repositorio

---

### Paso 4: Configurar el Servicio

Llena los siguientes campos:

| Campo | Valor | Descripción |
|-------|-------|-------------|
| **Name** | `cipa` | Nombre de tu servicio (aparecerá en la URL) |
| **Region** | `Oregon (US West)` | Región del servidor (elegir la más cercana) |
| **Branch** | `claude/deploy-railway-intranet-setup-011CUzK7LHYPqoX7JVpmDm4y` | Rama de deployment |
| **Root Directory** | *(vacío)* | Dejar en blanco |
| **Environment** | `Docker` | ✅ Render detectará el Dockerfile automáticamente |
| **Instance Type** | `Free` | Plan gratuito |

---

### Paso 5: Configurar Variables de Entorno

**MUY IMPORTANTE:** Scroll down hasta la sección **"Environment Variables"**.

Agrega las siguientes variables haciendo click en **"Add Environment Variable"**:

#### 🔐 Variables Obligatorias:

```bash
# 1. JWT Secret Key
Key: JWT_SECRET_KEY
Value: [Click en "Generate" para crear valor aleatorio]

# 2. Base Path (para subpath)
Key: BASE_PATH
Value: /intranet/cipa

# 3. Base Path Frontend
Key: VITE_BASE_PATH
Value: /intranet/cipa

# 4. Puerto
Key: PORT
Value: 10000

# 5. Debug Mode
Key: DEBUG
Value: False

# 6. Log Level
Key: LOG_LEVEL
Value: INFO
```

**💡 Tip:** Para `JWT_SECRET_KEY`, Render tiene un botón **"Generate"** que crea un valor aleatorio seguro automáticamente.

---

### Paso 6: Agregar Disco Persistente (¡IMPORTANTE!)

⚠️ **Sin este paso, tu base de datos se reseteará en cada deploy.**

1. Scroll down hasta **"Disks"** o **"Persistent Disks"**
2. Click en **"Add Disk"**
3. Configurar:
   - **Name:** `cipa-data`
   - **Mount Path:** `/app/backend/data`
   - **Size:** `1 GB` (gratis)
4. Click **"Add"**

---

### Paso 7: Crear el Servicio

1. Revisa toda la configuración
2. Click en **"Create Web Service"** al final de la página
3. Render comenzará el build automáticamente

⏳ **Tiempo estimado del primer build:** 8-12 minutos

Verás el progreso en tiempo real:
- ✅ Clonando repositorio...
- ✅ Building frontend (React + Vite)...
- ✅ Installing Python dependencies...
- ✅ Building Docker image...
- ✅ Deploying...
- ✅ **Live** ✅

---

### Paso 8: Obtener URL del Servicio

Una vez que el status sea **"Live"** (en verde):

1. Tu URL será algo como: `https://cipa-XXXX.onrender.com`
2. Copia esta URL (la necesitarás para configurar el dominio)

---

## 🌐 Configuración de Dominio

Tienes **3 opciones** para configurar tu dominio `correagro.com`:

---

### **OPCIÓN 1: Subdominio** ⭐ **RECOMENDADO**

**Resultado final:** `https://intranet.correagro.com`

**Ventajas:**
- ✅ Configuración MUY simple (5 minutos)
- ✅ No requiere servicios adicionales
- ✅ Mejor performance
- ✅ Más profesional

#### Pasos en GoDaddy:

1. **Inicia sesión en GoDaddy**
   - Ve a [https://godaddy.com](https://godaddy.com)
   - Login → **"My Products"**

2. **Administrar DNS del dominio**
   - Encuentra `correagro.com`
   - Click en **"DNS"** o en los 3 puntos **"..."** → **"Manage DNS"**

3. **Agregar registro CNAME**
   - Scroll down a la sección **"Records"**
   - Click en **"Add"** o **"Add Record"**

   Configurar:
   ```
   Type: CNAME
   Name: intranet
   Value: cipa-XXXX.onrender.com.
   TTL: 1 Hour
   ```

   ⚠️ **IMPORTANTE:** El punto al final de `.onrender.com.` es obligatorio

4. **Guardar** → Click **"Save"**

5. **Esperar propagación DNS:** 5-30 minutos

#### Pasos en Render:

1. **Ve a tu servicio en Render Dashboard**
2. Click en **"Settings"** (tab superior)
3. Scroll down a **"Custom Domains"**
4. Click **"Add Custom Domain"**
5. Ingresar: `intranet.correagro.com`
6. Click **"Save"**
7. Render verificará automáticamente el DNS
8. **HTTPS se configurará automáticamente** (gratis con Let's Encrypt)

#### Actualizar Variables de Entorno:

Ya que ahora usas el dominio raíz (no subpath):

1. **Settings** → **Environment**
2. Editar estas variables:
   ```bash
   BASE_PATH = /
   VITE_BASE_PATH = /
   ```
3. Click **"Save Changes"**

#### Redeploy:

1. **Settings** → Scroll down
2. Click en **"Manual Deploy"** → **"Deploy latest commit"**
3. Esperar ~5 minutos

✅ **¡Listo!** Accede en: `https://intranet.correagro.com`

---

### **OPCIÓN 2: Subpath con Cloudflare Workers**

**Resultado final:** `https://correagro.com/intranet/cipa`

⚠️ **GoDaddy NO soporta subpaths directamente.** Necesitas Cloudflare (gratis) como proxy.

Ver guía completa en **[RENDER_DEPLOY.md](./RENDER_DEPLOY.md)** - Sección "OPCIÓN 3: Cloudflare Workers"

**Resumen:**
1. Crear cuenta en Cloudflare (gratis)
2. Agregar dominio `correagro.com` a Cloudflare
3. Cambiar nameservers en GoDaddy a los de Cloudflare
4. Crear Worker con código de proxy reverso
5. Configurar route: `correagro.com/intranet/cipa/*`

---

### **OPCIÓN 3: Forwarding Simple (No Recomendado)**

Si solo necesitas una redirección simple (la URL cambiará en el navegador):

**En GoDaddy:**
1. Dominios → `correagro.com` → **"Forwarding"**
2. **"Add Forwarding"**
3. Forward from: `http://correagro.com/intranet/cipa`
4. Forward to: `https://cipa-XXXX.onrender.com/intranet/cipa`
5. Type: 301 (Permanent)

⚠️ **Limitación:** Los usuarios verán la URL de Render en el navegador.

---

## ✅ Verificación del Deployment

### 1. Health Check

Abre tu navegador o usa `curl`:

```bash
# Con subdominio:
curl https://intranet.correagro.com/api/health

# Con subpath:
curl https://correagro.com/intranet/cipa/api/health

# Respuesta esperada:
{
  "status": "healthy",
  "timestamp": "2025-11-10T...",
  "version": "1.0.1",
  "base_path": "/intranet/cipa"
}
```

### 2. Acceder a la Interfaz

- Abre tu navegador
- Ve a tu URL configurada
- Deberías ver la **página de login de CIPA**

### 3. Crear Usuario Administrador

Necesitas crear al menos un usuario para poder acceder.

**Desde Render Shell:**

1. Render Dashboard → Tu servicio
2. Click en **"Shell"** (tab superior derecha)
3. Espera a que cargue la terminal
4. Ejecutar:
   ```bash
   cd /app/backend
   python scripts/inicializar_auth.py
   ```
5. Seguir las instrucciones en pantalla

**Alternativa - Desde tu computadora local:**

```bash
# Si tienes acceso al repositorio
cd backend
python scripts/inicializar_auth.py
```

---

## 🔐 Medidas de Seguridad Implementadas

### ✅ Autenticación y Autorización
- **JWT (JSON Web Tokens)** con Access + Refresh tokens
- **Expiración de tokens:** Access (1 hora), Refresh (30 días)
- **Password hashing** con bcrypt (12 rounds)
- **Rate limiting** en login (5 intentos/minuto)
- **Bloqueo automático** tras intentos fallidos

### ✅ Seguridad de Red
- **CORS** configurado
- **HTTPS automático** en Render (Let's Encrypt)
- **Proxy headers** validados

### ✅ Seguridad de Datos
- **Base de datos SQLite** con permisos restrictivos
- **Logs de auditoría** de accesos
- **Sesiones revocables**
- **Disco persistente** protegido

### ✅ Buenas Prácticas
- **Usuario no-root** en Docker
- **Variables de entorno** para secretos
- **Health checks** automáticos
- **Dependencias actualizadas**

### 🔒 Recomendaciones Adicionales

1. **Rotar JWT_SECRET_KEY regularmente**
   - Cada 3-6 meses
   - Cuando sospechas de compromiso

2. **Backup de base de datos**
   ```bash
   # Desde Render Shell:
   cp /app/backend/data/notas_credito.db /tmp/backup-$(date +%Y%m%d).db
   ```

3. **Monitorear logs**
   - Render Dashboard → **Logs** (tab)
   - Revisar semanalmente

4. **Configurar alertas**
   - Render Dashboard → Settings → **Notifications**
   - Agregar email o webhook

5. **Evitar sleep (opcional)**
   - Configurar ping cada 10 min
   - Usar [UptimeRobot](https://uptimerobot.com) (gratis)
   - O actualizar a plan Starter ($7/mes) para instancia always-on

---

## 🐛 Solución de Problemas

### ❌ Build Failed

**Síntomas:** El deploy falla con errores durante el build.

**Solución:**
1. Ver logs: Dashboard → **Logs**
2. Identificar el error específico
3. Errores comunes:
   - Dependencia faltante → Agregar a `requirements.txt`
   - Error de sintaxis → Revisar código
   - Timeout → Es normal en primer deploy, reintenta

---

### ❌ Application Unavailable / 502 Bad Gateway

**Síntomas:** La app no responde o muestra error 502.

**Causas posibles:**
1. Puerto incorrecto
2. App no inició correctamente
3. Health check fallando

**Solución:**
1. Verificar `PORT=10000` en Environment Variables
2. Ver logs: ¿La app inició?
3. Probar health check manualmente
4. Verificar que Dockerfile está correcto

---

### ❌ "Token inválido" en el Frontend

**Síntomas:** No puedes hacer login o te desloguea constantemente.

**Causas:**
- `JWT_SECRET_KEY` no configurado
- `JWT_SECRET_KEY` cambió después del login

**Solución:**
1. Verificar que `JWT_SECRET_KEY` existe en Environment Variables
2. Si lo cambiaste, todos deben volver a loguearse
3. Limpiar localStorage del navegador:
   - F12 → Application → Local Storage → Clear All

---

### ❌ Base de Datos se Resetea en Cada Deploy

**Síntomas:** Pierdes todos los datos después de un deploy.

**Causa:** No configuraste el Persistent Disk.

**Solución:**
1. Settings → Disks → **Add Disk**
2. Mount path: `/app/backend/data`
3. Size: 1 GB
4. **Redeploy**

---

### ❌ DNS No Resuelve (Subdominio)

**Síntomas:** `intranet.correagro.com` no carga.

**Causas:**
- Propagación DNS toma tiempo
- CNAME mal configurado

**Solución:**
1. Esperar 15-30 minutos (puede tomar hasta 24h)
2. Verificar DNS:
   ```bash
   nslookup intranet.correagro.com
   ```
3. Verificar que agregaste el punto final: `cipa-XXXX.onrender.com.`
4. En GoDaddy, asegurarse que el registro esté **activo** (no pausado)

---

### ❌ Render: "Deploy Took Too Long"

**Síntomas:** El build se cancela por timeout.

**Causa:** Build muy lento (red, muchas dependencias).

**Solución:**
1. **Normal en primer deploy** - Render cachea después
2. Esperar hasta 15 minutos
3. Si falla, Render reintentará automáticamente
4. Deployments subsecuentes serán más rápidos (~3-5 min)

---

### ❌ Sleep Mode - Primera Petición Lenta

**Síntomas:** La app tarda 30-60s en responder después de inactividad.

**Causa:** Plan Free de Render duerme la app tras 15 min de inactividad.

**Soluciones:**

**Opción A: Configurar Ping (Gratis)**
1. Crear cuenta en [UptimeRobot](https://uptimerobot.com)
2. Agregar monitor:
   - Type: HTTP(s)
   - URL: `https://intranet.correagro.com/api/health`
   - Interval: 10 minutos
3. La app nunca dormirá

**Opción B: Upgrade a Starter Plan**
- $7/mes
- Instancia always-on (no sleep)
- 512 MB RAM garantizados

---

## 📊 Monitoreo en Render

### Dashboard de Render

En tu servicio, tienes acceso a:

**Metrics (Métricas):**
- CPU usage
- Memory usage
- Request count
- Response time
- Bandwidth

**Logs:**
- En tiempo real
- Filtros por severity
- Descarga de logs

**Deploy History:**
- Todos los deploys anteriores
- Rollback con 1 click

**Events:**
- Historial de eventos del servicio
- Errors, warnings, info

---

## 📚 Recursos Adicionales

- [Documentación de Render](https://render.com/docs)
- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de Vite](https://vitejs.dev)
- [Documentación de GoDaddy DNS](https://www.godaddy.com/help/manage-dns-680)

---

## 🎉 ¡Listo para Producción!

Si seguiste todos los pasos, tu aplicación CIPA está ahora funcionando en:

**URL de Render (directa):** `https://cipa-XXXX.onrender.com/intranet/cipa`

**URL personalizada (recomendada):** `https://intranet.correagro.com`

### Próximos Pasos

1. ✅ Crear usuarios adicionales (si es necesario)
2. ✅ Importar datos históricos de notas de crédito
3. ✅ Configurar backups automáticos
4. ✅ Configurar ping para evitar sleep (UptimeRobot)
5. ✅ Monitorear logs regularmente

---

## 🆘 ¿Necesitas Más Ayuda?

Si tienes problemas:

1. ✅ Revisa la sección [Solución de Problemas](#solución-de-problemas)
2. ✅ Consulta los logs en Render Dashboard
3. ✅ Verifica el health check
4. ✅ Revisa **[RENDER_DEPLOY.md](./RENDER_DEPLOY.md)** para guía detallada
5. ✅ Contacta al soporte de Render (muy rápidos)

---

**¡Disfruta de CIPA en producción! 🚀**

**Desarrollado con ❤️ por Correagro**
