# Renovación del sistema CIPA

## Módulos

### Exportación
- Endpoint preview: `POST /api/admin/export-preview`
- Exportación: `POST /api/admin/exportar-excel` y `POST /api/admin/exportar-pdf`
- Parámetros: `fecha_desde`, `fecha_hasta`, `tipo`

### Facturas
- Endpoint listado: `GET /api/facturas`
- Filtros: `fecha_desde`, `fecha_hasta`, `estado`, `registrable`, `con_nota`, `numero_factura`, `nombre_cliente`, `search`, `orden`, `direccion`

### Notas pendientes
- Listado: `GET /api/notas/pendientes`
- CRUD: `POST /api/notas/pendientes`, `PUT /api/notas/pendientes/{id}`, `DELETE /api/notas/pendientes/{id}`
- Alertas: `GET /api/notas/pendientes/alertas`

### Aplicaciones
- Listado: `GET /api/aplicaciones-sistema`
- CRUD: `POST /api/aplicaciones-sistema`, `PUT /api/aplicaciones-sistema/{id}`, `DELETE /api/aplicaciones-sistema/{id}`
- Uso: `POST /api/aplicaciones-sistema/{id}/uso`

### Logs
- Listado: `GET /api/admin/logs`
- Filtros: `entidad`, `accion`, `usuario`, `fecha_desde`, `fecha_hasta`, `search`

### Autenticación y 2FA
- Setup: `POST /api/auth/2fa/setup`
- Enable: `POST /api/auth/2fa/enable`
- Disable: `POST /api/auth/2fa/disable`
- Status: `GET /api/auth/2fa/status`
- Login con OTP: enviar `otp` cuando el usuario tenga 2FA activo

## Variables de entorno MySQL
- `DB_ENGINE=mysql`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

## Migración
- SQLite → MySQL: `python backend/scripts/migrate_sqlite_to_mysql.py --sqlite-path backend/data/notas_credito.db --truncate`

## Seguridad
- Hash de contraseñas con bcrypt
- Tokens JWT con invalidación de sesiones
- 2FA TOTP con `pyotp`
