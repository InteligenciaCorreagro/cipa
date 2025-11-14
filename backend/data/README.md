# ⚠️ NO USAR ESTE DIRECTORIO

## Base de Datos Consolidada

**La base de datos del proyecto está en:**
```
/data/notas_credito.db
```

Este directorio `backend/data/` **NO SE DEBE USAR**.

## Configuración

Todos los componentes deben usar la variable de entorno:
```env
DB_PATH=./data/notas_credito.db
```

O si no está definida, usar la ruta relativa desde la raíz del proyecto:
```python
# Desde backend/api/app.py o backend/main.py
DB_PATH = os.getenv('DB_PATH', './data/notas_credito.db')
```

## Estructura del Proyecto

```
cipa/
├── data/
│   └── notas_credito.db        ← USAR ESTA BASE DE DATOS
├── backend/
│   ├── data/
│   │   └── README.md           ← ESTE ARCHIVO
│   ├── api/
│   │   └── app.py             ← API usa DB_PATH=./data/notas_credito.db
│   ├── core/
│   │   └── notas_credito_manager.py
│   └── main.py                ← Proceso diario usa DB_PATH=./data/notas_credito.db
└── scripts/
    └── populate_historical_data.py  ← Scripts usan DB_PATH=./data/notas_credito.db
```

## ¿Por qué?

1. **Una sola fuente de verdad:** Todos los componentes comparten la misma base de datos
2. **Evita inconsistencias:** No hay duplicación de datos
3. **Facilita el versionado:** Solo una BD en Git
4. **Simplifica backups:** Un solo archivo para respaldar
5. **Compatible con GitHub Actions:** La BD se actualiza y versiona automáticamente

## Si encuentras una BD aquí

Significa que algo está mal configurado. Verifica que todas las variables de entorno apunten a `./data/notas_credito.db`.
