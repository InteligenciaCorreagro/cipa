# ⚡ CIPA - Deployment Rápido en Render

## 🚀 5 Minutos para Producción (¡GRATIS!)

### 1️⃣ Crear Servicio en Render

```
1. Ir a https://render.com → Registrarse con GitHub
2. Click "New +" → "Web Service"
3. Conectar repo: InteligenciaCorreagro/cipa
4. Configurar:
   - Name: cipa
   - Environment: Docker
   - Plan: Free
   - Branch: claude/deploy-railway-intranet-setup-011CUzK7LHYPqoX7JVpmDm4y
```

### 2️⃣ Variables de Entorno

Agregar en **Environment Variables**:

```bash
JWT_SECRET_KEY = [Click "Generate" para crear uno aleatorio]
BASE_PATH = /intranet/cipa
VITE_BASE_PATH = /intranet/cipa
PORT = 10000
DEBUG = False
LOG_LEVEL = INFO
```

### 3️⃣ Agregar Disco Persistente

En **Disks** → **Add Disk**:
```
Name: cipa-data
Mount Path: /app/backend/data
Size: 1 GB
```

### 4️⃣ Deploy

Click **"Create Web Service"** → Esperar 8-12 min

### 5️⃣ Verificar

```bash
# Tu URL será algo como:
https://cipa-XXXX.onrender.com/intranet/cipa/api/health

# Deberías ver:
{"status": "healthy", "base_path": "/intranet/cipa"}
```

---

## 🌐 Configurar Dominio (OPCIÓN 1 - RECOMENDADA)

### Usar Subdominio: `intranet.correagro.com`

**En GoDaddy:**

```
1. Dominios → correagro.com → DNS
2. Add Record:
   - Type: CNAME
   - Name: intranet
   - Value: cipa-XXXX.onrender.com.
   - TTL: 1 Hour
3. Guardar
```

**En Render:**

```
1. Settings → Custom Domains
2. Add: intranet.correagro.com
3. Esperar verificación DNS (5-15 min)
4. HTTPS automático ✅
```

**Actualizar variables:**

```bash
BASE_PATH = /
VITE_BASE_PATH = /
```

**Redeploy:** Settings → Manual Deploy

✅ **Acceso:** `https://intranet.correagro.com`

---

## 🌐 Configurar Dominio (OPCIÓN 2 - SUBPATH)

### Usar Subpath: `correagro.com/intranet/cipa`

⚠️ **Requiere Cloudflare** (GoDaddy no soporta subpaths)

Ver guía completa en **[RENDER_DEPLOY.md](./RENDER_DEPLOY.md)** (sección Cloudflare)

---

## 🔐 Crear Usuario Admin

**Desde Render Shell:**

```bash
1. Render Dashboard → Shell (tab superior)
2. Ejecutar:
   cd /app/backend
   python scripts/inicializar_auth.py
```

---

## 📊 Plan Gratuito de Render

- ✅ **750 horas/mes** (24/7 con ping externo)
- ✅ **512 MB RAM**
- ✅ **1 GB disco persistente** (gratis)
- ✅ **HTTPS automático**
- ✅ **Auto-deploy desde GitHub**
- ⚠️ **Sleep tras 15 min inactividad** (primer request ~30s)

**Solución para evitar sleep:**
- Configura ping cada 10 min con [UptimeRobot](https://uptimerobot.com) (gratis)

---

## 🐛 Problemas Comunes

### ❌ Build failed
→ Ver logs en Render Dashboard

### ❌ BD se resetea
→ Asegúrate de agregar Persistent Disk

### ❌ Token inválido
→ Verifica JWT_SECRET_KEY en variables

### ❌ DNS no resuelve
→ Espera 15-30 min, verifica punto final en CNAME

---

## 📚 Documentación Completa

- **[RENDER_DEPLOY.md](./RENDER_DEPLOY.md)** - Guía completa con capturas
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Guía general de deployment

---

## 🎉 ¡Listo!

Tu app CIPA está en producción con:

- 🔐 JWT + bcrypt
- 🚀 Auto-deploy
- 📊 Health checks
- 💾 BD persistente
- 🔒 HTTPS automático
- 💰 **100% GRATIS**

---

**¿Dudas?** Ver [RENDER_DEPLOY.md](./RENDER_DEPLOY.md) para troubleshooting completo.

**¡Disfruta! 🚀**
