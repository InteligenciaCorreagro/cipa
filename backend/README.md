# CIPA Backend

Backend del sistema de gestión de notas de crédito CIPA.

## 📁 Estructura

```
backend/
├── api/                    # API REST
│   ├── app.py             # Aplicación Flask principal
│   ├── auth.py            # Sistema de autenticación JWT
│   └── requirements.txt   # Dependencias de la API
├── core/                   # Módulos de negocio
│   ├── api_client.py      # Cliente API SIESA
│   ├── archivador_notas.py
│   ├── business_rules.py
│   ├── email_sender.py
│   ├── excel_processor.py
│   └── notas_credito_manager.py
├── scripts/                # Scripts de utilidad
│   ├── inicializar_auth.py
│   ├── verificar_usuario_admin.py
│   ├── backup_database.py
│   └── migrations/
├── data/                   # Base de datos SQLite
├── config/                 # Configuraciones
├── main.py                 # Proceso principal
├── iniciar_api.py          # Script de inicio de API
├── requirements.txt        # Dependencias globales
└── .env.example            # Template de variables de entorno
```

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Inicializar Base de Datos

```bash
# Primera vez: crear tablas de autenticación
python scripts/inicializar_auth.py
```

### 4. Iniciar API

```bash
# Opción 1: Script con verificaciones
python iniciar_api.py

# Opción 2: Directamente
python api/app.py
```

La API estará disponible en: `http://localhost:5000`

## 🔐 Autenticación

**Credenciales por defecto:**
```
Username: admin
Password: admin123
```

### Cambiar Contraseña

```bash
# Via API
POST /api/auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "nueva_contraseña": "tu_nueva_contraseña"
}
```

## 📡 Endpoints API

### Autenticación

```
POST   /api/auth/login              # Login
POST   /api/auth/logout             # Logout
POST   /api/auth/refresh            # Refresh token
POST   /api/auth/change-password    # Cambiar contraseña
```

### Notas de Crédito

```
GET    /api/notas                   # Listar notas (con filtros)
GET    /api/notas/<id>              # Obtener nota específica
GET    /api/notas/estadisticas      # Estadísticas generales
GET    /api/notas/por-estado        # Notas agrupadas por estado
GET    /api/aplicaciones/<numero>   # Aplicaciones de una nota
GET    /api/health                  # Health check
```

### Filtros Disponibles

```
?estado=PENDIENTE|PARCIAL|APLICADA
?nit_cliente=123456789
?fecha_desde=2024-01-01
?fecha_hasta=2024-12-31
?limite=50
?offset=0
```

## 🛠️ Scripts

### inicializar_auth.py
Inicializa el sistema de autenticación (primera vez)

```bash
python scripts/inicializar_auth.py
```

### verificar_usuario_admin.py
Verifica el estado del usuario admin

```bash
python scripts/verificar_usuario_admin.py
```

### backup_database.py
Hace backup de la base de datos

```bash
python scripts/backup_database.py
```

### test_sistema.py
Ejecuta tests del sistema

```bash
python scripts/test_sistema.py
```

## 💾 Base de Datos

### Ubicación
```
backend/data/notas_credito.db
```

### Tablas

- `notas_credito` - Notas de crédito registradas
- `aplicaciones_notas` - Historial de aplicaciones
- `usuarios` - Usuarios del sistema
- `sesiones` - Sesiones JWT activas
- `intentos_login` - Log de intentos de login

### Backup

```bash
python scripts/backup_database.py
```

Los backups se guardan en `backend/data/backups/`

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here

# API Configuration
API_PORT=5000
DEBUG=False

# Database
DB_PATH=./data/notas_credito.db

# SIESA API (opcional)
CONNI_KEY=your-key
CONNI_TOKEN=your-token

# Email (opcional)
EMAIL_USERNAME=your-email
EMAIL_PASSWORD=your-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## 🧪 Testing

### Con curl

```bash
# Health check
curl http://localhost:5000/api/health

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Obtener estadísticas
curl http://localhost:5000/api/notas/estadisticas \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Con Postman

Importar colección desde `../postman/`

## 🔧 Desarrollo

### Estructura de Código

- **api/app.py** - Endpoints y lógica de la API
- **api/auth.py** - Sistema de autenticación y autorización
- **core/** - Lógica de negocio reutilizable
- **scripts/** - Utilidades y herramientas

### Agregar Nuevo Endpoint

```python
# En api/app.py

@app.route('/api/mi-endpoint', methods=['GET'])
@jwt_required()
def mi_endpoint():
    """Documentación del endpoint"""
    # Tu lógica aquí
    return jsonify({"data": "..."}), 200
```

### Agregar Nuevo Módulo Core

```python
# En core/mi_modulo.py

class MiModulo:
    def __init__(self):
        # Inicialización
        pass

    def metodo(self):
        # Lógica
        pass
```

## 📊 Monitoreo

### Logs

Los logs se muestran en consola con el formato:
```
2024-10-31 10:30:45 - nombre - NIVEL - mensaje
```

### Health Check

```bash
curl http://localhost:5000/api/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2024-10-31T10:30:45"
}
```

## 🚨 Solución de Problemas

### API no inicia

1. Verificar dependencias instaladas
2. Verificar puerto 5000 disponible
3. Revisar logs en consola

### Error de BD

```bash
python scripts/inicializar_auth.py
```

### Error de tokens

1. Verificar JWT_SECRET_KEY en .env
2. Verificar tablas de autenticación
3. Ver `../docs/SOLUCION_AUTH.md`

## 📚 Documentación Adicional

- **API completa**: `api/README.md`
- **Arquitectura**: `../docs/ARQUITECTURA.md`
- **Guía rápida**: `../docs/GUIA_RAPIDA.md`

## 🔒 Seguridad

- ✅ JWT con refresh tokens
- ✅ Bcrypt para contraseñas
- ✅ Rate limiting por IP
- ✅ CORS configurado
- ✅ Bloqueo temporal tras intentos fallidos
- ✅ Logging de intentos de acceso

## 📦 Dependencias

Ver `requirements.txt` para la lista completa.

Principales:
- Flask 3.0.0
- Flask-JWT-Extended 4.6.0
- Flask-Limiter 3.5.0
- Flask-CORS 4.0.0
- bcrypt 4.1.2
- python-dotenv 1.0.0

## 🤝 Contribuir

1. Crear rama desde `main`
2. Hacer cambios
3. Probar localmente
4. Commit con mensajes descriptivos
5. Push y crear Pull Request

---

**Backend organizado profesionalmente** 🚀
