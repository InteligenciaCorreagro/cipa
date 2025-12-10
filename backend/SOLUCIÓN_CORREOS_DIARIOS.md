# Solución: Correos Diarios No Se Envían

## 🔍 Diagnóstico del Problema

Los correos diarios no se están enviando. Las causas más comunes son:

1. ❌ **Variables de entorno no configuradas** en GitHub Secrets
2. ❌ **Contraseña incorrecta** (Gmail requiere "App Password", no contraseña normal)
3. ❌ **Workflow no se está ejecutando** (deshabilitado o falta configuración)
4. ❌ **Servidor SMTP bloqueado** o credenciales inválidas

---

## ✅ Solución Paso a Paso

### 🔐 Paso 1: Crear App Password en Gmail

**⚠️ IMPORTANTE**: Gmail NO acepta tu contraseña normal para aplicaciones. Debes crear una "App Password".

#### Instrucciones:

1. **Activa la Verificación en 2 Pasos** (requisito):
   - Ve a: https://myaccount.google.com/security
   - Busca "Verificación en 2 pasos"
   - Actívala siguiendo las instrucciones

2. **Crea una App Password**:
   - Ve a: https://myaccount.google.com/apppasswords
   - O en "Seguridad" → "Contraseñas de aplicaciones"
   - Selecciona:
     - **App**: Correo
     - **Dispositivo**: Otro (personalizado)
     - **Nombre**: "Sistema CIPA" o similar
   - Click en **"Generar"**

3. **Copia la contraseña generada**:
   ```
   Ejemplo: abcd efgh ijkl mnop
   ```
   - ⚠️ **Cópiala ahora**, no la volverás a ver
   - Puedes escribirla con o sin espacios

4. **Usa esta contraseña** en `EMAIL_PASSWORD` (NO tu contraseña de Gmail)

---

### ⚙️ Paso 2: Configurar GitHub Secrets

Para que el workflow automático funcione, debes configurar los secretos en GitHub:

1. **Ve a tu repositorio en GitHub**:
   ```
   https://github.com/InteligenciaCorreagro/cipa
   ```

2. **Navega a Settings**:
   - Click en "Settings" (Configuración)
   - En el menú lateral: **"Secrets and variables"** → **"Actions"**

3. **Agrega los siguientes secretos** (click en "New repository secret"):

   | Nombre del Secret | Valor | Ejemplo |
   |------------------|-------|---------|
   | `SMTP_SERVER` | Servidor SMTP | `smtp.gmail.com` |
   | `SMTP_PORT` | Puerto SMTP | `587` |
   | `EMAIL_USERNAME` | Tu email | `tucorreo@gmail.com` |
   | `EMAIL_PASSWORD` | App Password de Gmail | `abcd efgh ijkl mnop` |
   | `DESTINATARIOS` | Correos separados por coma | `email1@correagro.com,email2@correagro.com` |

4. **Verifica que también tengas** (ya deberían estar configurados):
   - `CONNI_KEY` - Clave de API SIESA
   - `CONNI_TOKEN` - Token de API SIESA

---

### 🚀 Paso 3: Probar el Envío Localmente (Opcional)

Antes de depender del workflow automático, prueba que el correo funcione:

```bash
cd backend
python3 diagnostico_correos.py
```

Este script te permite:
1. ✅ Verificar la configuración
2. 📧 Enviar un correo de prueba
3. 📚 Ver instrucciones detalladas
4. 🔍 Diagnosticar problemas

**Sigue el menú interactivo**:
- Opción 1: Verificar configuración
- Opción 2: Enviar correo de prueba
- Opción 4: Ver instrucciones de Gmail App Password

---

### ⏰ Paso 4: Verificar el Workflow de GitHub Actions

1. **Ve a la pestaña "Actions"** en tu repositorio:
   ```
   https://github.com/InteligenciaCorreagro/cipa/actions
   ```

2. **Verifica el workflow "Proceso Diario"**:
   - Debería aparecer en la lista de workflows
   - Busca ejecuciones recientes

3. **Ejecuta manualmente** (para probar):
   - Click en "Proceso Diario - Facturas y Notas Crédito"
   - Click en "Run workflow"
   - Selecciona la rama (main)
   - Click en "Run workflow"

4. **Revisa los logs**:
   - Click en la ejecución que se está ejecutando
   - Expande el paso "Ejecutar proceso de facturas"
   - Busca mensajes sobre el envío de correo:
     ```
     ENVIANDO EMAIL A OPERATIVA
     Email enviado exitosamente
     ```
   - O errores:
     ```
     Error al enviar correo: [mensaje de error]
     ```

---

### 🔍 Paso 5: Verificar que el Workflow se Ejecute Automáticamente

El workflow está configurado para ejecutarse **todos los días a las 8:00 AM** (hora Bogotá):

```yaml
schedule:
  - cron: '0 13 * * *'  # 1:00 PM UTC = 8:00 AM Bogotá
```

**¿Por qué podría no ejecutarse?**

1. **Repositorio privado inactivo**:
   - GitHub desactiva workflows en repos privados sin actividad por 60 días
   - **Solución**: Ejecuta manualmente el workflow una vez

2. **Workflow deshabilitado**:
   - Ve a "Actions" → "Proceso Diario" → Verifica que no diga "Disabled"
   - Si está deshabilitado, click en "Enable workflow"

3. **Rama incorrecta**:
   - El workflow debe estar en la rama `main` o la rama por defecto

---

## 🎯 Checklist de Verificación

Marca cada ítem una vez verificado:

### Configuración de Correo:
- [ ] Tengo una cuenta de Gmail (o servicio SMTP alternativo)
- [ ] Activé la verificación en 2 pasos en Gmail
- [ ] Creé una App Password en Gmail
- [ ] Copié la App Password correctamente

### GitHub Secrets:
- [ ] `SMTP_SERVER` configurado (`smtp.gmail.com`)
- [ ] `SMTP_PORT` configurado (`587`)
- [ ] `EMAIL_USERNAME` configurado (mi correo de Gmail)
- [ ] `EMAIL_PASSWORD` configurado (App Password, NO contraseña normal)
- [ ] `DESTINATARIOS` configurado (correos separados por coma)
- [ ] `CONNI_KEY` configurado
- [ ] `CONNI_TOKEN` configurado

### Workflow:
- [ ] El workflow existe en `.github/workflows/daily_process.yml`
- [ ] El workflow está habilitado (no dice "Disabled")
- [ ] Ejecuté el workflow manualmente para probar
- [ ] Revisé los logs y no hay errores

### Prueba Local:
- [ ] Ejecuté `diagnostico_correos.py`
- [ ] La verificación de configuración pasó
- [ ] Envié un correo de prueba exitosamente
- [ ] Recibí el correo de prueba

---

## 🐛 Problemas Comunes y Soluciones

### Error: "Authentication failed" o "Username and Password not accepted"

**Causa**: Estás usando tu contraseña normal de Gmail en vez de App Password

**Solución**:
1. Ve a https://myaccount.google.com/apppasswords
2. Crea una nueva App Password
3. Actualiza el secret `EMAIL_PASSWORD` en GitHub con esta nueva contraseña

---

### Error: "Connection timed out" o "Could not connect to SMTP server"

**Causa**: Puerto bloqueado o servidor incorrecto

**Solución**:
1. Verifica que `SMTP_SERVER` sea `smtp.gmail.com`
2. Verifica que `SMTP_PORT` sea `587`
3. Si usas firewall corporativo, puede que el puerto 587 esté bloqueado
4. Prueba con puerto `465` (requiere cambios en el código para usar SSL)

---

### Error: "Recipient address rejected"

**Causa**: Direcciones de correo en `DESTINATARIOS` incorrectas

**Solución**:
1. Verifica que los correos estén separados por coma: `email1@example.com,email2@example.com`
2. No uses espacios entre las comas
3. Verifica que los correos sean válidos

---

### El workflow no se ejecuta automáticamente

**Causa**: Workflow deshabilitado o repo inactivo

**Solución**:
1. Ve a Actions → Proceso Diario → Verifica que esté habilitado
2. Si dice "Disabled", click en "Enable workflow"
3. Ejecuta manualmente una vez para reactivar
4. Verifica que el workflow esté en la rama principal

---

### Recibo el correo en SPAM

**Solución**:
1. Marca el correo como "No es spam"
2. Agrega el correo del remitente a tus contactos
3. Crea un filtro para que futuros correos vayan a la bandeja principal

---

## 📧 Alternativas a Gmail

Si Gmail no funciona o prefieres otro servicio:

### Outlook / Office 365:
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
EMAIL_USERNAME=tu_email@outlook.com
EMAIL_PASSWORD=tu_contraseña
```

### Servicios profesionales (recomendados para producción):

1. **SendGrid** (12,000 correos gratis/mes):
   - https://sendgrid.com
   - `SMTP_SERVER=smtp.sendgrid.net`
   - `SMTP_PORT=587`

2. **Amazon SES** (62,000 correos gratis/mes):
   - https://aws.amazon.com/ses/
   - `SMTP_SERVER=email-smtp.us-east-1.amazonaws.com`
   - `SMTP_PORT=587`

3. **Mailgun** (5,000 correos gratis/mes):
   - https://www.mailgun.com
   - `SMTP_SERVER=smtp.mailgun.org`
   - `SMTP_PORT=587`

---

## 🆘 Si Nada Funciona

1. **Ejecuta el diagnóstico**:
   ```bash
   cd backend
   python3 diagnostico_correos.py
   ```

2. **Captura el error completo**:
   - Ejecuta la opción 2 (enviar correo de prueba)
   - Copia el mensaje de error completo

3. **Revisa los logs de GitHub Actions**:
   - Ve a Actions → Última ejecución
   - Copia el log completo del paso "Ejecutar proceso de facturas"

4. **Verifica que las variables estén en el código**:
   ```bash
   cd backend
   grep -n "EMAIL_USERNAME" main.py
   grep -n "DESTINATARIOS" main.py
   ```

---

## ✅ Verificación Final

Después de configurar todo, verifica que funcione:

1. **Prueba local**:
   ```bash
   python3 diagnostico_correos.py
   # Opción 2: Enviar correo de prueba
   ```

2. **Prueba en GitHub Actions**:
   - Ve a Actions → Proceso Diario → Run workflow
   - Espera a que termine
   - Revisa los logs
   - Verifica tu correo

3. **Espera al día siguiente**:
   - El workflow se ejecutará automáticamente a las 8:00 AM
   - Deberías recibir el correo diario

---

## 📚 Archivos Relacionados

- **Workflow**: `.github/workflows/daily_process.yml`
- **Código de envío**: `backend/core/email_sender.py`
- **Proceso principal**: `backend/main.py` (líneas 203-226)
- **Diagnóstico**: `backend/diagnostico_correos.py`
- **Configuración**: `.env.example` (plantilla)

---

## 🎯 Resumen Rápido

**Para que los correos funcionen necesitas**:

1. ✅ App Password de Gmail (NO contraseña normal)
2. ✅ Configurar 5 secrets en GitHub Actions:
   - `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD`, `DESTINATARIOS`
3. ✅ Verificar que el workflow esté habilitado
4. ✅ Probar el envío con `diagnostico_correos.py`

**La causa más común de fallo**: Usar la contraseña normal de Gmail en vez de App Password.

---

**Fecha de creación**: 2025-12-09
**Versión**: 1.0
