# 🚀 Inicio Rápido - Deploy en Render

## ⚡ En 5 Pasos

### 1️⃣ Push a GitHub

```bash
git add .
git commit -m "🚀 Configuración para Render"
git push origin main
```

### 2️⃣ Crear Backend en Render

1. Ir a https://dashboard.render.com → **New +** → **Web Service**
2. Conectar repositorio `cipa`
3. Configurar:
   - **Name**: `cipa-backend`
   - **Root Directory**: `backend`
   - **Build Command**:
     ```
     pip install --upgrade pip && pip install -r requirements.txt && python scripts/inicializar_auth.py || echo "Auth ya inicializado"
     ```
   - **Start Command**:
     ```
     gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 api.app:app
     ```
4. **Environment Variables**:
   ```
   JWT_SECRET_KEY = [generar con: python3 -c "import secrets; print(secrets.token_urlsafe(64))"]
   API_PORT = 5000
   DEBUG = False
   FLASK_ENV = production
   PYTHON_VERSION = 3.11.0
   ```
5. **Add Disk**:
   - Name: `cipa-database`
   - Mount: `/opt/render/project/src/backend/data`
   - Size: `1 GB`
6. **Create Web Service**

### 3️⃣ Crear Frontend en Render

1. **New +** → **Static Site**
2. Conectar mismo repositorio
3. Configurar:
   - **Name**: `cipa-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**:
     ```
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`
4. **Environment Variables**:
   ```
   VITE_API_URL = https://cipa-backend.onrender.com
   VITE_USE_SUBPATH = false
   NODE_VERSION = 18.17.0
   ```
5. **Create Static Site**

### 4️⃣ Configurar Dominio en GoDaddy (Opcional)

#### Opción A: Subdominio (Recomendada)

En GoDaddy → DNS → Add Records:

```
Type: CNAME
Name: cipa
Value: cipa-frontend.onrender.com
TTL: 1 Hour
```

```
Type: CNAME
Name: cipa-api
Value: cipa-backend.onrender.com
TTL: 1 Hour
```

Luego en Render:
- **cipa-frontend** → Settings → Custom Domain → Add `cipa.correagro.com`
- **cipa-backend** → Settings → Custom Domain → Add `cipa-api.correagro.com`

Actualizar variables:
```env
# Frontend
VITE_API_URL=https://cipa-api.correagro.com

# Backend
CORS_ORIGINS=https://cipa.correagro.com,https://correagro.com
```

#### Opción B: Subpath (Compleja)

Ver: [GODADDY_CONFIGURATION.md](./GODADDY_CONFIGURATION.md)

### 5️⃣ Probar

Abrir en navegador:

```
https://cipa-frontend.onrender.com
# o
https://cipa.correagro.com
```

**Login**:
- Username: `admin`
- Password: `admin123`

⚠️ **Cambiar contraseña inmediatamente**

---

## 🛠️ Comandos Útiles

### Generar JWT Secret

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Verificar DNS

```bash
nslookup cipa.correagro.com
```

### Test API

```bash
curl https://cipa-backend.onrender.com/api/health
```

---

## 📚 Documentación Completa

- [Guía Completa de Render](./DEPLOYMENT_RENDER.md)
- [Configuración de GoDaddy](./GODADDY_CONFIGURATION.md)

---

## 🆘 Problemas Comunes

### Backend no inicia

```bash
# Verificar requirements.txt está completo
cat backend/requirements.txt
```

### Frontend no conecta

Verificar en Render → cipa-frontend → Environment:
```
VITE_API_URL=https://cipa-backend.onrender.com
```

### CORS Error

En Render → cipa-backend → Environment:
```
CORS_ORIGINS=https://cipa-frontend.onrender.com,https://cipa.correagro.com
```

Redeploy después de cambiar variables.

---

## ✅ Checklist

- [ ] Push a GitHub
- [ ] Backend creado en Render
- [ ] Variables de entorno del backend configuradas
- [ ] Disco persistente agregado
- [ ] Frontend creado en Render
- [ ] Variables de entorno del frontend configuradas
- [ ] `/api/health` responde OK
- [ ] Login funciona
- [ ] Dominio configurado (opcional)

---

**¿Dudas?** → Ver [DEPLOYMENT_RENDER.md](./DEPLOYMENT_RENDER.md)
