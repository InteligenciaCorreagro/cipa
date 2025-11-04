# 🏢 Sistema CIPA - Gestión de Notas de Crédito

Sistema completo para gestión de notas de crédito con API REST, frontend profesional y procesamiento automatizado.

## 📁 Estructura del Proyecto

```
cipa/
├── backend/          # 🔧 Backend completo (Python/Flask)
│   ├── api/         # API REST con autenticación JWT
│   ├── core/        # Módulos de negocio
│   ├── scripts/     # Scripts de utilidad y migrations
│   ├── data/        # Base de datos SQLite
│   └── config/      # Configuraciones
│
├── frontend/         # 🎨 Frontend (React + TypeScript + Vite)
│   ├── src/         # Código fuente
│   └── dist/        # Build de producción
│
├── docs/             # 📚 Documentación completa
│   ├── ARQUITECTURA.md
│   ├── GUIA_RAPIDA.md
│   └── SOLUCION_AUTH.md
│
└── postman/          # 🧪 Colección Postman para testing
```

## 🚀 Inicio Rápido

### Backend (API REST)

```bash
# 1. Ir al backend
cd backend

# 2. Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar autenticación (primera vez)
python scripts/inicializar_auth.py

# 5. Iniciar API
python api/app.py
```

**API disponible en:** `http://localhost:5000`

**Credenciales por defecto:**
- Username: `admin`
- Password: `admin123`

### Frontend (Interfaz Web)

```bash
# 1. Ir al frontend
cd frontend

# 2. Instalar dependencias (primera vez)
npm install

# 3. Iniciar servidor de desarrollo
npm run dev
```

**Frontend disponible en:** `http://localhost:3000`

## ✨ Características

### 🔐 Backend
- ✅ API REST con Flask
- ✅ Autenticación JWT (Access + Refresh tokens)
- ✅ Rate limiting y seguridad
- ✅ Base de datos SQLite
- ✅ Sistema de notas de crédito
- ✅ Gestión de aplicaciones
- ✅ Estadísticas y reportes

### 🎨 Frontend
- ✅ React 18 + TypeScript
- ✅ Diseño minimalista con Tailwind CSS
- ✅ Dashboard con estadísticas
- ✅ Gestión de notas de crédito
- ✅ Sistema de autenticación completo
- ✅ Manejo de errores robusto
- ✅ Responsive design

### 💼 Lógica de Negocio
- ✅ Validación de tipos de inventario
- ✅ Validación de monto mínimo
- ✅ Aplicación automática de notas de crédito
- ✅ Historial completo de aplicaciones
- ✅ Generación de reportes Excel
- ✅ Envío por email (opcional)

## 📡 API Endpoints

### Autenticación
```
POST   /api/auth/login              # Login
POST   /api/auth/logout             # Logout
POST   /api/auth/refresh            # Refresh token
POST   /api/auth/change-password    # Cambiar contraseña
```

### Notas de Crédito
```
GET    /api/notas                   # Listar notas
GET    /api/notas/<id>              # Obtener nota
GET    /api/notas/estadisticas      # Estadísticas
GET    /api/notas/por-estado        # Agrupado por estado
GET    /api/aplicaciones/<numero>   # Aplicaciones
GET    /api/health                  # Health check
```

## 🗂️ Documentación Completa

Toda la documentación está en la carpeta `docs/`:

- **[ARQUITECTURA.md](docs/ARQUITECTURA.md)** - Diagramas y arquitectura del sistema
- **[GUIA_RAPIDA.md](docs/GUIA_RAPIDA.md)** - Guía de implementación rápida
- **[CAMBIOS_SISTEMA.md](docs/CAMBIOS_SISTEMA.md)** - Historial de cambios
- **[NUEVAS_FUNCIONALIDADES.md](docs/NUEVAS_FUNCIONALIDADES.md)** - Nuevas features
- **[SOLUCION_AUTH.md](docs/SOLUCION_AUTH.md)** - Solución a problemas de autenticación
- **[PROYECTO_ORGANIZADO.md](PROYECTO_ORGANIZADO.md)** - Guía de la estructura

## 🛠️ Scripts Disponibles

### Backend
```bash
cd backend

# Autenticación
python scripts/inicializar_auth.py          # Inicializar sistema de auth
python scripts/verificar_usuario_admin.py   # Verificar usuario admin

# Utilidades
python scripts/backup_database.py           # Backup de la BD
python scripts/test_sistema.py              # Tests del sistema
python scripts/consultar_notas.py           # Consultar notas
python scripts/reporte_diario.py            # Generar reporte

# Proceso principal
python main.py                               # Procesar notas de crédito
```

### Frontend
```bash
cd frontend

npm run dev         # Desarrollo
npm run build       # Build para producción
npm run preview     # Preview del build
npm run lint        # Linter
```

## 💾 Base de Datos

**Ubicación:** `backend/data/notas_credito.db`

### Tablas Principales

- `notas_credito` - Notas de crédito registradas
- `aplicaciones_notas` - Historial de aplicaciones
- `usuarios` - Usuarios del sistema
- `sesiones` - Sesiones JWT activas
- `intentos_login` - Log de intentos de acceso

### Backup
```bash
cd backend
python scripts/backup_database.py
```

## ⚙️ Configuración

### Variables de Entorno

Copiar `backend/.env.example` a `backend/.env`:

```env
# JWT
JWT_SECRET_KEY=tu-secret-key-aqui

# API
API_PORT=5000
DEBUG=False

# Database
DB_PATH=./data/notas_credito.db

# Email (opcional)
EMAIL_USERNAME=tu-email
EMAIL_PASSWORD=tu-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## 🧪 Testing

### Con Postman

1. Importar colección desde `postman/`
2. Configurar environment con URL base
3. Ejecutar login para obtener tokens
4. Probar endpoints protegidos

### Con curl

```bash
# Health check
curl http://localhost:5000/api/health

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Obtener estadísticas (requiere token)
curl http://localhost:5000/api/notas/estadisticas \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

## 📦 Deployment

### Backend con Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["python", "api/app.py"]
```

### Frontend

```bash
cd frontend
npm run build
# Servir carpeta dist/ con nginx, apache, vercel, netlify, etc.
```

## 🔒 Seguridad

- ✅ JWT con access y refresh tokens
- ✅ Passwords con bcrypt
- ✅ Rate limiting por IP
- ✅ CORS configurado
- ✅ Bloqueo temporal tras intentos fallidos
- ✅ Logging de accesos

## 🆘 Solución de Problemas

### Backend no inicia
1. Verificar dependencias: `pip install -r backend/requirements.txt`
2. Inicializar auth: `python backend/scripts/inicializar_auth.py`
3. Revisar logs en consola

### Frontend no conecta
1. Verificar que backend esté en `http://localhost:5000`
2. Verificar `.env` del frontend
3. Revisar consola del navegador

### Tokens inválidos
```bash
cd backend
python scripts/inicializar_auth.py
python scripts/verificar_usuario_admin.py
```

Ver `docs/SOLUCION_AUTH.md` para más detalles.

## 🔗 Recursos

- **Backend README:** [backend/README.md](backend/README.md)
- **Frontend README:** [frontend/README.md](frontend/README.md)
- **API Documentation:** [backend/api/README.md](backend/api/README.md)
- **Postman Collection:** [postman/README.md](postman/README.md)

## 🤝 Contribuir

1. Crear rama desde `main`
2. Hacer cambios
3. Probar localmente
4. Commit con mensajes descriptivos
5. Push y crear Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 📞 Soporte

Para problemas o preguntas:
1. Revisar documentación en `docs/`
2. Revisar logs de la API
3. Consultar `SOLUCION_AUTH.md` para problemas de autenticación

---

**Desarrollado con las mejores prácticas de desarrollo moderno** 🚀
