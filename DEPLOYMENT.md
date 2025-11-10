# 🚀 Guía de Deployment - CIPA en Railway

Esta guía te llevará paso a paso para desplegar la aplicación CIPA en Railway de forma **100% GRATUITA** y configurarla para que funcione en el subpath `correagro.com/intranet/cipa`.

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Deployment en Railway](#deployment-en-railway)
3. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
4. [Configuración de GoDaddy](#configuración-de-godaddy)
5. [Verificación del Deployment](#verificación-del-deployment)
6. [Solución de Problemas](#solución-de-problemas)
7. [Medidas de Seguridad](#medidas-de-seguridad)

---

## ✅ Requisitos Previos

- ✅ Cuenta en [Railway.app](https://railway.app) (con GitHub)
- ✅ Repositorio en GitHub con el código de CIPA
- ✅ Acceso a la cuenta de GoDaddy con el dominio `correagro.com`
- ✅ Usuario administrador creado en la aplicación (ver sección de inicialización)

---

## 🚂 Deployment en Railway

### Paso 1: Crear Proyecto en Railway

1. **Inicia sesión en Railway**
   - Ve a [https://railway.app](https://railway.app)
   - Haz clic en "Login" y autentícate con tu cuenta de GitHub

2. **Crear nuevo proyecto**
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Busca y selecciona el repositorio `InteligenciaCorreagro/cipa`
   - Selecciona la rama `claude/deploy-railway-intranet-setup-011CUzK7LHYPqoX7JVpmDm4y`

3. **Railway detectará automáticamente el Dockerfile**
   - Railway usará el archivo `Dockerfile` en la raíz del proyecto
   - El build comenzará automáticamente

### Paso 2: Esperar el Build

El proceso de build tomará aproximadamente **5-10 minutos**. Railway:
- ✅ Construirá el frontend con React + Vite
- ✅ Instalará las dependencias de Python
- ✅ Configurará el backend Flask
- ✅ Creará la imagen Docker optimizada

---

## ⚙️ Configuración de Variables de Entorno

### Paso 3: Configurar Variables en Railway

1. **Ve a la sección de Variables**
   - En tu proyecto de Railway, haz clic en la pestaña "Variables"

2. **Agregar las siguientes variables:**

   ```bash
   # 🔐 SEGURIDAD - JWT (OBLIGATORIO)
   JWT_SECRET_KEY=<GENERAR_CLAVE_ALEATORIA_64_CARACTERES>

   # 🌍 CONFIGURACIÓN DE RUTA
   BASE_PATH=/intranet/cipa
   VITE_BASE_PATH=/intranet/cipa

   # 🐛 DEBUG (Producción)
   DEBUG=False

   # 📊 LOGGING
   LOG_LEVEL=INFO
   ```

3. **Generar JWT_SECRET_KEY seguro:**

   En tu terminal local, ejecuta:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

   Copia el resultado y úsalo como valor de `JWT_SECRET_KEY`.

4. **Aplicar cambios**
   - Haz clic en "Add" o "Update"
   - Railway reiniciará automáticamente el servicio

---

## 🌐 Configuración de GoDaddy

### Paso 4: Obtener URL de Railway

1. **En Railway, ve a Settings > Networking**
2. **Genera un dominio público:**
   - Haz clic en "Generate Domain"
   - Obtendrás una URL como: `https://tu-proyecto.up.railway.app`
3. **Copia esta URL** (la necesitarás para GoDaddy)

### Paso 5: Configurar Subpath en GoDaddy

Hay **dos opciones** para configurar el subpath en GoDaddy:

---

#### **OPCIÓN A: Redirect con Path Forwarding (Recomendado)**

Esta opción es más simple y funciona mejor para subpaths.

1. **Inicia sesión en GoDaddy**
   - Ve a [https://godaddy.com](https://godaddy.com)
   - Inicia sesión con tu cuenta

2. **Ve a Dominios > correagro.com**
   - Haz clic en "Administrar" junto a `correagro.com`

3. **Configurar Forwarding (Redirección con Path)**

   En GoDaddy, las redirecciones de subpath se configuran mediante:
   - **Subdirectorios + Forwarding**

   **Pasos:**

   a. **Crear un subdirectorio forwarding:**
      - Ve a "Forwarding" o "Redirección"
      - Haz clic en "Add" o "Agregar"
      - En "Domain/Subdirectory" ingresa: `correagro.com/intranet/cipa`
      - En "Forward to" ingresa: `https://tu-proyecto.up.railway.app/intranet/cipa`
      - Tipo: `301 (Permanent)` o `302 (Temporary)`
      - Forward settings: Selecciona "Forward only" o "Forward with masking"
      - Haz clic en "Save"

---

#### **OPCIÓN B: Reverse Proxy con Cloudflare (Avanzado)**

Si necesitas mantener la URL `correagro.com/intranet/cipa` visible en el navegador sin redirección, necesitarás un reverse proxy.

**GoDaddy no soporta reverse proxy directamente**, pero puedes usar **Cloudflare** (gratuito):

1. **Configurar Cloudflare**
   - Crea cuenta en [Cloudflare](https://cloudflare.com)
   - Agrega el dominio `correagro.com`
   - Cambia los nameservers en GoDaddy a los de Cloudflare

2. **Crear Cloudflare Worker para Reverse Proxy**

   a. Ve a Workers & Pages > Create Worker

   b. Usa este código:

   ```javascript
   addEventListener('fetch', event => {
     event.respondWith(handleRequest(event.request))
   })

   async function handleRequest(request) {
     const url = new URL(request.url)

     // Si la ruta comienza con /intranet/cipa
     if (url.pathname.startsWith('/intranet/cipa')) {
       // Proxy a Railway
       const railwayUrl = 'https://tu-proyecto.up.railway.app' + url.pathname + url.search

       const modifiedRequest = new Request(railwayUrl, {
         method: request.method,
         headers: request.headers,
         body: request.body
       })

       const response = await fetch(modifiedRequest)
       return response
     }

     // Para otras rutas, continuar normal
     return fetch(request)
   }
   ```

   c. **Deploy el Worker**

   d. **Configurar Route en Cloudflare:**
      - Ve a Workers > Routes
      - Agrega route: `correagro.com/intranet/cipa/*`
      - Selecciona el Worker creado

---

### ⚠️ Limitaciones de GoDaddy

**IMPORTANTE:** GoDaddy tiene limitaciones significativas para configurar subpaths:

1. **No soporta reverse proxy nativo**
   - Solo permite forwarding (redirección)

2. **Forwarding con subpath:**
   - La redirección cambiará la URL en el navegador
   - No es completamente "transparente"

3. **Alternativas recomendadas:**
   - ✅ **Cloudflare Workers** (gratuito, mejor opción)
   - ✅ **Migrar a un hosting con soporte de reverse proxy** (Nginx, Apache)
   - ✅ **Usar un subdominio en lugar de subpath:** `cipa.correagro.com`

---

### 🎯 Opción Alternativa: Usar Subdominios

Si las limitaciones de subpath son problemáticas, considera usar un **subdominio**:

**En lugar de:** `correagro.com/intranet/cipa`
**Usar:** `intranet.correagro.com` o `cipa.correagro.com`

**Ventajas:**
- ✅ Configuración más simple en GoDaddy (solo DNS)
- ✅ No requiere Cloudflare Workers
- ✅ Mejor performance
- ✅ Sin limitaciones de proxy

**Configuración en GoDaddy para subdominios:**

1. Ve a DNS Management
2. Agrega un registro CNAME:
   - **Type:** CNAME
   - **Name:** `intranet` (o `cipa`)
   - **Value:** `tu-proyecto.up.railway.app.`
   - **TTL:** 1 Hour
3. Guarda los cambios

4. Actualiza variables en Railway:
   ```bash
   BASE_PATH=/
   VITE_BASE_PATH=/
   ```

---

## ✅ Verificación del Deployment

### Paso 6: Verificar que la Aplicación Funciona

1. **Health Check**
   - Abre tu navegador
   - Ve a: `https://tu-proyecto.up.railway.app/intranet/cipa/api/health`
   - Deberías ver:
     ```json
     {
       "status": "healthy",
       "timestamp": "2025-11-10T...",
       "version": "1.0.1",
       "base_path": "/intranet/cipa"
     }
     ```

2. **Acceder a la Interfaz**
   - Ve a: `https://correagro.com/intranet/cipa` (o tu URL configurada)
   - Deberías ver la página de login de CIPA

3. **Verificar Login**
   - Ingresa con las credenciales creadas
   - Si no tienes usuario, sigue la sección de inicialización

---

## 🔐 Medidas de Seguridad Implementadas

La aplicación incluye múltiples capas de seguridad:

### ✅ Autenticación y Autorización
- **JWT (JSON Web Tokens)** con Access + Refresh tokens
- **Expiración de tokens:** Access (1 hora), Refresh (30 días)
- **Password hashing** con bcrypt (salt rounds: 12)
- **Rate limiting** en endpoints de login (5 intentos/minuto)
- **Bloqueo automático** tras múltiples intentos fallidos

### ✅ Seguridad de Red
- **CORS** configurado para orígenes permitidos
- **HTTPS** forzado en Railway (automático)
- **Proxy headers** validados (X-Forwarded-For, X-Real-IP)

### ✅ Seguridad de Datos
- **Base de datos SQLite** con permisos restrictivos
- **Logs de auditoría** de accesos y operaciones
- **Sesiones revocables** (logout invalida tokens)

### ✅ Buenas Prácticas
- **Usuario no-root** en Docker
- **Variables de entorno** para configuración sensible
- **Health checks** para monitoreo
- **Dependencias actualizadas** y sin vulnerabilidades conocidas

### ✅ Recomendaciones Adicionales

1. **Cambia el JWT_SECRET_KEY regularmente**
   - Cada 3-6 meses o si sospechas de compromiso

2. **Monitorea los logs**
   - Revisa logs en Railway Dashboard > Deployments > Logs

3. **Backup de base de datos**
   - Configura backups automáticos de `/app/backend/data/notas_credito.db`

4. **Límites de recursos**
   - Railway Free Tier: 500 horas/mes, 512MB RAM, 1GB storage
   - Monitorea el uso en Railway Dashboard

---

## 🐛 Solución de Problemas

### Error: "Application failed to respond"

**Causa:** La aplicación no está respondiendo en el puerto correcto.

**Solución:**
1. Verifica que la variable `PORT` esté configurada en Railway
2. Revisa los logs: Railway Dashboard > Logs
3. Verifica que el health check funcione

---

### Error: "Token inválido" en el frontend

**Causa:** JWT_SECRET_KEY no está configurado o cambió.

**Solución:**
1. Configura `JWT_SECRET_KEY` en Railway
2. Reinicia el servicio
3. Limpia el localStorage del navegador (F12 > Application > Local Storage > Clear)

---

### Error: "Cannot GET /intranet/cipa"

**Causa:** El routing no está configurado correctamente.

**Solución:**
1. Verifica que `BASE_PATH` y `VITE_BASE_PATH` estén configurados
2. Verifica que el build del frontend se ejecutó con la variable `VITE_BASE_PATH`
3. Verifica los logs del servidor

---

### La página carga pero los estilos no se aplican

**Causa:** Las rutas de los assets no son correctas con el subpath.

**Solución:**
1. Verifica que `VITE_BASE_PATH=/intranet/cipa` esté configurado **ANTES** del build
2. Rebuild el proyecto en Railway:
   - Ve a Deployments
   - Haz clic en "Redeploy"

---

### GoDaddy: "No se puede crear forwarding con subpath"

**Causa:** GoDaddy no soporta forwarding de subpaths de manera nativa.

**Solución:**
1. Usa Cloudflare Workers (ver Opción B arriba)
2. O usa un subdominio en lugar de subpath (más simple)

---

## 📚 Recursos Adicionales

- [Documentación de Railway](https://docs.railway.app)
- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de Vite](https://vitejs.dev)
- [Documentación de Cloudflare Workers](https://developers.cloudflare.com/workers/)
- [Documentación de GoDaddy DNS](https://www.godaddy.com/help/dns-management-19873)

---

## 🎉 ¡Listo!

Si seguiste todos los pasos, tu aplicación CIPA debería estar funcionando en:

**URL de Railway:** `https://tu-proyecto.up.railway.app/intranet/cipa`
**URL personalizada:** `https://correagro.com/intranet/cipa`

### Próximos Pasos

1. **Crear usuarios adicionales** (si es necesario)
2. **Importar datos históricos** de notas de crédito
3. **Configurar backups automáticos** de la base de datos
4. **Monitorear el uso** en Railway Dashboard

---

## 🆘 ¿Necesitas Ayuda?

Si tienes problemas con el deployment:

1. Revisa los logs en Railway Dashboard
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que el health check funcione
4. Contacta al soporte técnico si el problema persiste

---

**¡Disfruta de CIPA en producción! 🚀**
