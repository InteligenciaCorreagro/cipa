# 🔴 ERROR: Outlook/Office365 - Autenticación Básica Deshabilitada

## ❌ El Problema

**Error recibido**:
```
(535, b'5.7.139 Authentication unsuccessful, basic authentication is disabled.
[BN9PR03CA0396.namprd03.prod.outlook.com]')
```

**¿Qué significa?**

Microsoft **deshabilitó permanentemente** la autenticación básica (usuario/contraseña) para SMTP en Outlook/Office365 desde **octubre de 2022**.

El sistema actual **NO PUEDE** enviar correos usando una cuenta de Outlook/Office365 con usuario y contraseña.

---

## ✅ Soluciones (3 Opciones)

### 🎯 Opción 1: Usar Gmail (RECOMENDADO - Más Fácil)

Esta es la solución más rápida y simple.

#### Pasos:

1. **Crea una cuenta de Gmail** (si no tienes una):
   - Ve a: https://accounts.google.com/signup
   - O usa una cuenta de Gmail existente

2. **Activa verificación en 2 pasos**:
   - Ve a: https://myaccount.google.com/security
   - Activa "Verificación en 2 pasos"

3. **Crea App Password**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona: App = "Correo", Dispositivo = "Otro"
   - Nombre: "Sistema CIPA"
   - Copia la contraseña de 16 caracteres

4. **Actualiza los GitHub Secrets**:
   ```
   SMTP_SERVER = smtp.gmail.com
   SMTP_PORT = 587
   EMAIL_USERNAME = tucorreo@gmail.com
   EMAIL_PASSWORD = [App Password de 16 caracteres]
   DESTINATARIOS = correos@correagro.com,otros@correagro.com
   ```

**✅ VENTAJAS**:
- Funciona inmediatamente
- Gratis
- Límite: 500 correos/día (más que suficiente)
- Ya está probado y funciona

**❌ DESVENTAJAS**:
- Necesitas crear/usar una cuenta de Gmail

---

### 🎯 Opción 2: Usar Servicio SMTP Profesional (RECOMENDADO para Producción)

Servicios profesionales de correo que funcionan sin problemas:

#### A) **SendGrid** (RECOMENDADO)
- **Gratis**: 100 correos/día permanentemente
- **Muy confiable**: Usado por empresas grandes
- **Fácil de configurar**

**Pasos**:
1. Regístrate: https://signup.sendgrid.com/
2. Verifica tu email
3. Ve a Settings → API Keys → Create API Key
4. Copia la API Key

**Configuración**:
```
SMTP_SERVER = smtp.sendgrid.net
SMTP_PORT = 587
EMAIL_USERNAME = apikey
EMAIL_PASSWORD = [tu API Key completa]
DESTINATARIOS = correos@correagro.com
```

**✅ VENTAJAS**:
- Profesional y confiable
- 100 correos/día gratis (suficiente)
- Estadísticas de entrega
- No requiere cambios en el código

#### B) **Brevo (ex-Sendinblue)**
- **Gratis**: 300 correos/día
- **Fácil de usar**

**Pasos**:
1. Regístrate: https://www.brevo.com/
2. Ve a SMTP & API → SMTP
3. Copia las credenciales

**Configuración**:
```
SMTP_SERVER = smtp-relay.brevo.com
SMTP_PORT = 587
EMAIL_USERNAME = [tu email de Brevo]
EMAIL_PASSWORD = [SMTP Key de Brevo]
DESTINATARIOS = correos@correagro.com
```

#### C) **Amazon SES**
- **Gratis**: 62,000 correos/mes (si tienes cuenta AWS)
- **Más complejo de configurar**

---

### 🎯 Opción 3: Habilitar SMTP Auth en Office365 (Requiere Admin)

**⚠️ DIFÍCIL**: Solo si tienes acceso de administrador a Office365.

Microsoft ahora requiere OAuth2 o habilitar SMTP AUTH por buzón.

#### Si eres administrador de Office365:

1. **Ve al Admin Center de Microsoft 365**:
   - https://admin.microsoft.com

2. **Habilita SMTP AUTH para el buzón específico**:
   ```powershell
   # Requiere PowerShell con módulo Exchange Online
   Connect-ExchangeOnline
   Set-CASMailbox -Identity usuario@dominio.com -SmtpClientAuthenticationDisabled $false
   ```

3. **O crea una "App Password" en Office365**:
   - Ve a: https://myaccount.microsoft.com/security
   - Activa verificación en 2 pasos
   - Genera App Password

4. **Configuración**:
   ```
   SMTP_SERVER = smtp.office365.com
   SMTP_PORT = 587
   EMAIL_USERNAME = tucorreo@correagro.com
   EMAIL_PASSWORD = [App Password]
   ```

**❌ PROBLEMAS**:
- Requiere permisos de administrador de Office365
- Puede que tu organización no permita habilitar SMTP AUTH
- Microsoft lo puede deshabilitar de nuevo

---

## 🚀 Solución Inmediata (15 minutos)

**Te recomiendo Opción 1 (Gmail) por rapidez**:

### Paso a Paso:

1. **Crear cuenta Gmail** (5 min):
   - https://accounts.google.com/signup
   - Usa: `cipa-notificaciones@gmail.com` (o similar)

2. **Configurar 2FA + App Password** (5 min):
   ```bash
   # Ejecuta el script de diagnóstico
   cd backend
   python3 diagnostico_correos.py
   # Selecciona opción 4 para ver instrucciones
   ```

3. **Actualizar GitHub Secrets** (5 min):
   - Ve a: https://github.com/InteligenciaCorreagro/cipa/settings/secrets/actions
   - Actualiza los 5 secrets con las credenciales de Gmail

4. **Probar**:
   ```bash
   # Localmente
   python3 diagnostico_correos.py  # Opción 2

   # En GitHub Actions
   # Ve a Actions → Run workflow
   ```

---

## 📊 Comparación de Opciones

| Opción | Tiempo Setup | Dificultad | Costo | Límite | Recomendado |
|--------|--------------|------------|-------|--------|-------------|
| **Gmail** | 15 min | Fácil | Gratis | 500/día | ✅ Sí (desarrollo) |
| **SendGrid** | 20 min | Fácil | Gratis | 100/día | ✅ Sí (producción) |
| **Brevo** | 20 min | Fácil | Gratis | 300/día | ✅ Sí (alternativa) |
| **Office365** | 2+ horas | Muy difícil | Requiere licencia | Variable | ❌ No (complicado) |

---

## 🔧 Cambios en GitHub Secrets

Independientemente de la opción que elijas, debes actualizar estos secrets:

Ve a: https://github.com/InteligenciaCorreagro/cipa/settings/secrets/actions

### Para Gmail:
```
SMTP_SERVER → smtp.gmail.com
SMTP_PORT → 587
EMAIL_USERNAME → tucorreo@gmail.com
EMAIL_PASSWORD → [App Password de 16 caracteres]
DESTINATARIOS → correos@correagro.com,otros@correagro.com
```

### Para SendGrid:
```
SMTP_SERVER → smtp.sendgrid.net
SMTP_PORT → 587
EMAIL_USERNAME → apikey
EMAIL_PASSWORD → [tu API Key completa de SendGrid]
DESTINATARIOS → correos@correagro.com,otros@correagro.com
```

### Para Brevo:
```
SMTP_SERVER → smtp-relay.brevo.com
SMTP_PORT → 587
EMAIL_USERNAME → [tu email de Brevo]
EMAIL_PASSWORD → [SMTP Key de Brevo]
DESTINATARIOS → correos@correagro.com,otros@correagro.com
```

---

## 🧪 Probar la Nueva Configuración

Después de cambiar los secrets:

1. **Prueba local** (asegúrate de tener .env actualizado):
   ```bash
   cd backend
   python3 diagnostico_correos.py
   # Opción 1: Verificar configuración
   # Opción 2: Enviar correo de prueba
   ```

2. **Prueba en GitHub Actions**:
   - Ve a: https://github.com/InteligenciaCorreagro/cipa/actions
   - Click en "Proceso Diario - Facturas y Notas Crédito"
   - Click en "Run workflow"
   - Espera a que termine
   - Revisa los logs: debe decir "Email enviado exitosamente"

---

## 💡 Mi Recomendación

**Para comenzar AHORA**: Usa **Gmail** (Opción 1)
- Rápido (15 minutos)
- Funciona garantizado
- 500 correos/día son suficientes

**Para producción a largo plazo**: Usa **SendGrid** (Opción 2A)
- Más profesional
- Estadísticas de entrega
- Mejor reputación de IP
- Escalable

**NO recomiendo**: Tratar de arreglar Office365 (Opción 3)
- Muy complicado
- Requiere permisos de admin
- Microsoft puede deshabilitarlo de nuevo

---

## 🆘 Necesitas Ayuda?

Si eliges Gmail, puedo guiarte paso a paso:

1. Dime si ya tienes una cuenta de Gmail o necesitas crear una
2. Te guío para activar 2FA
3. Te ayudo a crear la App Password
4. Verificamos que funcione

Si prefieres SendGrid u otra opción, también puedo ayudarte con eso.

**¿Qué opción prefieres que configuremos?**

---

## 📋 Resumen Ultra-Rápido

**Problema**: Outlook/Office365 bloqueó la autenticación básica

**Solución más rápida**: Usar Gmail
1. Crea cuenta Gmail (o usa una existente)
2. Activa 2FA: https://myaccount.google.com/security
3. Crea App Password: https://myaccount.google.com/apppasswords
4. Actualiza secrets en GitHub
5. ¡Listo!

**Solución profesional**: Usar SendGrid (100 correos/día gratis)
1. Regístrate: https://signup.sendgrid.com/
2. Crea API Key
3. Actualiza secrets en GitHub
4. ¡Listo!

---

**Creado**: 2025-12-10
**Error específico**: Office365 authentication disabled
