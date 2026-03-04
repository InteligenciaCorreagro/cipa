# Despliegue en Railway (Backend + Frontend)

## Estructura de ramas

- `production-backend`: rama para despliegue del API (`backend/`)
- `production-frontend`: rama para despliegue de la UI (`frontend/`)

## Archivos de despliegue

- Backend:
  - `backend/Dockerfile`
  - `backend/railway.json`
  - `backend/.env.railway.example`
- Frontend:
  - `frontend/Dockerfile`
  - `frontend/railway.json`
  - `frontend/.env.railway.example`

## Crear proyecto en Railway

1. Crear un proyecto nuevo en Railway.
2. Crear dos servicios:
   - Servicio `backend` (Root Directory: `backend`)
   - Servicio `frontend` (Root Directory: `frontend`)
3. Conectar ambos servicios al mismo repositorio.
4. Configurar branch por servicio:
   - `backend` -> `production-backend`
   - `frontend` -> `production-frontend`

## Variables de entorno

### Backend

Definir en el servicio backend:

- `API_PORT=8080`
- `JWT_SECRET_KEY`
- `JWT_ACCESS_TOKEN_HOURS=8`
- `JWT_REFRESH_TOKEN_DAYS=45`
- `CONNI_KEY`
- `CONNI_TOKEN`
- `DB_ENGINE=mysql`
- `MYSQL_HOST`
- `MYSQL_PORT=3306`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

### Frontend

Definir en el servicio frontend:

- `VITE_API_URL=https://<url-backend>.up.railway.app`
- `VITE_USE_SUBPATH=false`

## CI/CD GitHub Actions

Workflows incluidos:

- `.github/workflows/deploy_railway_backend.yml`
- `.github/workflows/deploy_railway_frontend.yml`

Secrets requeridos en GitHub:

- `RAILWAY_TOKEN`
- `RAILWAY_BACKEND_SERVICE`
- `RAILWAY_BACKEND_ENVIRONMENT`
- `RAILWAY_FRONTEND_SERVICE`
- `RAILWAY_FRONTEND_ENVIRONMENT`

Los workflows despliegan automáticamente al hacer push en:

- `production-backend`
- `production-frontend`
