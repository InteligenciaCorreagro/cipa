# Solución al Problema de Autenticación

## ✅ Problema Identificado

El token no estaba funcionando porque:
1. **Las tablas de autenticación no existían en la base de datos**
2. **El usuario admin no estaba creado**

## ✅ Problema Resuelto

Ya se inicializó el sistema de autenticación correctamente:

```bash
✅ Tablas creadas: usuarios, sesiones, intentos_login
✅ Usuario admin creado exitosamente
✅ Credenciales configuradas
```

### Credenciales de Acceso

```
Username: admin
Password: admin123
```

## 🔧 Scripts Creados

### 1. `inicializar_auth.py`
Script que inicializa el sistema de autenticación:
- Crea las tablas necesarias
- Crea el usuario admin
- Verifica que todo esté configurado correctamente

```bash
python inicializar_auth.py
```

### 2. `verificar_usuario_admin.py`
Script para verificar el estado del usuario admin:
- Muestra todos los usuarios en la BD
- Verifica el hash de contraseñas
- Muestra el estado de bloqueos

```bash
python verificar_usuario_admin.py
```

## 🚀 Cómo Iniciar la API

### Opción 1: Usando Python directamente

```bash
# Desde la raíz del proyecto
python api/app.py
```

La API estará disponible en: `http://localhost:5000`

### Opción 2: Usando el script de inicio

```bash
python iniciar_api.py
```

## 🧪 Probar con Postman

1. **Login:**
   - **POST** `http://localhost:5000/api/auth/login`
   - **Body (JSON):**
     ```json
     {
       "username": "admin",
       "password": "admin123"
     }
     ```
   - **Respuesta esperada:**
     ```json
     {
       "access_token": "eyJ0eXAiOiJKV1QiLC...",
       "refresh_token": "eyJ0eXAiOiJKV1QiLC...",
       "usuario": {
         "id": 1,
         "username": "admin",
         "email": "admin@cipa.com",
         "rol": "admin"
       }
     }
     ```

2. **Usar el token:**
   - Copiar el `access_token`
   - En las peticiones siguientes, agregar header:
     ```
     Authorization: Bearer eyJ0eXAiOiJKV1QiLC...
     ```

3. **Obtener estadísticas:**
   - **GET** `http://localhost:5000/api/notas/estadisticas`
   - **Header:** `Authorization: Bearer <tu_access_token>`

## 🌐 Probar con el Frontend

1. **Iniciar el frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Acceder:**
   - Abrir: `http://localhost:3000`
   - Login con: `admin` / `admin123`

## ⚠️ Problema Actual con Dependencias

Hay un problema con las dependencias de `cryptography` y `cffi` que causa que la API no inicie automáticamente.

### Soluciones Posibles:

#### Solución 1: Usar un entorno virtual (RECOMENDADO)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r api/requirements.txt

# Iniciar API
python api/app.py
```

#### Solución 2: Reinstalar cryptography

```bash
pip uninstall cryptography cffi
pip install --no-binary :all: cryptography cffi
pip install -r api/requirements.txt
```

#### Solución 3: Usar Docker (si está disponible)

Crear `Dockerfile` para la API:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api/app.py"]
```

## 📋 Verificación

Para verificar que todo está funcionando:

```bash
# 1. Verificar que la BD tiene las tablas
python verificar_usuario_admin.py

# 2. Iniciar la API
python api/app.py

# 3. En otra terminal, probar el endpoint de health
curl http://localhost:5000/api/health

# 4. Probar login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## ✨ Estado Actual

```
✅ Base de datos: OK
✅ Tablas de autenticación: Creadas
✅ Usuario admin: Creado
✅ Frontend: Configurado con manejo de errores
⚠️  API: Problema con dependencias (requiere entorno virtual)
```

## 📞 Siguiente Paso

**RECOMENDACIÓN:** Usar un entorno virtual de Python para evitar conflictos de dependencias:

```bash
# Desde la raíz del proyecto
python3 -m venv venv
source venv/bin/activate
pip install -r api/requirements.txt
python api/app.py
```

Esto resolverá el problema de dependencias y la API funcionará correctamente.
