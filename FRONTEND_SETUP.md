# Frontend - Guía de Configuración y Ejecución

## Problema Resuelto

El frontend estaba apareciendo vacío debido a:
1. **Configuración de proxy incorrecta**: El proxy de Vite apuntaba al puerto 5000 pero el backend corre en el puerto 2500
2. **Variables de entorno no configuradas**: Faltaba el archivo `.env.development`

## Cambios Realizados

### 1. Configuración del Frontend

- **vite.config.ts**: Actualizado el proxy para apuntar a `http://localhost:2500`
- **.env.development**: Creado con `VITE_API_URL=http://localhost:2500`
- **.env.example**: Actualizado con el puerto correcto

### 2. Nueva Funcionalidad: Procesar Rango de Fechas

Se implementó una nueva página de administrador que permite:
- Seleccionar un rango de fechas (hasta 90 días)
- Procesar facturas de múltiples días
- Generar un Excel consolidado
- Descargar el archivo generado

#### Archivos agregados:
- `frontend/src/pages/AdminProcesarRangoPage.tsx` - Interfaz de usuario
- Rutas actualizadas en `App.tsx`
- Navegación actualizada en `MainLayout.tsx`

## Cómo Ejecutar el Frontend

### Opción 1: Modo Desarrollo (Recomendado)

1. **Instalar dependencias** (solo la primera vez):
   ```bash
   cd frontend
   npm install
   ```

2. **Verificar que el backend esté corriendo**:
   ```bash
   cd backend
   python api/app.py
   ```
   El backend debe estar corriendo en http://localhost:2500

3. **Ejecutar el frontend en modo desarrollo**:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Abrir en el navegador**:
   - URL: http://localhost:3000
   - Usuario por defecto: admin
   - Contraseña: (consultar con el equipo)

### Opción 2: Modo Producción (Build)

1. **Construir el frontend**:
   ```bash
   cd frontend
   npm run build
   ```
   Esto genera los archivos en `frontend/dist/`

2. **Servir los archivos estáticos**:
   - Opción A: Usar un servidor web (nginx, apache, etc.)
   - Opción B: Usar `serve`:
     ```bash
     npx serve -s dist -l 3000
     ```

## Características del Frontend

### Tecnologías Utilizadas
- **Vite 7**: Build tool ultra-rápido
- **React 19**: Framework UI
- **TypeScript**: Type safety
- **Tailwind CSS**: Estilos
- **Shadcn/ui**: Componentes de UI
- **React Router**: Navegación
- **TanStack React Query**: Gestión de estado del servidor
- **Zustand**: Gestión de estado global
- **Axios**: Cliente HTTP

### Páginas Disponibles

1. **Dashboard** (`/`) - Vista general con estadísticas
2. **Consulta de Notas** (`/notas`) - Buscar y filtrar notas de crédito
3. **Reporte Operativo** (`/reporte-operativo`) - Reportes operativos
4. **Procesar Rango de Fechas** (`/admin/procesar-rango`) - **NUEVO** - Solo admin
5. **Gestión de Usuarios** (`/usuarios`) - Solo admin

### Funcionalidad de Rango de Fechas

La nueva funcionalidad permite a los administradores:

1. **Seleccionar Fechas**:
   - Fecha desde y fecha hasta
   - Máximo 90 días de rango

2. **Procesar**:
   - El sistema procesa cada día en el rango
   - Obtiene facturas de la API de SIESA
   - Aplica reglas de negocio
   - Registra en la base de datos
   - Aplica notas de crédito pendientes

3. **Descargar**:
   - Genera un Excel consolidado
   - Botón de descarga directa

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/     # Componentes reutilizables
│   ├── layouts/        # Layouts de página
│   ├── pages/          # Páginas de la aplicación
│   │   ├── AdminProcesarRangoPage.tsx  # NUEVO
│   │   ├── DashboardPage.tsx
│   │   ├── NotasPage.tsx
│   │   └── ...
│   ├── services/       # Servicios (API client)
│   ├── store/          # Estado global (Zustand)
│   ├── types/          # Tipos TypeScript
│   └── hooks/          # Custom hooks
├── .env.development    # Variables de entorno (desarrollo) - NUEVO
├── .env.example        # Ejemplo de variables
├── vite.config.ts      # Configuración de Vite - ACTUALIZADO
└── package.json        # Dependencias
```

## Solución de Problemas

### Frontend aparece en blanco

1. **Verificar que el backend esté corriendo**:
   ```bash
   curl http://localhost:2500/api/health
   ```
   Debe retornar: `{"status": "healthy", ...}`

2. **Verificar las variables de entorno**:
   - Archivo `.env.development` debe existir
   - Debe contener: `VITE_API_URL=http://localhost:2500`

3. **Verificar la consola del navegador**:
   - Abrir DevTools (F12)
   - Ver si hay errores de red o JavaScript

### Error de CORS

Si ves errores de CORS, verifica:
1. El backend tiene CORS habilitado en `api/app.py`
2. El proxy de Vite está configurado correctamente en `vite.config.ts`

### Error 401 (No autorizado)

1. Limpiar localStorage:
   ```javascript
   // En la consola del navegador:
   localStorage.clear()
   ```
2. Volver a hacer login

## Próximos Pasos

Para mejorar la funcionalidad de rango de fechas:

1. **Consolidación de Excels**: Actualmente genera un Excel por día. Se puede mejorar para consolidar todos en un solo archivo.

2. **Barra de progreso**: Mostrar el progreso del procesamiento día por día.

3. **Notificaciones**: Enviar email cuando termine el procesamiento.

4. **Historial**: Guardar un historial de procesamientos realizados.

## Contacto y Soporte

Para problemas o dudas, contactar al equipo de desarrollo.
