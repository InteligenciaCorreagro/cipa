# ⚡ Railway Deployment - Guía Rápida

## 🚀 Deployment en 5 Minutos

### 1️⃣ Crear Proyecto en Railway

```bash
1. Ir a https://railway.app
2. Click en "New Project"
3. Seleccionar "Deploy from GitHub repo"
4. Elegir: InteligenciaCorreagro/cipa
5. Rama: claude/deploy-railway-intranet-setup-011CUzK7LHYPqoX7JVpmDm4y
```

### 2️⃣ Configurar Variables de Entorno

En Railway Dashboard > Variables, agregar:

```bash
# GENERAR CON: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=<TU_CLAVE_SECRETA_AQUI>

# Configuración de subpath
BASE_PATH=/intranet/cipa
VITE_BASE_PATH=/intranet/cipa

# Producción
DEBUG=False
LOG_LEVEL=INFO
```

### 3️⃣ Esperar el Build

⏳ El build tarda ~5-10 minutos. Railway hará:
- ✅ Build del frontend (React + Vite)
- ✅ Instalación de dependencias Python
- ✅ Creación de imagen Docker

### 4️⃣ Obtener URL Pública

```bash
1. Railway Dashboard > Settings > Networking
2. Click en "Generate Domain"
3. Copiar URL: https://tu-proyecto.up.railway.app
```

### 5️⃣ Verificar Deployment

```bash
# Health check
curl https://tu-proyecto.up.railway.app/intranet/cipa/api/health

# Debería retornar:
{
  "status": "healthy",
  "base_path": "/intranet/cipa"
}
```

---

## 🌐 Configuración de GoDaddy

### Opción A: Usar Subdominio (Más Simple) ⭐ Recomendado

**En lugar de:** `correagro.com/intranet/cipa`
**Usar:** `intranet.correagro.com` o `cipa.correagro.com`

**Configuración en GoDaddy:**

```bash
1. GoDaddy > Dominios > correagro.com > DNS Management
2. Agregar registro CNAME:
   - Type: CNAME
   - Name: intranet
   - Value: tu-proyecto.up.railway.app.
   - TTL: 1 Hour
3. Guardar

4. Actualizar variables en Railway:
   BASE_PATH=/
   VITE_BASE_PATH=/

5. Redeploy el proyecto
```

**✅ Listo!** Accede en: `https://intranet.correagro.com`

---

### Opción B: Usar Subpath con Cloudflare

Si **DEBES** usar `correagro.com/intranet/cipa`:

```bash
1. Crear cuenta en Cloudflare (gratis)
2. Agregar dominio correagro.com
3. Cambiar nameservers en GoDaddy a los de Cloudflare
4. En Cloudflare: Workers > Create Worker
5. Usar el código del archivo DEPLOYMENT.md (sección Cloudflare Worker)
6. Configurar route: correagro.com/intranet/cipa/*
```

⚠️ **Nota:** GoDaddy NO soporta subpaths nativamente. Cloudflare es necesario.

---

## 🔐 Crear Usuario Administrador

Después del deployment, crear usuario admin:

**Opción 1: Desde Railway Dashboard**

```bash
1. Railway Dashboard > Deployments > Shell
2. Ejecutar:
   cd /app/backend
   python scripts/inicializar_auth.py
```

**Opción 2: API (si ya tienes un usuario)**

```bash
# Login y crear nuevo usuario via API
curl -X POST https://tu-url/intranet/cipa/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password"}'
```

---

## 📊 Plan Gratuito de Railway

- ✅ **500 horas/mes** de ejecución (suficiente para producción)
- ✅ **512 MB RAM**
- ✅ **1 GB Storage**
- ✅ **HTTPS automático**
- ✅ **Deploy desde GitHub**

**Uso estimado para CIPA:**
- ~300-400 horas/mes (tráfico moderado)
- ~200 MB RAM
- ~50 MB Storage (base de datos SQLite)

---

## 🐛 Troubleshooting Rápido

### ❌ "Application failed to respond"
```bash
✅ Verificar variable PORT en Railway
✅ Revisar logs: Railway Dashboard > Logs
```

### ❌ "Token inválido"
```bash
✅ Configurar JWT_SECRET_KEY
✅ Limpiar localStorage del navegador (F12 > Application > Clear)
```

### ❌ "Cannot GET /intranet/cipa"
```bash
✅ Verificar BASE_PATH=/intranet/cipa
✅ Verificar VITE_BASE_PATH=/intranet/cipa
✅ Redeploy el proyecto
```

---

## 📚 Documentación Completa

Para más detalles, ver: **[DEPLOYMENT.md](./DEPLOYMENT.md)**

---

## 🎉 ¡Listo para Producción!

Tu aplicación CIPA está optimizada y lista para usar en Railway con:

- 🔐 Seguridad JWT + bcrypt
- 🚀 Performance optimizada (build minificado)
- 📊 Monitoring con health checks
- 🔄 Auto-deploy desde GitHub
- 💰 100% GRATIS en Railway

**¡Disfruta! 🚀**
