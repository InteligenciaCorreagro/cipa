# 🚀 GUÍA RÁPIDA DE IMPLEMENTACIÓN

## Sistema de Gestión de Facturas con Notas Crédito

**Versión**: 2.0  
**Fecha**: Octubre 2025

---

## 📦 CONTENIDO DEL PAQUETE

Este paquete incluye la implementación completa de las tres reglas de negocio solicitadas:

### ✅ Reglas Implementadas

1. **Filtrado por Tipo de Inventario**: 25 tipos excluidos
2. **Validación de Monto Mínimo**: $498,000 COP
3. **Gestión Completa de Notas Crédito**:
   - Identificación automática (prefijo 'N')
   - Persistencia en SQLite (sin costo)
   - Aplicación automática a facturas (mismo cliente + producto)
   - Validación de montos y cantidades
   - Historial completo de aplicaciones

---

## ⚡ INICIO RÁPIDO (5 MINUTOS)

### Paso 1: Configuración Inicial

```bash
# 1. Copiar archivo de configuración
cp .env.example .env

# 2. Editar .env con tus credenciales
nano .env   # o usar cualquier editor

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar pruebas
python test_sistema.py
```

### Paso 2: Primera Ejecución

```bash
# Ejecutar proceso principal
python main.py

# Si todo funciona, verás:
# - Facturas filtradas por reglas de negocio
# - Notas crédito identificadas y guardadas
# - Excel generado en ./output/
# - Correo enviado
```

### Paso 3: Verificar Resultados

```bash
# Ver estado de notas crédito
python consultar_notas.py

# O modo comando específico
python consultar_notas.py resumen
python consultar_notas.py pendientes
```

---

## 📊 ESTRUCTURA DE ARCHIVOS

```
cipa_sistema_actualizado/
├── main.py                          # ⭐ PROCESO PRINCIPAL
├── requirements.txt                 # Dependencias
├── .env.example                     # Plantilla de configuración
│
├── src/                             # Módulos del sistema
│   ├── api_client.py                # Cliente API SIESA
│   ├── business_rules.py            # ⭐ REGLAS DE NEGOCIO
│   ├── notas_credito_manager.py     # ⭐ GESTIÓN NOTAS CRÉDITO
│   ├── excel_processor.py           # Procesamiento Excel
│   └── email_sender.py              # Envío de correos
│
├── consultar_notas.py               # ⭐ HERRAMIENTA DE CONSULTA
├── test_sistema.py                  # Tests unitarios
│
├── data/                            # Base de datos SQLite
│   └── notas_credito.db             # (se crea automáticamente)
│
├── output/                          # Archivos generados
│   ├── facturas_YYYYMMDD.xlsx
│   ├── facturas_rechazadas_YYYYMMDD.txt
│   └── reporte_notas_credito_YYYYMMDD.txt
│
├── .github/workflows/               # GitHub Actions
│   └── daily_report.yml             # Ejecución automática
│
└── README.md                        # Documentación completa
```

---

## 🔧 CONFIGURACIÓN REQUERIDA

### Variables de Entorno (.env)

```env
# API SIESA (OBLIGATORIO)
CONNI_KEY=tu_key_aqui
CONNI_TOKEN=tu_token_aqui

# Email (OBLIGATORIO)
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_password_de_app
DESTINATARIOS=email1@company.com,email2@company.com

# Opcional (valores por defecto)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
DB_PATH=./data/notas_credito.db
```

⚠️ **IMPORTANTE para Gmail**: Usa "Contraseñas de Aplicación", no tu contraseña principal
👉 https://support.google.com/accounts/answer/185833

---

## 📋 REGLAS DE NEGOCIO - DETALLE

### 1. Tipos de Inventario Excluidos

```
VSMENORCC    VS4205101    INVMEDICAD   INV1430051
VS42100501   VS420515     VS42051003   VS420510
VSMENOR      INVFLETEPT   VSMENOR5%    VS42505090
INVFLETGEN   INV144542    INV144554    VSMAY-MECC
VSMAY-MECP   VSMAY-GEN    DESCESPEC    DESCUENTO
INV144562    VS425050     VS41200822   INV1460
VS41200819
```

**Ubicación**: `src/business_rules.py` línea 16

### 2. Monto Mínimo

- **Valor**: $498,000 COP
- Facturas con valor inferior son **rechazadas**
- Se genera reporte de rechazos: `facturas_rechazadas_YYYYMMDD.txt`

**Ubicación**: `src/business_rules.py` línea 47

### 3. Notas Crédito

**Lógica de Aplicación**:
```python
# Condiciones para aplicar nota a factura:
1. Cliente debe coincidir (NIT)
2. Producto debe coincidir (código)
3. Valor aplicado ≤ Valor factura
4. Cantidad aplicada ≤ Cantidad factura
5. Nota tiene saldo pendiente > 0

# Si no se puede aplicar hoy:
- Queda en BD como PENDIENTE
- Se intentará aplicar en siguientes ejecuciones
```

**Base de Datos**: `data/notas_credito.db` (SQLite, sin costo)

---

## 🔍 CONSULTAR ESTADO DE NOTAS

### Modo Interactivo

```bash
python consultar_notas.py
```

Menú con opciones:
1. Ver notas pendientes
2. Ver aplicaciones recientes
3. Consultar nota específica
4. Resumen general

### Modo Comando

```bash
# Resumen general
python consultar_notas.py resumen

# Listar pendientes
python consultar_notas.py pendientes

# Aplicaciones últimos 7 días
python consultar_notas.py aplicaciones 7

# Historial de nota específica
python consultar_notas.py nota N001234
```

---

## 🧪 PRUEBAS

### Ejecutar Suite Completa

```bash
python test_sistema.py
```

**Valida**:
- ✅ Identificación de notas crédito
- ✅ Filtrado de tipos de inventario
- ✅ Validación de monto mínimo
- ✅ Registro y aplicación de notas
- ✅ Transformaciones de Excel
- ✅ Base de datos SQLite

### Pruebas Manuales

```bash
# 1. Verificar que se crean los directorios
ls -la data/ output/

# 2. Verificar que existe la BD después de ejecutar
ls -lh data/notas_credito.db

# 3. Ver contenido de la BD
sqlite3 data/notas_credito.db "SELECT COUNT(*) FROM notas_credito;"
sqlite3 data/notas_credito.db "SELECT COUNT(*) FROM aplicaciones_notas;"
```

---

## 🚀 DESPLIEGUE EN GITHUB ACTIONS

### 1. Subir Código a GitHub

```bash
git init
git add .
git commit -m "Sistema de gestión de facturas v2.0"
git remote add origin <tu-repo>
git push -u origin main
```

### 2. Configurar Secrets

1. Ir a: **Settings** → **Secrets and variables** → **Actions**
2. Click en **New repository secret**
3. Agregar cada variable:
   - `CONNI_KEY`
   - `CONNI_TOKEN`
   - `EMAIL_USERNAME`
   - `EMAIL_PASSWORD`
   - `SMTP_SERVER` (opcional: smtp.gmail.com)
   - `SMTP_PORT` (opcional: 587)
   - `DESTINATARIOS`

### 3. Verificar Workflow

- Ir a tab **Actions**
- Esperar ejecución automática (1:00 PM UTC = 8:00 AM Bogotá)
- O ejecutar manualmente: **Run workflow**

---

## 📊 SALIDAS GENERADAS

### 1. Excel de Facturas Válidas
**Archivo**: `output/facturas_YYYYMMDD.xlsx`
- Facturas que pasaron todas las validaciones
- Con aplicaciones de notas crédito reflejadas
- Listo para carga en sistema

### 2. Reporte de Rechazos
**Archivo**: `output/facturas_rechazadas_YYYYMMDD.txt`
```
Factura: F123456
Cliente: Cliente Test
Razón: Tipo de inventario excluido: VSMENOR
Valor: $600,000.00
```

### 3. Reporte de Notas Crédito
**Archivo**: `output/reporte_notas_credito_YYYYMMDD.txt`
```
RESUMEN:
- Notas pendientes: 5
- Saldo pendiente: $2,500,000.00
- Aplicaciones hoy: 3

APLICACIONES:
Nota N001234 -> Factura F005678
  Valor: $800,000.00
  Estado: APLICADA
```

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "Faltan variables de entorno"
```bash
# Verificar .env existe
ls -la .env

# Verificar contenido
cat .env | grep -v "^#"
```

### Error: "No se puede conectar a la API"
```bash
# Verificar credenciales
echo $CONNI_KEY
echo $CONNI_TOKEN

# Probar conectividad
curl -I https://siesaprod.cipa.com.co
```

### Error: "No se puede enviar email"
```bash
# Para Gmail, verificar:
# 1. Verificación en dos pasos activada
# 2. Contraseña de aplicación generada
# 3. No usar contraseña principal

# Probar SMTP manualmente
python -c "import smtplib; s=smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); print('OK')"
```

### Base de datos corrupta
```bash
# Hacer respaldo
cp data/notas_credito.db data/backup_$(date +%Y%m%d).db

# Verificar integridad
sqlite3 data/notas_credito.db "PRAGMA integrity_check;"

# Si está corrupta, eliminar (perderá historial)
rm data/notas_credito.db
# Se recreará en próxima ejecución
```

---

## 📈 MONITOREO Y MANTENIMIENTO

### Ver Logs en GitHub Actions
1. Ir a tab **Actions**
2. Seleccionar ejecución
3. Click en job "generar-reporte"
4. Ver logs detallados

### Consultas Útiles a la BD

```bash
# Abrir BD
sqlite3 data/notas_credito.db

# Consultas útiles:
sqlite> SELECT COUNT(*) FROM notas_credito WHERE estado='PENDIENTE';
sqlite> SELECT SUM(saldo_pendiente) FROM notas_credito WHERE estado='PENDIENTE';
sqlite> SELECT COUNT(*) FROM aplicaciones_notas;
sqlite> SELECT SUM(valor_aplicado) FROM aplicaciones_notas;

# Ver últimas 5 notas registradas
sqlite> SELECT numero_nota, fecha_nota, saldo_pendiente, estado 
        FROM notas_credito ORDER BY fecha_registro DESC LIMIT 5;

# Ver últimas 5 aplicaciones
sqlite> SELECT numero_nota, numero_factura, valor_aplicado, fecha_aplicacion
        FROM aplicaciones_notas ORDER BY fecha_aplicacion DESC LIMIT 5;
```

### Limpieza Periódica

```bash
# Respaldo mensual
0 0 1 * * cp /path/to/data/notas_credito.db /path/to/backup/notas_$(date +\%Y\%m).db

# Limpiar outputs antiguos (más de 30 días)
find output/ -name "*.xlsx" -mtime +30 -delete
find output/ -name "*.txt" -mtime +30 -delete
```

---

## 📞 SOPORTE

### Documentación Completa
Ver `README.md` para documentación exhaustiva de:
- Arquitectura del sistema
- Flujos de procesamiento
- Ejemplos de código
- Diagramas

### Modificar Reglas de Negocio

**Agregar tipo de inventario excluido**:
```python
# Editar: src/business_rules.py línea 16
TIPOS_INVENTARIO_EXCLUIDOS = {
    'VSMENOR',
    'VS4205101',
    # ... tipos existentes ...
    'NUEVO_TIPO'  # Agregar aquí
}
```

**Cambiar monto mínimo**:
```python
# Editar: src/business_rules.py línea 47
MONTO_MINIMO = 600000.0  # Nuevo valor
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Pre-Despliegue
- [ ] Credenciales API configuradas
- [ ] Credenciales email configuradas
- [ ] Destinatarios verificados
- [ ] Tests ejecutados exitosamente
- [ ] Prueba manual local exitosa
- [ ] Base de datos creada

### Despliegue
- [ ] Código subido a GitHub
- [ ] Secrets configurados
- [ ] Workflow habilitado
- [ ] Primera ejecución manual exitosa
- [ ] Archivos generados correctamente
- [ ] Emails recibidos

### Post-Despliegue
- [ ] Monitorear primera ejecución automática
- [ ] Verificar logs sin errores
- [ ] Validar facturas procesadas correctamente
- [ ] Confirmar notas crédito registradas
- [ ] Documentar casos especiales
- [ ] Verificar backups semanales funcionando
- [ ] Confirmar reportes diarios llegando

---

## 🆕 NUEVAS FUNCIONALIDADES

### 1. Registro de Facturas Rechazadas en BD

Todas las facturas rechazadas se guardan en la base de datos para:
- **Auditoría completa** de qué se está rechazando
- **Detección automática** de nuevos tipos de inventario
- **Alertas** cuando aparecen tipos nuevos que deberían agregarse a la lista de excluidos

**Tablas en BD:**
- `facturas_rechazadas` - Historial completo de rechazos
- `tipos_inventario_detectados` - Todos los tipos de inventario vistos

**Consultas útiles:**
```bash
# Ver tipos de inventario nuevos detectados
sqlite3 data/notas_credito.db "SELECT * FROM tipos_inventario_detectados WHERE es_excluido=0 ORDER BY primera_deteccion DESC;"

# Ver facturas rechazadas últimos 7 días
sqlite3 data/notas_credito.db "SELECT numero_factura, tipo_inventario, valor_total, razon_rechazo FROM facturas_rechazadas WHERE fecha_registro >= date('now', '-7 days');"
```

### 2. Reporte Diario desde Base de Datos

**Script:** `reporte_diario.py`

Genera y envía reporte HTML consultando solo la BD (sin procesar facturas):
- Estado de notas crédito pendientes
- Facturas rechazadas últimos 7 días
- **⚠️ ALERTA de tipos de inventario nuevos**
- Estadísticas completas

**Uso manual:**
```bash
python reporte_diario.py
```

**Ejecución automática:**
- GitHub Actions lo ejecuta diariamente a las 9:00 AM (Bogotá)
- Workflow: `.github/workflows/reporte_diario.yml`

### 3. Backups Automáticos Semanales

**Script:** `backup_database.py`

**Características:**
- Backups comprimidos con gzip (ahorro ~70% espacio)
- Limpieza automática de backups antiguos
- Retención configurable (default 90 días)
- Backups almacenados en GitHub Artifacts

**Uso manual:**
```bash
# Crear backup
python backup_database.py crear

# Crear backup sin comprimir
python backup_database.py crear --no-comprimir

# Listar backups disponibles
python backup_database.py listar

# Limpiar backups antiguos (mantener últimos 30 días)
python backup_database.py limpiar --dias 30

# Restaurar desde backup
python backup_database.py restaurar --backup ./backups/notas_credito_backup_20251027_120000.db.gz
```

**Ejecución automática:**
- GitHub Actions ejecuta backups todos los **domingos a las 9:00 PM** (Bogotá)
- Workflow: `.github/workflows/backup_semanal.yml`
- Descarga: Actions → Artifacts → `backups-semanales`

---

## 🎯 PRÓXIMOS PASOS SUGERIDOS

1. **Optimización**: Agregar índices adicionales en BD si crece mucho
2. **Alertas**: Implementar notificaciones cuando notas no se pueden aplicar
3. **Dashboard**: Crear visualización web del estado de notas crédito
4. **Auditoría**: Implementar logs más detallados de cambios
5. **Reporting**: Añadir reportes semanales/mensuales automáticos
6. ~~**BD de Rechazos**: Guardar facturas rechazadas para análisis~~ ✅ **IMPLEMENTADO**
7. ~~**Backups**: Sistema de respaldo automático~~ ✅ **IMPLEMENTADO**

---

## 📊 WORKFLOWS DE GITHUB ACTIONS

El sistema ahora tiene 3 workflows automáticos:

### 1. Reporte Diario de Facturas (8:00 AM)
- Procesa facturas desde API SIESA
- Aplica reglas de negocio
- Gestiona notas crédito
- Envía Excel por email
- **Workflow:** `daily_report.yml`

### 2. Reporte Diario desde BD (9:00 AM)
- Consulta estado del sistema
- Alerta de tipos de inventario nuevos
- Envía reporte HTML por email
- **Workflow:** `reporte_diario.yml`

### 3. Backup Semanal (Domingos 9:00 PM)
- Crea backup comprimido de la BD
- Limpia backups antiguos
- Guarda en GitHub Artifacts (90 días)
- **Workflow:** `backup_semanal.yml`

---

**¡Sistema listo para producción!** 🚀

---

*Última actualización: Octubre 2025*
*Versión: 2.0*
*Desarrollado para: COMPAÑÍA INDUSTRIAL DE PRODUCTOS AGROPECUARIOS S.A.*
