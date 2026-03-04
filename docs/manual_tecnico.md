# Manual Técnico

## Stack
- Backend: Flask, SQLite, JWT
- Frontend: React + Vite
- Exportación: Excel y PDF

## Variables de Entorno
- JWT_SECRET_KEY
- DATA_ENCRYPTION_KEY
- DATA_HASH_SALT
- DB_PATH

## Esquema de Base de Datos
- facturas: repeticiones, sumatoria, registrable, valores restantes
- notas_credito: estados (PENDIENTE, APLICADA, NO_APLICADA), es_agente
- aplicaciones_notas: historial de aplicación con valores antes y después
- log_motivos_no_aplicacion: motivos y detalle
- audit_logs: cambios de entidades

## Seguridad
- Autenticación JWT
- Encriptación de NIT y nombres en reposo
- Auditoría de cambios

## Reglas de Negocio
- Monto mínimo registrable por factura: $524.000
- Código abc123: máximo 5 repeticiones, sumatoria > $524.000
- Notas crédito solo validan agente, sin reglas estándar
- Nota agente se aplica a factura correspondiente
- Si la nota deja la factura en cero, se elimina la línea

## Ejecución
- Backend: iniciar Flask con las variables de entorno configuradas
- Frontend: iniciar Vite con npm

## Pruebas
- Unitarias: reglas de negocio y aplicación de notas
- Integración: flujo de aplicación y reglas abc123

## Backup
- Workflow diario en GitHub Actions
- Script: backend/scripts/backup_database.py
