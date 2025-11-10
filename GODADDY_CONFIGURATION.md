# 🌐 Configuración de GoDaddy para Sistema CIPA

## 📋 Contenido

1. [Opción 1: Subdominio (Recomendada)](#opción-1-subdominio-recomendada)
2. [Opción 2: Subpath con Reverse Proxy](#opción-2-subpath-con-reverse-proxy)
3. [Configuración de SSL/HTTPS](#configuración-de-sslhttps)
4. [Verificación y Pruebas](#verificación-y-pruebas)
5. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Contexto

Tienes el dominio `correagro.com` que ya está en uso para tu página web principal. Quieres agregar el Sistema CIPA accesible desde:

```
https://correagro.com/intranet/cipa
```

Hay **dos formas** de lograr esto:

| Opción | URL Final | Dificultad | Ventajas | Desventajas |
|--------|-----------|------------|----------|-------------|
| **Subdominio** | `cipa.correagro.com` | ⭐ Fácil | Simple, no requiere servidor propio | URL diferente |
| **Subpath** | `correagro.com/intranet/cipa` | ⭐⭐⭐ Compleja | URL exacta solicitada | Requiere reverse proxy |

---

## ✅ Opción 1: Subdominio (Recomendada)

Esta es la opción **más simple y recomendada**. El sistema estará disponible en:

```
https://cipa.correagro.com
```

### Paso 1: Crear Subdominio en GoDaddy

1. **Accede a GoDaddy**: https://account.godaddy.com

2. **Ir a DNS Management**:
   - Clic en "My Products"
   - Encuentra tu dominio `correagro.com`
   - Clic en el botón "DNS" o "Manage DNS"

3. **Agregar Registro CNAME**:
   - Scroll down hasta "Records"
   - Clic en "Add"
   - Selecciona tipo: **CNAME**
   - Configurar:
     ```
     Type: CNAME
     Name: cipa
     Value: cipa-frontend.onrender.com
     TTL: 1 Hour (o 3600 seconds)
     ```
   - Clic en "Save"

4. **Agregar Registro CNAME para API**:
   - Agregar otro registro CNAME:
     ```
     Type: CNAME
     Name: cipa-api
     Value: cipa-backend.onrender.com
     TTL: 1 Hour
     ```
   - Clic en "Save"

### Paso 2: Configurar Custom Domain en Render

#### A. Frontend

1. Ir a **Render Dashboard** → **cipa-frontend**
2. Clic en **"Settings"** → **"Custom Domain"**
3. Clic en **"+ Add Custom Domain"**
4. Ingresar: `cipa.correagro.com`
5. Clic en **"Save"**

Render te mostrará instrucciones de verificación:
- Si configuraste el CNAME correctamente, la verificación será automática en 5-10 minutos
- Render proveerá SSL/HTTPS automático (Let's Encrypt)

#### B. Backend

1. Ir a **Render Dashboard** → **cipa-backend**
2. Clic en **"Settings"** → **"Custom Domain"**
3. Clic en **"+ Add Custom Domain"**
4. Ingresar: `cipa-api.correagro.com`
5. Clic en **"Save"**

### Paso 3: Actualizar Variables de Entorno

#### Frontend (cipa-frontend)

En Render → cipa-frontend → Environment:

```env
VITE_API_URL=https://cipa-api.correagro.com
VITE_USE_SUBPATH=false
```

#### Backend (cipa-backend)

En Render → cipa-backend → Environment:

```env
CORS_ORIGINS=https://cipa.correagro.com,https://correagro.com
```

### Paso 4: Redeploy

Después de cambiar las variables, haz redeploy:

1. Render → cipa-frontend → **"Manual Deploy"** → **"Deploy latest commit"**
2. Render → cipa-backend → **"Manual Deploy"** → **"Deploy latest commit"**

### ✅ ¡Listo!

Espera 10-30 minutos para propagación de DNS. Luego accede a:

```
https://cipa.correagro.com
```

---

## 🔧 Opción 2: Subpath con Reverse Proxy

⚠️ **ADVERTENCIA**: Esta opción es **significativamente más compleja** y requiere:
- Servidor con acceso root/admin
- Conocimientos de Nginx/Apache
- Configuración de proxy reverso
- Gestión manual de SSL

### Arquitectura

```
Usuario
  ↓
https://correagro.com/intranet/cipa
  ↓
Servidor Web Principal (Nginx/Apache)
  ↓
Proxy Reverso
  ↓
https://cipa-frontend.onrender.com
```

### Requisitos

1. **Acceso al servidor** que aloja `correagro.com`
2. **Nginx o Apache** instalado y configurado
3. **Permisos root** para editar configuraciones

---

### Configuración con Nginx

Si tu servidor usa **Nginx**, sigue estos pasos:

#### Paso 1: Verificar Instalación de Nginx

SSH a tu servidor:

```bash
ssh usuario@correagro.com
nginx -v
```

#### Paso 2: Editar Configuración de Nginx

Localiza el archivo de configuración de `correagro.com`:

```bash
sudo nano /etc/nginx/sites-available/correagro.com
```

O en algunos servidores:

```bash
sudo nano /etc/nginx/conf.d/correagro.com.conf
```

#### Paso 3: Agregar Configuración de Proxy

Dentro del bloque `server {}`, agregar:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name correagro.com www.correagro.com;

    # Tu configuración existente para la página principal
    location / {
        # ... configuración existente ...
    }

    # ===== CONFIGURACIÓN PARA CIPA =====

    # Frontend (React)
    location /intranet/cipa {
        # Remover el prefijo antes de proxear
        rewrite ^/intranet/cipa/(.*)$ /$1 break;
        rewrite ^/intranet/cipa$ / break;

        # Proxy al frontend de Render
        proxy_pass https://cipa-frontend.onrender.com;

        # Headers necesarios
        proxy_set_header Host cipa-frontend.onrender.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Original-URI $request_uri;

        # WebSocket support (si lo necesitas)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Backend API
    location /intranet/cipa/api {
        # Remover el prefijo antes de proxear
        rewrite ^/intranet/cipa/api/(.*)$ /api/$1 break;

        # Proxy al backend de Render
        proxy_pass https://cipa-backend.onrender.com;

        # Headers necesarios
        proxy_set_header Host cipa-backend.onrender.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# HTTPS (si tienes SSL configurado)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name correagro.com www.correagro.com;

    # Certificados SSL (actualizar con tus paths)
    ssl_certificate /etc/letsencrypt/live/correagro.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/correagro.com/privkey.pem;

    # Incluir la misma configuración de proxy de arriba
    # ... (copiar bloques location)
}
```

#### Paso 4: Probar Configuración

```bash
sudo nginx -t
```

Si todo está OK:

```bash
sudo systemctl reload nginx
```

---

### Configuración con Apache

Si tu servidor usa **Apache**, sigue estos pasos:

#### Paso 1: Habilitar Módulos Necesarios

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2enmod rewrite
sudo systemctl restart apache2
```

#### Paso 2: Editar Configuración de Apache

```bash
sudo nano /etc/apache2/sites-available/correagro.com.conf
```

#### Paso 3: Agregar Configuración de Proxy

```apache
<VirtualHost *:80>
    ServerName correagro.com
    ServerAlias www.correagro.com

    # Tu configuración existente
    DocumentRoot /var/www/correagro.com

    # ... otras configuraciones ...

    # ===== CONFIGURACIÓN PARA CIPA =====

    # Frontend (React)
    <Location /intranet/cipa>
        ProxyPreserveHost Off
        ProxyPass https://cipa-frontend.onrender.com/
        ProxyPassReverse https://cipa-frontend.onrender.com/

        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Host "correagro.com"
    </Location>

    # Backend API
    <Location /intranet/cipa/api>
        ProxyPreserveHost Off
        ProxyPass https://cipa-backend.onrender.com/api
        ProxyPassReverse https://cipa-backend.onrender.com/api

        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Host "correagro.com"
    </Location>
</VirtualHost>

# HTTPS
<VirtualHost *:443>
    ServerName correagro.com
    ServerAlias www.correagro.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/correagro.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/correagro.com/privkey.pem

    # Incluir la misma configuración de proxy de arriba
    # ... (copiar bloques Location)
</VirtualHost>
```

#### Paso 4: Probar y Recargar

```bash
sudo apache2ctl configtest
sudo systemctl reload apache2
```

---

### Configuración del Frontend para Subpath

Si usas la **Opción 2 (Subpath)**, debes configurar el frontend para subpath:

#### En Render → cipa-frontend → Environment:

```env
VITE_API_URL=https://correagro.com/intranet/cipa/api
VITE_USE_SUBPATH=true
```

#### Redeploy del Frontend

Después de cambiar las variables:

```
Render → cipa-frontend → Manual Deploy → Deploy latest commit
```

---

## 🔐 Configuración de SSL/HTTPS

### Con Subdominio (Opción 1)

✅ **Render lo hace automáticamente** con Let's Encrypt. No necesitas hacer nada.

### Con Subpath (Opción 2)

Necesitas **certificado SSL** para `correagro.com`:

#### Si usas Let's Encrypt (Gratuito):

```bash
# Instalar certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx  # Para Nginx
# o
sudo apt install certbot python3-certbot-apache  # Para Apache

# Obtener certificado
sudo certbot --nginx -d correagro.com -d www.correagro.com  # Nginx
# o
sudo certbot --apache -d correagro.com -d www.correagro.com  # Apache

# Renovación automática (verificar)
sudo certbot renew --dry-run
```

---

## ✅ Verificación y Pruebas

### 1. Verificar DNS

```bash
# Para subdominio
nslookup cipa.correagro.com
dig cipa.correagro.com

# Debería resolver a cipa-frontend.onrender.com
```

### 2. Verificar Conectividad

```bash
# Test de conectividad
curl -I https://cipa.correagro.com  # Subdominio
# o
curl -I https://correagro.com/intranet/cipa  # Subpath
```

### 3. Probar API

```bash
# Health check
curl https://cipa-api.correagro.com/api/health  # Subdominio
# o
curl https://correagro.com/intranet/cipa/api/health  # Subpath
```

### 4. Probar en Navegador

Abrir:
```
https://cipa.correagro.com  # Subdominio
# o
https://correagro.com/intranet/cipa  # Subpath
```

---

## 🔍 Solución de Problemas

### ❌ DNS no resuelve

**Problema**: `nslookup` no encuentra el subdominio

**Causas**:
1. CNAME no configurado correctamente en GoDaddy
2. Propagación de DNS en progreso (puede tardar hasta 48h, usualmente 5-30 min)

**Solución**:
1. Verificar registro CNAME en GoDaddy
2. Usar [whatsmydns.net](https://www.whatsmydns.net/) para verificar propagación global
3. Esperar más tiempo

---

### ❌ Error 502 Bad Gateway

**Problema**: Nginx/Apache no puede conectarse a Render

**Causas**:
1. Servicio de Render suspendido (cold start)
2. URL de proxy incorrecta
3. Headers mal configurados

**Solución**:
1. Acceder directamente a `https://cipa-frontend.onrender.com` para "despertar" el servicio
2. Verificar que las URLs en la configuración de proxy sean correctas
3. Revisar logs del servidor:
   ```bash
   sudo tail -f /var/log/nginx/error.log  # Nginx
   sudo tail -f /var/log/apache2/error.log  # Apache
   ```

---

### ❌ CORS Error

**Problema**: Frontend no puede conectarse al backend

**Solución**:

1. **En Render → cipa-backend → Environment**, agregar el dominio:
   ```env
   CORS_ORIGINS=https://cipa.correagro.com,https://correagro.com
   ```

2. **Verificar** en `backend/api/app.py`:
   ```python
   CORS(app, resources={r"/api/*": {
       "origins": ["https://cipa.correagro.com", "https://correagro.com"],
       "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
       "allow_headers": ["Content-Type", "Authorization"],
       "expose_headers": ["Content-Type", "Authorization"],
       "supports_credentials": True
   }})
   ```

3. **Redeploy** el backend

---

### ❌ Assets no cargan (CSS/JS 404)

**Problema**: Frontend carga pero sin estilos ni JavaScript

**Causa**: Rutas de assets mal configuradas para subpath

**Solución**:

Verificar en **frontend/.env.production**:
```env
VITE_USE_SUBPATH=true  # Para subpath
# o
VITE_USE_SUBPATH=false  # Para subdominio
```

Redeploy del frontend.

---

### ❌ Redirect loops

**Problema**: Navegador muestra "Too many redirects"

**Causa**: Configuración de proxy reverso incorrecta

**Solución**:

1. Verificar headers en Nginx:
   ```nginx
   proxy_set_header X-Forwarded-Proto $scheme;
   proxy_set_header X-Forwarded-Host $host;
   ```

2. No usar `proxy_redirect` a menos que sea necesario

---

## 📊 Tabla Comparativa Final

| Aspecto | Subdominio | Subpath |
|---------|-----------|---------|
| **URL** | `cipa.correagro.com` | `correagro.com/intranet/cipa` |
| **Configuración** | 10 minutos | 1-2 horas |
| **Mantenimiento** | Mínimo | Alto |
| **Requiere Servidor** | ❌ No | ✅ Sí |
| **SSL Automático** | ✅ Sí (Render) | ❌ No (manual) |
| **Dificultad** | ⭐ Fácil | ⭐⭐⭐ Difícil |
| **Recomendado** | ✅ **SÍ** | ⚠️ Solo si es necesario |

---

## 🎯 Recomendación Final

**Usa la Opción 1 (Subdominio)** a menos que tengas una razón MUY específica para necesitar el subpath.

Ventajas del Subdominio:
- ✅ Configuración en 10 minutos
- ✅ SSL automático y gratuito
- ✅ No requiere servidor propio
- ✅ Más fácil de mantener
- ✅ Mejor rendimiento (sin proxy intermedio)
- ✅ Menos puntos de falla

La URL `cipa.correagro.com` es profesional y fácil de recordar.

---

## 🆘 Necesitas Ayuda?

Si tienes problemas con la configuración:

1. **Revisar logs** del servidor web
2. **Verificar DNS** con `nslookup` y `dig`
3. **Probar acceso directo** a Render: `https://cipa-frontend.onrender.com`
4. **Consultar documentación**:
   - Render: https://render.com/docs/custom-domains
   - GoDaddy: https://www.godaddy.com/help/add-a-cname-record-19236

---

**Última actualización**: 2025-11-10
