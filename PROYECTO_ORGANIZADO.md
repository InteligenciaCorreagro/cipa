# 📁 Estructura del Proyecto CIPA - Organizada

## 🎯 Nueva Organización

El proyecto ha sido reorganizado de manera profesional para mejor mantenibilidad y claridad.

```
cipa/
├── backend/                 # 🔧 Backend completo
│   ├── api/                # API REST con Flask
│   │   ├── app.py         # Aplicación principal
│   │   ├── auth.py        # Sistema de autenticación
│   │   └── requirements.txt
│   ├── core/               # 💼 Módulos de negocio
│   │   ├── api_client.py  # Cliente API SIESA
│   │   ├── archivador_notas.py
│   │   ├── business_rules.py
│   │   ├── email_sender.py
│   │   ├── excel_processor.py
│   │   └── notas_credito_manager.py
│   ├── scripts/            # 🛠️ Scripts de utilidad
│   │   ├── inicializar_auth.py
│   │   ├── verificar_usuario_admin.py
│   │   ├── backup_database.py
│   │   ├── test_sistema.py
│   │   ├── migrations/    # Scripts de migración
│   │   └── ...
│   ├── data/               # 💾 Base de datos
│   │   └── notas_credito.db
│   ├── config/             # ⚙️ Configuraciones
│   ├── main.py             # Script principal de procesamiento
│   ├── iniciar_api.py      # Script para iniciar API
│   ├── requirements.txt    # Dependencias Python
│   └── .env.example        # Plantilla de variables de entorno
│
├── frontend/               # 🎨 Frontend React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── ...
│   ├── package.json
│   └── README.md
│
├── docs/                   # 📚 Documentación
│   ├── ARQUITECTURA.md
│   ├── CAMBIOS_SISTEMA.md
│   ├── GUIA_RAPIDA.md
│   ├── NUEVAS_FUNCIONALIDADES.md
│   └── SOLUCION_AUTH.md
│
├── postman/                # 🧪 Colección Postman
│   ├── CIPA_API_Collection.postman_collection.json
│   └── README.md
│
├── .gitignore
├── .env.example
└── README.md
```

## 🚀 Inicio Rápido

### Backend

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
cd backend
pip install -r requirements.txt

# Inicializar autenticación (primera vez)
python scripts/inicializar_auth.py

# Iniciar API
python iniciar_api.py
# o
python api/app.py
```

La API estará en: `http://localhost:5000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend estará en: `http://localhost:3000`

## 📋 Scripts Disponibles

### Backend Scripts

| Script | Ubicación | Descripción |
|--------|-----------|-------------|
| `iniciar_api.py` | `backend/` | Inicia la API REST con verificaciones |
| `main.py` | `backend/` | Proceso principal de notas de crédito |
| `inicializar_auth.py` | `backend/scripts/` | Inicializa sistema de autenticación |
| `verificar_usuario_admin.py` | `backend/scripts/` | Verifica usuario admin |
| `backup_database.py` | `backend/scripts/` | Backup de la base de datos |
| `test_sistema.py` | `backend/scripts/` | Tests del sistema |

### Ejemplos de Uso

```bash
# Inicializar autenticación
cd backend
python scripts/inicializar_auth.py

# Verificar usuario admin
python scripts/verificar_usuario_admin.py

# Backup de BD
python scripts/backup_database.py

# Procesar notas
python main.py

# Tests
python scripts/test_sistema.py
```

## 🔐 Autenticación

**Credenciales por defecto:**
```
Username: admin
Password: admin123
```

⚠️ **IMPORTANTE:** Cambiar la contraseña después del primer login.

## 📖 Documentación

Toda la documentación está en la carpeta `docs/`:

- **`ARQUITECTURA.md`** - Diagramas y arquitectura del sistema
- **`GUIA_RAPIDA.md`** - Guía de implementación rápida
- **`CAMBIOS_SISTEMA.md`** - Historial de cambios
- **`NUEVAS_FUNCIONALIDADES.md`** - Nuevas features
- **`SOLUCION_AUTH.md`** - Solución a problemas de autenticación

## 🗂️ Módulos Core

### `api_client.py`
Cliente para API SIESA

### `business_rules.py`
Reglas de negocio (validaciones, filtros)

### `notas_credito_manager.py`
Gestión de notas de crédito

### `archivador_notas.py`
Sistema de archivado

### `excel_processor.py`
Generación de reportes Excel

### `email_sender.py`
Envío de correos

## 🔧 Configuración

### Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```env
# API
JWT_SECRET_KEY=your-secret-key-here
API_PORT=5000
DEBUG=False

# Database
DB_PATH=./data/notas_credito.db

# SIESA API (si aplica)
CONNI_KEY=your-key
CONNI_TOKEN=your-token

# Email (si aplica)
EMAIL_USERNAME=your-email
EMAIL_PASSWORD=your-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## 🧪 Testing

### API con Postman

1. Importar colección desde `postman/`
2. Configurar environment con la URL base
3. Ejecutar el login para obtener tokens
4. Probar endpoints

### Frontend

```bash
cd frontend
npm run build  # Compilar
npm run test   # Tests (si hay)
```

## 📦 Deployment

### Backend

#### Con Docker (recomendado)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
CMD ["python", "api/app.py"]
```

#### Sin Docker

```bash
# Producción
cd backend
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 api.app:app
```

### Frontend

```bash
cd frontend
npm run build
# Servir carpeta dist/ con nginx, apache, etc.
```

## 🆘 Solución de Problemas

### Backend no inicia

1. Verificar dependencias: `pip install -r backend/requirements.txt`
2. Verificar BD: `python backend/scripts/verificar_usuario_admin.py`
3. Verificar logs en consola

### Frontend no conecta

1. Verificar que backend esté corriendo en `http://localhost:5000`
2. Verificar `frontend/.env` tenga `VITE_API_URL=http://localhost:5000`
3. Revisar consola del navegador

### Tokens inválidos

1. Ejecutar `python backend/scripts/inicializar_auth.py`
2. Verificar que las tablas de autenticación existan
3. Revisar `docs/SOLUCION_AUTH.md`

## 📝 Migración desde Estructura Anterior

Si tienes la estructura antigua:

1. ✅ Archivos movidos a `backend/`
2. ✅ Scripts movidos a `backend/scripts/`
3. ✅ Documentación movida a `docs/`
4. ✅ Imports actualizados

Los archivos antiguos en la raíz pueden ser eliminados después de verificar que todo funciona.

## 🎯 Próximos Pasos

1. [ ] Probar backend con `python backend/api/app.py`
2. [ ] Probar frontend con `npm run dev`
3. [ ] Verificar autenticación
4. [ ] Ejecutar tests
5. [ ] Deploy a producción

## 💡 Consejos

- **Usa entorno virtual** para evitar conflictos de dependencias
- **Lee la documentación** en `docs/` antes de modificar
- **Haz backup** de la BD regularmente con `backend/scripts/backup_database.py`
- **Revisa los logs** para debugging

## 📞 Soporte

Para problemas o preguntas:
1. Revisar documentación en `docs/`
2. Revisar logs de la API
3. Consultar `SOLUCION_AUTH.md` para problemas de autenticación

---

**Proyecto reorganizado profesionalmente** 🎉
