# ARQUITECTURA DEL SISTEMA CIPA - Análisis Detallado

## 1. VISIÓN GENERAL

CIPA es un sistema completo de gestión de notas de crédito con automatización diaria que:
- Consulta la API SIESA para obtener facturas y notas crédito
- Valida datos contra reglas de negocio específicas
- Aplica automáticamente notas crédito a facturas
- Genera reportes Excel y envía por correo diarios
- Proporciona API REST con interfaz web para consultas

**Stack Tecnológico:**
- Backend: Python 3.11 + Flask
- Frontend: React 18 + TypeScript + Vite
- Base de Datos: SQLite (notas_credito.db)
- Automatización: GitHub Actions (ejecuta diariamente)
- Autenticación: JWT con bcrypt

---

## 2. AUTOMATIZACIÓN Y WORKFLOWS

### 2.1 Proceso Diario (daily_process.yml)
**Ejecuta:** Todos los días a las 1:00 PM UTC (8:00 AM Bogotá)
**Trigger Manual:** Disponible en GitHub Actions

**Flujo de Ejecución:**
```
1. Setup (Checkout, Python 3.11, Dependencias)
   ↓
2. Verificación BD Existente
   - Crea backup si existe
   - Muestra estadísticas ANTES del proceso
   ↓
3. Ejecutar main.py
   - Obtiene facturas de API SIESA
   - Aplica reglas de negocio
   - Registra/aplica notas crédito
   - Genera reportes Excel y TXT
   ↓
4. Estadísticas POST-PROCESO
   - Muestra cambios en BD
   - Lista aplicaciones del día
   ↓
5. Persistencia en Repositorio
   - Commit automático de la BD actualizada
   - Mensaje con estadísticas diarias
   ↓
6. Artifacts
   - Subida de reportes Excel (30 días)
   - Subida de reportes TXT (30 días)
   - Backup BD (7 días)
```

**Secretos Requeridos:**
- CONNI_KEY, CONNI_TOKEN (API SIESA)
- EMAIL_USERNAME, EMAIL_PASSWORD (SMTP)
- SMTP_SERVER, SMTP_PORT
- DESTINATARIOS (correos separados por coma)

### 2.2 Backup Semanal (backup_semanal.yml)
**Ejecuta:** Domingos a las 2:00 AM UTC (9:00 PM sábado Bogotá)

---

## 3. SISTEMA DE POBLACIÓN DE BASE DE DATOS

### 3.1 Arquitectura de Datos
La BD es el corazón del sistema, almacenada en **SQLite** y versionada en Git:
- **Ubicación:** `/home/user/cipa/data/notas_credito.db` (749KB)
- **Persistencia:** Commitida a repo después de cada proceso diario

### 3.2 Tablas Principales

#### NOTAS_CREDITO
Almacena todas las notas de crédito recibidas:
```
- id, numero_nota, fecha_nota
- nit_cliente, nombre_cliente
- codigo_producto, nombre_producto
- tipo_inventario
- valor_total, cantidad
- saldo_pendiente, cantidad_pendiente (se actualiza con aplicaciones)
- causal_devolucion
- estado (PENDIENTE | APLICADA)
- fecha_registro, fecha_aplicacion_completa
- UNIQUE(numero_nota, codigo_producto)
```

#### APLICACIONES_NOTAS
Historial de cada aplicación de nota a factura:
```
- id, id_nota, numero_nota
- numero_factura, fecha_factura
- nit_cliente, codigo_producto
- valor_aplicado, cantidad_aplicada
- fecha_aplicacion (timestamp automático)
```

#### FACTURAS_RECHAZADAS (Auditoría)
Todas las facturas rechazadas con razón:
```
- Actualmente: 2,955 registros
- Razones: Tipo inventario excluido, Monto mínimo, etc.
```

#### TIPOS_INVENTARIO_DETECTADOS
Tipos de inventario descubiertos en facturas:
```
- codigo_tipo (UNIQUE)
- descripcion, es_excluido
- primera_deteccion, ultima_deteccion
- total_facturas (contador)
```

#### USUARIOS (Autenticación)
```
- username, password_hash (bcrypt)
- email, rol (admin|editor|viewer)
- activo, intentos_fallidos, bloqueado_hasta
- fecha_creacion, fecha_modificacion, ultimo_acceso
```

#### SESIONES (Tracking JWT)
```
- user_id, token_jti, refresh_jti
- ip_address, user_agent
- fecha_creacion, fecha_expiracion, activa
```

#### INTENTOS_LOGIN (Auditoría)
```
- username, ip_address
- exitoso, razon_fallo, fecha
```

---

## 4. SCRIPTS DE POBLACIÓN Y AUTOMATIZACIÓN

### 4.1 Script Principal: main.py
**Flujo Detallado:**

```
PASO 1: OBTENER FACTURAS DE API
├─ Consulta: Api_Consulta_Fac_Correagro
├─ Parámetros: FECHA_INI='YYYY-MM-DD'|FECHA_FIN='YYYY-MM-DD'
└─ Resultado: Lista de líneas de facturas desde SIESA

PASO 2: APLICAR REGLAS DE NEGOCIO (BusinessRulesValidator)
├─ Separar notas crédito (prefijo 'N')
├─ Validar tipos de inventario
│  └─ 23 tipos excluidos (VSMENORCC, INVMEDICAD, etc.)
├─ Validar monto mínimo ($498,000 COP)
├─ Agrupar líneas por factura
└─ Resultado: 
   ├─ facturas_validas
   ├─ notas_credito
   └─ facturas_rechazadas

PASO 3: REGISTRAR NOTAS CRÉDITO EN BD (NotasCreditoManager)
├─ Verificar duplicados (UNIQUE: numero_nota + codigo_producto)
├─ Registrar tipos de inventario detectados
└─ Resultado: Notas disponibles para aplicación

PASO 4: APLICAR NOTAS A FACTURAS
├─ Para cada factura válida:
│  ├─ Buscar notas pendientes del MISMO cliente + MISMO producto
│  ├─ Aplicar monto menor entre (saldo_nota, valor_factura)
│  ├─ Actualizar saldo y estado
│  └─ Registrar aplicación en aplicaciones_notas
└─ Resultado: aplicaciones realizadas

PASO 5: GENERAR REPORTES
├─ Excel: facturas_{YYYYMMDD}.xlsx
├─ Txt: facturas_rechazadas_{YYYYMMDD}.txt
├─ Txt: reporte_notas_credito_{YYYYMMDD}.txt
└─ Con estadísticas completas

PASO 6: ENVIAR CORREO (EmailSender)
└─ A destinatarios configurados con archivo Excel adjunto
```

### 4.2 Script de Exportación Personalizada
**Archivo:** `backend/export_operativa_custom.py`

Permite generar reportes con rango de fechas customizado:
```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-11-01 \
  --fecha-fin 2025-11-13 \
  --enviar-correo \
  --output-dir ./output
```

**Diferencia con main.py:**
- NO registra notas nuevas en BD (modo lectura)
- Usa rango de fechas customizado
- Opcional: envía correo

### 4.3 Scripts de Utilidad Disponibles
```
backend/scripts/
├─ backup_database.py          # Backup manual de BD
├─ consultar_notas.py          # Consulta notas con filtros
├─ limpiar_notas_invalidas.py  # Limpieza de datos
├─ reporte_diario.py           # Generar reportes manuales
├─ verificar_config.py         # Validar configuración
├─ inicializar_auth.py         # Setup inicial usuario admin
├─ test_api_connection.py      # Prueba conectividad SIESA
└─ migrations/                 # Scripts de migración BD
```

---

## 5. GESTIÓN DE NOTAS CRÉDITO - DETALLE TÉCNICO

### 5.1 Flujo de Vida de una Nota Crédito

```
1. RECIBIDA DE API
   └─ Prefijo 'N' + Tipo Inventario Permitido

2. VALIDACIÓN EN NEGOCIO
   ├─ Verifica tipo inventario no esté excluido
   └─ Si pasa: entra a REGISTRAR

3. REGISTRADA EN BD
   ├─ Estado: PENDIENTE
   ├─ saldo_pendiente = valor_total
   ├─ cantidad_pendiente = cantidad
   └─ Espera aplicación

4. APLICACIÓN AUTOMÁTICA
   ├─ Se busca factura del MISMO cliente + MISMO producto
   ├─ Si encuentra:
   │  ├─ Aplicar min(saldo_nota, valor_factura)
   │  ├─ Registrar en aplicaciones_notas
   │  └─ Actualizar saldos
   ├─ Si nota se aplica completamente → Estado APLICADA
   └─ Si queda saldo → Sigue PENDIENTE

5. PERSISTENCIA
   └─ BD commitida a repo cada día
```

### 5.2 Lógica de Aplicación

**Matching:**
- NIT_CLIENTE debe coincidir
- CODIGO_PRODUCTO debe coincidir
- Validar: saldo_pendiente > 0

**Cálculo:**
```python
valor_a_aplicar = min(saldo_nota, valor_factura)
proporcion = valor_a_aplicar / valor_factura
cantidad_a_aplicar = min(cantidad_nota, cantidad_factura * proporcion)
```

**Actualización:**
```python
nuevo_saldo = saldo_nota - valor_aplicado
nuevo_estado = 'APLICADA' if nuevo_saldo <= 0.01 else 'PENDIENTE'
```

---

## 6. VALIDACIONES Y REGLAS DE NEGOCIO

### 6.1 BusinessRulesValidator

**Tipos de Inventario Excluidos (23 tipos):**
```
VSMENORCC, VS4205101, INVMEDICAD, INV1430051, VS42100501,
VS420515, VS42051003, VS420510, VSMENOR, INVFLETEPT,
VSMENOR5%, VS42505090, INVFLETGEN, INV144542, INV144554,
VSMAY-MECC, VSMAY-MECP, VSMAY-GEN, DESCESPEC, DESCUENTO,
INV144562, VS425050, VS41200822, INV1460, VS41200819
```

**Validaciones:**

| Criterio | Valor | Acción |
|----------|-------|--------|
| Tipo Inventario | En lista excluidos | Rechazar |
| Monto Factura | < $498,000 COP | Rechazar |
| Prefijo | 'N' | Separar como Nota Crédito |
| Prefijo | Otro | Procesar como Factura |

**Normalización:**
- Espacios en blanco removidos
- Convertir a mayúsculas
- Comparación con lista normalizada

---

## 7. REPORTE OPERATIVO DIARIO

### 7.1 Excel Generado (facturas_YYYYMMDD.xlsx)
**Incluye columnas:**
- Número factura, prefijo, cliente
- Fecha factura, fecha vencimiento (calculada)
- NIT vendedor, código subyacente
- Descripción producto, cantidad
- Valor unitario, subtotal, IVA
- Valor total a cobrar
- Notas de aplicación si la aplica una nota crédito

### 7.2 Reportes TXT Adicionales

**reporte_notas_credito_YYYYMMDD.txt:**
```
Resumen:
- Notas pendientes
- Saldo pendiente total
- Notas aplicadas (histórico)
- Total aplicaciones (histórico)
- Monto total aplicado (histórico)

Detalle aplicaciones realizadas hoy:
  Nota → Factura
  Valor aplicado: $XXX
  Cantidad aplicada: XXX
  Saldo restante: $XXX
  Estado: [PENDIENTE|APLICADA]
```

**facturas_rechazadas_YYYYMMDD.txt:**
```
Factura
Cliente
Producto
Tipo Inventario
Valor
Razón de rechazo
─────────────────
(repite para cada rechazo)
```

### 7.3 Correo Automático

**De:** EMAIL_USERNAME (configurado)
**Para:** DESTINATARIOS
**Asunto:** "Reporte Diario de Facturas - DD/MM/YYYY"
**Cuerpo:** HTML con fecha y enlace a artifact
**Adjunto:** facturas_YYYYMMDD.xlsx

---

## 8. SISTEMA DE AUTENTICACIÓN Y USUARIOS

### 8.1 Arquitectura Auth

**JWT Flow:**
```
Login Endpoint (/api/login)
├─ Recibe: username, password
├─ Valida: credenciales contra BD (bcrypt)
├─ Si OK: 
│  ├─ Genera access_token (1 hora)
│  ├─ Genera refresh_token (30 días)
│  ├─ Registra sesión en BD
│  └─ Retorna tokens
└─ Si Error: Incrementa intentos fallidos

Protección Endpoints:
├─ @jwt_required() en decoradores
├─ Valida token en cada request
├─ Verifica sesión activa en BD
└─ Retorna 401 si inválido
```

### 8.2 Usuarios y Roles

**Usuario Admin Inicial:**
```
username: admin
password: admin123 (CAMBIAR en producción)
rol: admin
email: admin@cipa.com
```

**Roles Disponibles:**
- **admin:** Acceso completo a todo
- **editor:** Puede modificar datos
- **viewer:** Solo lectura

**Seguridad:**
- Hash bcrypt (cost 12)
- Rate limiting: 5 intentos → bloqueo 15 min
- Registro de todos los intentos de login
- Tracking de IP y user-agent

### 8.3 Tabla Usuarios
```
id, username (UNIQUE), password_hash
email, rol, activo
intentos_fallidos, bloqueado_hasta
ultimo_acceso, fecha_creacion, fecha_modificacion
```

---

## 9. API REST - ENDPOINTS PRINCIPALES

**Base URL:** `http://localhost:5000/api`

### Autenticación
```
POST /login
  body: {username, password}
  response: {access_token, refresh_token, usuario: {id, username, email, rol}}

POST /refresh
  header: Authorization: Bearer <refresh_token>
  response: {access_token}

POST /logout
  header: Authorization: Bearer <access_token>
```

### Notas Crédito (requiere JWT)
```
GET /notas-credito
  query: ?estado=PENDIENTE|APLICADA&cliente=nit&skip=0&limit=50
  response: [{numero_nota, valor_total, saldo_pendiente, estado, ...}]

GET /notas-credito/{id}/historial
  response: [aplicaciones de esa nota]

GET /resumen
  response: {notas_pendientes, saldo_pendiente_total, notas_aplicadas, ...}
```

### Facturas
```
GET /facturas-rechazadas
  response: [facturas no procesadas con razón]

GET /tipos-inventario
  response: [tipos detectados en los últimos 30 días]
```

### Health & Debug
```
GET /health
  response: {status: "OK", timestamp}

GET /database-stats
  response: {tables: {notas_credito: 0, aplicaciones: 0, ...}}
```

---

## 10. FRONTEND - ESTRUCTURA Y FEATURES

**Base URL:** `http://localhost:3000`

**Tecnología:** React 18 + TypeScript + Vite + Tailwind CSS

### Páginas Principales

**LoginPage:**
- Formulario login con validación
- Error handling
- Redirect a Dashboard si autenticado

**DashboardPage:**
- Resumen estadístico de notas
- Gráficos de estado
- Últimas aplicaciones realizadas
- Links a detalles

**NotasPage:**
- Listado completo de notas
- Filtros por estado/cliente
- Búsqueda
- Paginación

**NotaDetailPage:**
- Detalle de una nota específica
- Historial de aplicaciones
- Estado actual
- Información cliente/producto

### Características
- Sistema de autenticación JWT
- Manejo de tokens (auto-refresh)
- Almacenamiento en localStorage
- Handling de errores HTTP
- Loading states
- Responsive design

---

## 11. ARCHIVOS CLAVE Y LOCALIZACIÓN

```
AUTOMATIZACIÓN
├─ .github/workflows/daily_process.yml (283 líneas)
└─ .github/workflows/backup_semanal.yml (79 líneas)

BACKEND - CORE NEGOCIO
├─ backend/main.py (301 líneas)
│  ├─ Orquestación principal del proceso
│  └─ Llama módulos en orden: API → Reglas → Notas → Excel → Email
├─ backend/export_operativa_custom.py (345 líneas)
│  └─ Exportación personalizada con rango de fechas

BACKEND - MÓDULOS CORE (backend/core/)
├─ api_client.py (139 líneas)
│  └─ Cliente SIESA con manejo de errores
├─ business_rules.py (318 líneas)
│  └─ Validación de facturas y tipos inventario
├─ notas_credito_manager.py (670 líneas) **CRÍTICO**
│  └─ Gestión completa: registrar, buscar, aplicar notas
├─ excel_processor.py (400+ líneas)
│  └─ Transformación y generación de Excel
├─ email_sender.py (106 líneas)
│  └─ Envío de correos SMTP
└─ archivador_notas.py (400+ líneas)
   └─ Archivado de notas completadas

BACKEND - API REST (backend/api/)
├─ app.py (1300+ líneas)
│  └─ Servidor Flask con todos los endpoints
├─ auth.py (426 líneas)
│  └─ Sistema de autenticación JWT + bcrypt

BACKEND - SCRIPTS (backend/scripts/)
├─ backup_database.py (Backup manual)
├─ consultar_notas.py (Queries directas)
├─ reporte_diario.py (Generación reportes)
├─ verificar_config.py (Validación setup)
├─ test_api_connection.py (Prueba SIESA)
├─ inicializar_auth.py (Setup usuario admin)
└─ migrations/ (Scripts de migración)

CONFIGURACIÓN
├─ backend/.env.example
├─ backend/.env.production
├─ backend/requirements.txt
└─ backend/config/config.py (vacío actualmente)

BASE DE DATOS
└─ data/notas_credito.db (SQLite, 749KB)
   ├─ 9 tablas principales
   ├─ Versionada en Git
   └─ Actualizada diariamente por GitHub Actions

DOCUMENTACIÓN
├─ docs/ARQUITECTURA.md (con diagramas Mermaid)
├─ docs/GUIA_RAPIDA.md
├─ docs/API_ENDPOINTS.md
├─ docs/INSTRUCCIONES_POBLAR_BD.md
└─ docs/*.md (8 archivos más)
```

---

## 12. FLUJO DIARIO COMPLETO

### Línea de Tiempo (América/Bogotá)

```
8:00 AM (13:00 UTC)
├─ GitHub Actions dispara daily_process.yml
│
1️⃣ Setup (2 min)
├─ Checkout código
├─ Setup Python 3.11
├─ Instalar dependencias (cached)
│
2️⃣ Backup (1 min)
├─ Copiar BD actual a backup
├─ Mostrar estadísticas ANTES
│
3️⃣ Procesamiento (5-15 min)
├─ main.py ejecuta:
│  ├─ API SIESA: obtener facturas día anterior
│  ├─ Validaciones: filtrar por reglas
│  ├─ Notas: registrar y aplicar
│  ├─ Excel: generar reportes
│  └─ Email: enviar a operativa
│
4️⃣ Persistencia (2 min)
├─ Commit BD actualizada
├─ Push a repositorio
│
5️⃣ Artifacts (1 min)
├─ Upload Excel (30 días)
├─ Upload reportes TXT (30 días)
├─ Upload backup BD (7 días)
│
TOTAL: 15-30 minutos
RESULTADO: Correo recibido por operativa con reporte diario
```

---

## 13. ESTADÍSTICAS ACTUALES

```
Base de Datos (notas_credito.db):
├─ Usuarios: 1 (admin)
├─ Sesiones: Variable (activas)
├─ Notas Crédito: 0
├─ Aplicaciones Notas: 0
└─ Facturas Rechazadas: 2,955 (historial)

Código:
├─ Backend: ~3,000 líneas Python
├─ Frontend: React + TypeScript
└─ API: 1,389 líneas en /api

GitHub Actions:
├─ daily_process.yml: Ejecuta diariamente
└─ backup_semanal.yml: Ejecuta domingos
```

---

## 14. PUNTOS CRÍTICOS DE OPERACIÓN

### Requisitos Operativos

```
✅ API SIESA disponible (consulta diaria)
✅ Credenciales configuradas (secrets GitHub)
✅ Base de datos Git (persistencia)
✅ Servidor SMTP funcional (envío correos)
✅ Base de datos no corrupta
```

### Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| API SIESA no disponible | No se obtienen facturas | Log claro, reintento manual |
| BD corrupta | Pérdida de historial | Backup semanal en artifacts |
| Fallo SMTP | No se envía reporte | Log de error, retry en próxima ejecución |
| Secrets incorrectos | No accede API/SMTP | Validación en app.py y main.py |

---

## CONCLUSIONES

Sistema **totalmente automatizado** con:
- ✅ Captura diaria de datos (API SIESA)
- ✅ Validación automática (reglas negocio)
- ✅ Aplicación automática notas (matching cliente+producto)
- ✅ Reportes generados (Excel + TXT)
- ✅ Distribución automática (email diario)
- ✅ Persistencia en Git (versionamiento BD)
- ✅ API REST para consultas (con autenticación JWT)
- ✅ Frontend web profesional (React)

**Responsable de operación:** GitHub Actions (sin intervención manual necesaria)
