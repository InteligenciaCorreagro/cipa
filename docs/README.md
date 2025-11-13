# 📚 Documentación CIPA

Índice de documentación técnica del sistema CIPA.

## 📖 Guías de Usuario

### [GUIA_CONFIGURACION.md](./GUIA_CONFIGURACION.md)
**Configuración inicial del sistema**
- Unificación de base de datos
- Configuración de variables de entorno
- Estructura del proyecto
- Solución de problemas comunes

### [INSTRUCCIONES_POBLAR_BD.md](./INSTRUCCIONES_POBLAR_BD.md)
**Guía paso a paso para poblar la base de datos**
- Configuración del archivo `.env`
- Ejecución del script de población
- Verificación de datos
- Troubleshooting

## 🔧 Documentación Técnica

### [API_ENDPOINTS.md](./API_ENDPOINTS.md)
**Documentación completa de la API REST**
- Lista de todos los endpoints
- Parámetros y respuestas
- Ejemplos de uso con JavaScript/React
- Guía de paginación y filtros
- Manejo de errores

### [SOLUCION_ERROR_API.md](./SOLUCION_ERROR_API.md)
**Solución de errores comunes de la API SIESA**
- Error 400 Bad Request
- Problemas de formato de fechas
- Script de diagnóstico
- Comandos útiles

## 📁 Documentación en Raíz del Proyecto

Los siguientes documentos están en la raíz del proyecto:

- **[../README.md](../README.md)** - Introducción general del proyecto
- **[../DEPLOYMENT_RENDER.md](../DEPLOYMENT_RENDER.md)** - Guía de despliegue en Render
- **[../GODADDY_CONFIGURATION.md](../GODADDY_CONFIGURATION.md)** - Configuración de dominio GoDaddy
- **[../PROYECTO_ORGANIZADO.md](../PROYECTO_ORGANIZADO.md)** - Estructura del proyecto

## 🗂️ Estructura de Documentación

```
/home/user/cipa/
├── README.md                          # Introducción general
├── DEPLOYMENT_RENDER.md               # Deploy en Render
├── GODADDY_CONFIGURATION.md           # Config dominio
├── PROYECTO_ORGANIZADO.md             # Estructura proyecto
│
└── docs/                              # Documentación técnica
    ├── README.md                      # Este archivo (índice)
    ├── API_ENDPOINTS.md               # API REST
    ├── GUIA_CONFIGURACION.md          # Configuración
    ├── INSTRUCCIONES_POBLAR_BD.md     # Población de BD
    └── SOLUCION_ERROR_API.md          # Troubleshooting API
```

## 🚀 Inicio Rápido

1. **Primera vez instalando:** Lee [GUIA_CONFIGURACION.md](./GUIA_CONFIGURACION.md)
2. **Poblando base de datos:** Lee [INSTRUCCIONES_POBLAR_BD.md](./INSTRUCCIONES_POBLAR_BD.md)
3. **Usando la API:** Lee [API_ENDPOINTS.md](./API_ENDPOINTS.md)
4. **Problemas con API:** Lee [SOLUCION_ERROR_API.md](./SOLUCION_ERROR_API.md)

## 📝 Notas

- La documentación técnica detallada está en `docs/`
- La documentación de deployment está en la raíz
- Para contribuir, consulta el [README principal](../README.md)
