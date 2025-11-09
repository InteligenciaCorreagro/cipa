# Exportación Personalizada de Archivo Operativo

Este documento explica cómo usar el script `export_operativa_custom.py` para generar archivos de operativa con rangos de fechas personalizados.

## Descripción

El script `export_operativa_custom.py` permite exportar el archivo de facturas para la operativa usando un rango de fechas específico que tú definas. Esto es útil para:

- **Testear** datos de periodos específicos
- **Re-generar** archivos de fechas pasadas
- **Analizar** facturas de rangos de tiempo personalizados
- **Validar** cambios antes de ejecutar el proceso automático

**IMPORTANTE:** Este script NO afecta el proceso diario automático. Es una herramienta independiente para uso manual.

## Requisitos

- Python 3.11+
- Variables de entorno configuradas en `.env`
- Acceso a la API de SIESA (CONNI_KEY y CONNI_TOKEN)

## Uso Básico

### 1. Generar archivo sin enviar correo (solo local)

```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-11-01 \
  --fecha-fin 2025-11-08
```

Este comando:
- Obtiene las facturas del rango especificado
- Aplica las reglas de negocio
- Genera el archivo Excel en `./output/`
- NO envía correo electrónico
- NO registra notas de crédito en la base de datos

### 2. Generar archivo Y enviar por correo

```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-11-01 \
  --fecha-fin 2025-11-08 \
  --enviar-correo
```

Este comando hace lo mismo que el anterior, pero además:
- Envía el archivo por correo a los destinatarios configurados en `.env`

### 3. Especificar directorio de salida personalizado

```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-11-01 \
  --fecha-fin 2025-11-08 \
  --output-dir ./mis_exportaciones
```

## Parámetros

| Parámetro | Requerido | Descripción | Ejemplo |
|-----------|-----------|-------------|---------|
| `--fecha-inicio` | ✓ | Fecha de inicio del rango (formato: YYYY-MM-DD) | `2025-11-01` |
| `--fecha-fin` | ✓ | Fecha de fin del rango (formato: YYYY-MM-DD) | `2025-11-08` |
| `--enviar-correo` | ✗ | Enviar el archivo por correo | (flag sin valor) |
| `--output-dir` | ✗ | Directorio de salida (default: `./output`) | `./mis_exportaciones` |

## Archivos Generados

El script genera los siguientes archivos:

### 1. Archivo Excel Principal

**Ubicación:** `{output-dir}/facturas_custom_YYYYMMDD_YYYYMMDD.xlsx`

**Formato:** Mismo formato que el proceso diario
- 23 columnas con datos de facturas
- Facturas válidas según reglas de negocio
- Listo para enviar a operativa

**Ejemplo:** `facturas_custom_20251101_20251108.xlsx`

### 2. Reporte de Facturas Rechazadas (si aplica)

**Ubicación:** `{output-dir}/facturas_rechazadas_custom_YYYYMMDD_YYYYMMDD.txt`

**Contenido:**
- Lista de facturas que no cumplieron las reglas de negocio
- Razón de rechazo para cada factura
- Detalles del documento (número, cliente, valor, etc.)

## Ejemplos de Uso

### Exportar facturas de un día específico

```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-11-05 \
  --fecha-fin 2025-11-05
```

### Exportar facturas de una semana

```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-11-01 \
  --fecha-fin 2025-11-07
```

### Exportar y enviar facturas de un mes

```bash
python backend/export_operativa_custom.py \
  --fecha-inicio 2025-10-01 \
  --fecha-fin 2025-10-31 \
  --enviar-correo
```

### Re-generar archivo de ayer

```bash
# En Linux/Mac
python backend/export_operativa_custom.py \
  --fecha-inicio $(date -d "yesterday" +%Y-%m-%d) \
  --fecha-fin $(date -d "yesterday" +%Y-%m-%d)
```

## Diferencias con el Proceso Diario

| Característica | Proceso Diario | Exportación Personalizada |
|----------------|----------------|---------------------------|
| **Fecha** | Día anterior automático | Rango personalizado |
| **Ejecución** | Automática (GitHub Actions) | Manual por comando |
| **Registro de Notas** | SÍ - Registra notas en BD | NO - Solo lectura |
| **Aplicación de Notas** | SÍ - Aplica notas pendientes | NO - Solo muestra info |
| **Commit Git** | SÍ - Commit automático | NO - Solo genera archivos |
| **Envío de Correo** | SÍ - Siempre envía | Opcional (flag `--enviar-correo`) |

## Notas Importantes

### ⚠️ Notas de Crédito

El script en modo personalizado **NO registra ni aplica notas de crédito**. Esto es intencional para:
- Evitar duplicados en la base de datos
- Mantener la integridad de los registros del proceso diario
- Permitir testeos sin efectos secundarios

Si detecta notas de crédito en el rango, solo las muestra en el log pero no las procesa.

### ⚠️ Base de Datos

El script **NO modifica** la base de datos `notas_credito.db`. Solo lee el estado actual de las notas para mostrar información.

### ⚠️ Proceso Diario

Este script es completamente independiente del proceso diario automático. Puedes usarlo sin preocuparte de afectar el workflow normal.

## Solución de Problemas

### Error: "Faltan variables de entorno requeridas"

**Causa:** No se encontraron las variables `CONNI_KEY` o `CONNI_TOKEN` en el archivo `.env`

**Solución:**
```bash
# Verificar que el archivo .env existe
cat .env | grep CONNI_KEY
cat .env | grep CONNI_TOKEN
```

### Error: "La fecha de inicio debe ser anterior o igual a la fecha de fin"

**Causa:** La fecha de inicio es posterior a la fecha de fin

**Solución:** Verifica que el orden de las fechas sea correcto:
```bash
# Correcto
--fecha-inicio 2025-11-01 --fecha-fin 2025-11-08

# Incorrecto
--fecha-inicio 2025-11-08 --fecha-fin 2025-11-01
```

### Error: "El formato debe ser YYYY-MM-DD"

**Causa:** El formato de fecha no es correcto

**Solución:** Usa el formato ISO 8601:
```bash
# Correcto
--fecha-inicio 2025-11-01

# Incorrecto
--fecha-inicio 01-11-2025
--fecha-inicio 2025/11/01
--fecha-inicio 11/01/2025
```

### No se encontraron facturas

**Causa:** No hay facturas en el rango especificado o hay un error en la API

**Solución:**
1. Verifica que las fechas tengan facturas en SIESA
2. Revisa los logs para ver si hay errores de API
3. Verifica la conexión a la API de SIESA

## Logs y Depuración

El script muestra información detallada en la consola:

```
2025-11-09 10:30:00 - INFO - ============================================================
2025-11-09 10:30:00 - INFO - EXPORTACIÓN PERSONALIZADA DE ARCHIVO OPERATIVO
2025-11-09 10:30:00 - INFO - Rango de fechas: 2025-11-01 hasta 2025-11-08
2025-11-09 10:30:00 - INFO - Enviar correo: NO
2025-11-09 10:30:00 - INFO - ============================================================

2025-11-09 10:30:01 - INFO - Consultando facturas desde 2025-11-01 hasta 2025-11-08
2025-11-09 10:30:02 - INFO - Se obtuvieron 150 facturas
2025-11-09 10:30:02 - INFO - Total de documentos obtenidos de la API: 150

2025-11-09 10:30:03 - INFO - ============================================================
2025-11-09 10:30:03 - INFO - RESULTADOS DEL FILTRADO:
2025-11-09 10:30:03 - INFO -   - Facturas válidas: 120
2025-11-09 10:30:03 - INFO -   - Notas crédito: 5
2025-11-09 10:30:03 - INFO -   - Facturas rechazadas: 25
2025-11-09 10:30:03 - INFO - ============================================================

2025-11-09 10:30:04 - INFO - ✓ Archivo generado exitosamente: ./output/facturas_custom_20251101_20251108.xlsx
```

## Contacto y Soporte

Si encuentras problemas o tienes preguntas sobre el script, revisa:
1. Los logs en la consola
2. El archivo de facturas rechazadas (si existe)
3. Las variables de entorno en `.env`
