# Scripts de Población de Facturas

Este directorio contiene scripts para poblar la tabla de facturas con datos para el sistema de transacciones.

## 📋 Scripts Disponibles

### 1. `poblar_facturas_api_crudo.py` ⭐ RECOMENDADO

**Obtiene datos REALES del API de SIESA sin transformaciones**

```bash
# Poblar últimos 7 días con datos reales
python scripts/poblar_facturas_api_crudo.py --dias 7

# Poblar una fecha específica
python scripts/poblar_facturas_api_crudo.py --fecha 2025-11-10
```

**Características:**
- ✅ Datos REALES del API de SIESA
- ✅ Sin transformaciones (datos crudos)
- ✅ Aplica reglas de negocio (monto mínimo, tipos excluidos)
- ✅ Tipos de inventario tal cual vienen del API
- ⚠️ Requiere credenciales en `.env` (CONNI_KEY, CONNI_TOKEN)

**Requisitos:**
```bash
# Archivo .env debe contener:
CONNI_KEY=tu_clave_aqui
CONNI_TOKEN=tu_token_aqui
```

---

### 2. `poblar_facturas_diarias.py`

**Genera datos de PRUEBA con reglas de negocio**

```bash
# Poblar últimos 30 días con datos de prueba
python scripts/poblar_facturas_diarias.py --dias 30 --por-dia 12

# Poblar solo ayer
python scripts/poblar_facturas_diarias.py --solo-ayer --ayer-cantidad 25
```

**Características:**
- ✅ Datos de prueba realistas
- ✅ Cumple reglas de negocio
- ✅ No requiere API (offline)
- ⚠️ NO son datos reales del API

**Uso:**
- Para desarrollo y testing
- Cuando no hay acceso al API
- Para poblar datos históricos de ejemplo

---

### 3. `poblar_facturas_desde_api.py`

**Obtiene datos del API y aplica transformaciones (DEPRECATED)**

Usar `poblar_facturas_api_crudo.py` en su lugar.

---

## 🎯 ¿Cuál usar?

### Para PRODUCCIÓN o DATOS REALES:
```bash
python scripts/poblar_facturas_api_crudo.py --dias 7
```

### Para DESARROLLO o TESTING:
```bash
python scripts/poblar_facturas_diarias.py --dias 30 --por-dia 12
```

---

## 📊 Campos Guardados

Los datos se guardan en la tabla `facturas` con estos campos:

| Campo | Origen API SIESA | Descripción |
|-------|------------------|-------------|
| `numero_factura` | `f_prefijo` + `f_nrodocto` | Número completo de factura |
| `fecha_factura` | `f_fecha_factura` o `f_fecha` | Fecha sin modificar |
| `nit_cliente` | `f_nit` | NIT del cliente |
| `nombre_cliente` | `f_nombre_cliente` | Nombre sin modificar |
| `codigo_producto` | `f_cod_item` | Código del producto |
| `nombre_producto` | `f_desc_item` | Descripción del producto |
| `tipo_inventario` | `f_cod_tipo_inv` o `f_tipo_inv` | **TAL CUAL viene del API** |
| `valor_total` | `f_valor_subtotal_local` | Valor subtotal |
| `cantidad` | `f_cantidad` | Cantidad |
| `es_valida` | (calculado) | Cumple reglas de negocio |

---

## 🔍 Reglas de Negocio Aplicadas

1. **Monto mínimo:** $498,000 COP por factura completa
2. **Tipos excluidos:** 24 tipos de inventario bloqueados:
   - VSMENORCC, VS4205101, INVMEDICAD, etc.
3. **Validación de notas:** Por tipo de inventario

---

## 🚀 Ejemplo de Uso

### Limpiar y repoblar con datos reales:

```bash
cd /home/user/cipa/backend

# Limpiar tabla
python -c "import sqlite3; conn = sqlite3.connect('data/notas_credito.db'); conn.execute('DELETE FROM facturas'); conn.commit(); print('✅ Limpiado')"

# Poblar con datos reales del API
python scripts/poblar_facturas_api_crudo.py --dias 7

# Ver estadísticas
python -c "import sqlite3; conn = sqlite3.connect('data/notas_credito.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM facturas'); print(f'Total: {c.fetchone()[0]}')"
```

---

## ⚠️ Notas Importantes

1. **Tipos de Inventario:** Se guardan EXACTAMENTE como vienen del API
   - No se traducen
   - No se normalizan
   - No se modifican

2. **Datos Crudos:** El script `poblar_facturas_api_crudo.py` no aplica transformaciones del `ExcelProcessor`

3. **Credenciales:** El script que usa el API requiere `.env` configurado

---

## 🔧 Solución de Problemas

### "Faltan credenciales del API"
```bash
# Crear archivo .env en /home/user/cipa/backend/
echo "CONNI_KEY=tu_clave" >> .env
echo "CONNI_TOKEN=tu_token" >> .env
```

### "Sin documentos en el API"
- Normal para días sin facturación
- Probar con otra fecha

### "Error al guardar factura"
- Verificar que la tabla `facturas` existe
- Ejecutar `scripts/crear_tabla_facturas.py`

---

## 📝 Logs

Los scripts muestran logs detallados:

```
📅 OBTENIENDO FACTURAS DEL API SIESA: 2025-11-10
🔄 Consultando API de SIESA...
✅ Obtenidos 45 documentos del API
🔍 Aplicando reglas de negocio...

📊 RESULTADOS:
   ✓ Facturas válidas: 38
   ✓ Notas crédito: 5
   ✗ Rechazadas: 2

💾 GUARDADO EN BD:
   ✓ Válidas: 38
   ✓ Rechazadas: 2
```
