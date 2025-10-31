# CIPA Frontend - Sistema de Gestión de Notas de Crédito

Frontend profesional y minimalista para el sistema de gestión de notas de crédito CIPA.

## Tecnologías Utilizadas

- **React 18** - Biblioteca de UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool ultra-rápido
- **Tailwind CSS** - Framework CSS utility-first
- **Shadcn/ui** - Componentes UI accesibles y personalizables
- **React Router** - Navegación SPA
- **TanStack Query (React Query)** - Gestión de estado del servidor
- **Zustand** - Gestión de estado global
- **Axios** - Cliente HTTP
- **Recharts** - Visualización de datos

## Características Principales

### Autenticación
- Login con JWT (Access + Refresh tokens)
- Protección de rutas
- Auto-refresh de tokens
- Persistencia de sesión

### Dashboard
- Estadísticas en tiempo real
- Gráficos de distribución (Pie Chart)
- Gráficos de valores por estado (Bar Chart)
- Tarjetas de resumen con iconos

### Gestión de Notas de Crédito
- Listado paginado con filtros
- Búsqueda por NIT de cliente
- Filtros por estado (Pendiente, Parcial, Aplicada)
- Vista detallada de cada nota
- Historial completo de aplicaciones

### Diseño
- Interfaz minimalista y profesional
- Sidebar colapsable
- Responsive design
- Dark mode support (configurado)
- Animaciones suaves

## Instalación

### Requisitos Previos
- Node.js 18+
- npm o yarn

### Pasos de Instalación

1. **Clonar el repositorio y navegar al frontend:**
```bash
cd cipa/frontend
```

2. **Instalar dependencias:**
```bash
npm install
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
```

Editar `.env` y configurar la URL de la API:
```env
VITE_API_URL=http://localhost:5000
```

4. **Iniciar el servidor de desarrollo:**
```bash
npm run dev
```

El frontend estará disponible en: `http://localhost:3000`

## Scripts Disponibles

```bash
# Desarrollo
npm run dev          # Iniciar servidor de desarrollo

# Producción
npm run build        # Compilar para producción
npm run preview      # Vista previa de build de producción

# Calidad de código
npm run lint         # Ejecutar ESLint
```

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/        # Componentes reutilizables
│   │   ├── ui/           # Componentes UI base (Shadcn)
│   │   └── ProtectedRoute.tsx
│   ├── layouts/          # Layouts de página
│   │   └── MainLayout.tsx
│   ├── pages/            # Páginas/vistas
│   │   ├── DashboardPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── NotasPage.tsx
│   │   └── NotaDetailPage.tsx
│   ├── services/         # Servicios API
│   │   └── api.ts
│   ├── store/            # Estado global (Zustand)
│   │   └── authStore.ts
│   ├── hooks/            # Custom hooks
│   │   └── useNotas.ts
│   ├── types/            # Tipos TypeScript
│   │   └── index.ts
│   ├── lib/              # Utilidades
│   │   └── utils.ts
│   ├── App.tsx           # Componente principal
│   ├── main.tsx          # Punto de entrada
│   └── index.css         # Estilos globales
├── public/               # Archivos estáticos
├── .env                  # Variables de entorno
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Uso

### Login
1. Abrir `http://localhost:3000/login`
2. Usar credenciales por defecto:
   - **Usuario:** `admin`
   - **Contraseña:** `admin123`

### Dashboard
- Vista general con estadísticas
- Gráficos de distribución y valores
- Navegación rápida a módulos

### Notas de Crédito
- **Listado:** Ver todas las notas con paginación
- **Filtros:** Por estado o NIT de cliente
- **Detalles:** Click en el icono de ojo para ver detalles
- **Historial:** Ver aplicaciones realizadas a cada nota

## Integración con el Backend

El frontend se conecta a la API REST en `http://localhost:5000` (configurable en `.env`).

### Endpoints Utilizados
- `POST /api/auth/login` - Autenticación
- `POST /api/auth/logout` - Cerrar sesión
- `POST /api/auth/refresh` - Refrescar token
- `GET /api/notas` - Listar notas
- `GET /api/notas/:id` - Detalles de nota
- `GET /api/notas/estadisticas` - Estadísticas
- `GET /api/notas/por-estado` - Distribución por estado
- `GET /api/aplicaciones/:numero_nota` - Historial de aplicaciones

### Configuración de Proxy
Vite está configurado con un proxy para desarrollo:
- Todas las peticiones a `/api/*` se redirigen a `http://localhost:5000`

## Build para Producción

### Compilar
```bash
npm run build
```

Los archivos optimizados se generan en el directorio `dist/`.

### Servir Build Local
```bash
npm run preview
```

### Deploy
Los archivos en `dist/` pueden ser servidos por cualquier servidor web estático:
- **Nginx**
- **Apache**
- **Vercel**
- **Netlify**
- **GitHub Pages**
- **AWS S3 + CloudFront**

#### Ejemplo de configuración Nginx:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Personalización

### Colores y Tema
Los colores se definen en `src/index.css` usando variables CSS:
```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96.1%;
  /* ... */
}
```

### Componentes UI
Los componentes en `src/components/ui/` son personalizables:
- Editar directamente los componentes
- Agregar nuevas variantes
- Modificar estilos con Tailwind classes

### Agregar Nuevas Páginas
1. Crear componente en `src/pages/`
2. Agregar ruta en `src/App.tsx`
3. Agregar en el menú en `src/layouts/MainLayout.tsx`

## Buenas Prácticas Implementadas

✅ **TypeScript estricto** - Tipos completos en todo el código
✅ **Componentes reutilizables** - UI components modulares
✅ **Manejo de errores** - Error boundaries y estados de error
✅ **Loading states** - Indicadores de carga en peticiones
✅ **Optimización** - Code splitting y lazy loading
✅ **Accesibilidad** - Componentes accesibles (a11y)
✅ **Responsive** - Mobile-first design
✅ **Seguridad** - JWT con refresh tokens
✅ **Cache inteligente** - React Query con stale time
✅ **Clean code** - Código limpio y mantenible

## Solución de Problemas

### El frontend no se conecta al backend
1. Verificar que el backend esté corriendo en `http://localhost:5000`
2. Revisar la variable `VITE_API_URL` en `.env`
3. Verificar la consola del navegador para errores de CORS

### Errores de autenticación
1. Limpiar localStorage: `localStorage.clear()`
2. Recargar la página
3. Intentar login nuevamente

### Build falla
1. Limpiar node_modules: `rm -rf node_modules package-lock.json`
2. Reinstalar: `npm install`
3. Intentar build: `npm run build`

---

**Desarrollado con las mejores prácticas de desarrollo web moderno**
