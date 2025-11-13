# API Endpoints - Sistema CIPA

## 🔐 Autenticación

Todos los endpoints (excepto `/api/health` y `/api/auth/*`) requieren autenticación JWT.

**Header requerido:**
```
Authorization: Bearer <token>
```

---

## 📊 Endpoints de Dashboard y Grillas

### 1. Facturas Rechazadas
**Endpoint:** `GET /api/facturas/rechazadas`

Obtiene la grilla de facturas que fueron rechazadas por reglas de negocio.

**Query Parameters:**
- `limite` (int, opcional): Número de registros por página. Default: 50
- `offset` (int, opcional): Offset para paginación. Default: 0
- `fecha_desde` (string, opcional): Filtrar desde fecha (YYYY-MM-DD)
- `fecha_hasta` (string, opcional): Filtrar hasta fecha (YYYY-MM-DD)

**Respuesta:**
```json
{
  "items": [
    {
      "id": 123,
      "numero_factura": "FME12345",
      "fecha_factura": "2025-11-10",
      "nit_cliente": "800123456",
      "nombre_cliente": "CLIENTE EJEMPLO S.A.S.",
      "codigo_producto": "PROD001",
      "nombre_producto": "PRODUCTO EJEMPLO",
      "tipo_inventario": "DESCUENTO",
      "valor_total": 150000.00,
      "razon_rechazo": "Tipo de inventario excluido: DESCUENTO",
      "fecha_registro": "2025-11-10T10:30:00"
    }
  ],
  "total": 234,
  "limite": 50,
  "offset": 0
}
```

**Razones de rechazo comunes:**
- `"Tipo de inventario excluido: [TIPO]"` - El tipo de inventario está en la lista de excluidos
- `"Valor total de factura $X no cumple monto mínimo $498,000"` - La factura completa no alcanza el monto mínimo
- `"Nota crédito con tipo de inventario excluido: [TIPO]"` - Nota crédito con tipo excluido

---

### 2. Facturas con Notas Aplicadas
**Endpoint:** `GET /api/facturas/con-notas`

Obtiene la grilla de facturas que tienen notas de crédito aplicadas.

**Query Parameters:**
- `limite` (int, opcional): Número de registros por página. Default: 50
- `offset` (int, opcional): Offset para paginación. Default: 0
- `fecha_desde` (string, opcional): Filtrar desde fecha (YYYY-MM-DD)
- `fecha_hasta` (string, opcional): Filtrar hasta fecha (YYYY-MM-DD)

**Respuesta:**
```json
{
  "items": [
    {
      "id": 456,
      "numero_factura": "FME12345",
      "fecha_factura": "2025-11-10",
      "nit_cliente": "800123456",
      "nombre_cliente": "CLIENTE EJEMPLO S.A.S.",
      "codigo_producto": "PROD001",
      "nombre_producto": "PRODUCTO EJEMPLO",
      "tipo_inventario": "INV143002",
      "valor_total": 850000.00,
      "cantidad": 100.0,
      "descripcion_nota_aplicada": "Nota aplicada: NCE8262",
      "fecha_proceso": "2025-11-10"
    }
  ],
  "total": 127,
  "limite": 50,
  "offset": 0
}
```

**Campo `descripcion_nota_aplicada`:**
- `"Nota aplicada: NCE8262"` - Una sola nota aplicada
- `"Notas aplicadas: NCE8262, NPA2"` - Múltiples notas aplicadas
- `null` - Sin notas aplicadas (no debería aparecer en este endpoint)

---

### 3. Facturas Transadas
**Endpoint:** `GET /api/facturas/transacciones`

Obtiene facturas con valores transados (valor_transado > 0).

**Query Parameters:**
- `limite` (int, opcional): Número de registros por página. Default: 50
- `offset` (int, opcional): Offset para paginación. Default: 0

**Respuesta:**
```json
{
  "items": [
    {
      "id": 789,
      "numero_factura": "FME12345",
      "fecha_factura": "2025-11-10",
      "nit_cliente": "800123456",
      "nombre_cliente": "CLIENTE EJEMPLO S.A.S.",
      "codigo_producto": "PROD001",
      "nombre_producto": "PRODUCTO EJEMPLO",
      "valor_total": 850000.00,
      "valor_transado": 50000.00,
      "cantidad": 100.0,
      "cantidad_transada": 5.0,
      "estado": "VALIDA",
      "tiene_nota_credito": 1,
      "descripcion_nota_aplicada": "Nota aplicada: NCE8262"
    }
  ],
  "total": 89,
  "limite": 50,
  "offset": 0
}
```

---

### 4. Todas las Facturas
**Endpoint:** `GET /api/facturas`

Obtiene todas las facturas con filtros opcionales.

**Query Parameters:**
- `limite` (int, opcional): Número de registros por página. Default: 50
- `offset` (int, opcional): Offset para paginación. Default: 0
- `numero_factura` (string, opcional): Filtrar por número de factura
- `estado` (string, opcional): Filtrar por estado (VALIDA, PENDIENTE, etc.)
- `nit_cliente` (string, opcional): Filtrar por NIT de cliente
- `fecha_desde` (string, opcional): Filtrar desde fecha (YYYY-MM-DD)
- `fecha_hasta` (string, opcional): Filtrar hasta fecha (YYYY-MM-DD)
- `es_valida` (string, opcional): Filtrar por validez ("true" o "false")

**Respuesta:**
```json
{
  "items": [...],
  "total": 1523,
  "limite": 50,
  "offset": 0,
  "total_paginas": 31
}
```

---

### 5. Factura Individual
**Endpoint:** `GET /api/facturas/<id>`

Obtiene detalles de una factura específica incluyendo aplicaciones de notas.

**Respuesta:**
```json
{
  "id": 456,
  "numero_factura": "FME12345",
  "fecha_factura": "2025-11-10",
  "nit_cliente": "800123456",
  "nombre_cliente": "CLIENTE EJEMPLO S.A.S.",
  "codigo_producto": "PROD001",
  "nombre_producto": "PRODUCTO EJEMPLO",
  "tipo_inventario": "INV143002",
  "valor_total": 850000.00,
  "cantidad": 100.0,
  "descripcion_nota_aplicada": "Nota aplicada: NCE8262",
  "estado": "VALIDA",
  "tiene_nota_credito": 1,
  "fecha_proceso": "2025-11-10",
  "aplicaciones": [
    {
      "id": 12,
      "id_nota": 45,
      "numero_nota": "NCE8262",
      "numero_factura": "FME12345",
      "fecha_factura": "2025-11-10",
      "nit_cliente": "800123456",
      "codigo_producto": "PROD001",
      "valor_aplicado": 50000.00,
      "cantidad_aplicada": 5.0,
      "fecha_aplicacion": "2025-11-10T14:30:00"
    }
  ]
}
```

---

### 6. Estadísticas de Facturas
**Endpoint:** `GET /api/facturas/estadisticas`

Obtiene estadísticas generales de facturas.

**Respuesta:**
```json
{
  "total_facturas": 1523,
  "facturas_validas": 1234,
  "facturas_con_notas": 127,
  "facturas_rechazadas": 289,
  "valor_total": 1250000000.00,
  "valor_promedio": 820000.00
}
```

---

## 📋 Endpoints de Notas de Crédito

### 1. Todas las Notas
**Endpoint:** `GET /api/notas`

Obtiene todas las notas de crédito con filtros opcionales.

**Query Parameters:**
- `limite` (int, opcional): Número de registros por página. Default: 50
- `offset` (int, opcional): Offset para paginación. Default: 0
- `estado` (string, opcional): PENDIENTE, APLICADA, etc.
- `fecha_desde` (string, opcional): Filtrar desde fecha (YYYY-MM-DD)
- `fecha_hasta` (string, opcional): Filtrar hasta fecha (YYYY-MM-DD)

**Respuesta:**
```json
{
  "items": [
    {
      "id": 45,
      "numero_nota": "NCE8262",
      "fecha_nota": "2025-11-10",
      "nit_cliente": "800123456",
      "nombre_cliente": "CLIENTE EJEMPLO S.A.S.",
      "codigo_producto": "PROD001",
      "nombre_producto": "PRODUCTO EJEMPLO",
      "tipo_inventario": "INV143005",
      "valor_total": 100000.00,
      "cantidad": 10.0,
      "saldo_pendiente": 50000.00,
      "cantidad_pendiente": 5.0,
      "estado": "PENDIENTE",
      "fecha_registro": "2025-11-10T10:00:00"
    }
  ],
  "total": 234,
  "limite": 50,
  "offset": 0,
  "total_paginas": 5
}
```

### 2. Notas Pendientes
**Endpoint:** `GET /api/notas/pendientes`

Obtiene solo las notas con saldo pendiente.

### 3. Notas Aplicadas
**Endpoint:** `GET /api/notas/aplicadas`

Obtiene solo las notas completamente aplicadas.

---

## 🔍 Ejemplo de Uso desde Frontend

### JavaScript/React Example:

```javascript
// 1. Obtener facturas rechazadas
const fetchFacturasRechazadas = async (page = 0, limit = 50) => {
  const response = await fetch(
    `${API_URL}/api/facturas/rechazadas?limite=${limit}&offset=${page * limit}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return await response.json();
};

// 2. Obtener facturas con notas
const fetchFacturasConNotas = async (fechaDesde, fechaHasta) => {
  const response = await fetch(
    `${API_URL}/api/facturas/con-notas?fecha_desde=${fechaDesde}&fecha_hasta=${fechaHasta}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return await response.json();
};

// 3. Obtener detalles de una factura
const fetchFacturaDetalle = async (facturaId) => {
  const response = await fetch(
    `${API_URL}/api/facturas/${facturaId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return await response.json();
};
```

---

## 📊 Componentes de Grilla Sugeridos

### 1. Grilla de Facturas Rechazadas

**Columnas sugeridas:**
- Número Factura
- Fecha
- Cliente
- Producto
- Tipo Inventario
- Valor
- **Razón de Rechazo** ⚠️ (importante)
- Fecha Registro

**Filtros sugeridos:**
- Rango de fechas
- Buscar por número de factura
- Buscar por cliente

---

### 2. Grilla de Facturas con Notas

**Columnas sugeridas:**
- Número Factura
- Fecha
- Cliente
- Producto
- Valor
- Cantidad
- **Nota Aplicada** ✅ (importante)
- Fecha Proceso

**Filtros sugeridos:**
- Rango de fechas
- Buscar por número de factura
- Buscar por número de nota

---

### 3. Grilla de Transacciones

**Columnas sugeridas:**
- Número Factura
- Fecha
- Cliente
- Producto
- Valor Total
- **Valor Transado** 💰
- Cantidad Total
- **Cantidad Transada**
- Nota Aplicada (si tiene)

---

## 🎨 Estados y Badges

Sugerencias de badges/colores para el frontend:

| Estado | Color | Descripción |
|--------|-------|-------------|
| `tiene_nota_credito = 1` | 🟢 Verde | Factura con nota aplicada |
| `tiene_nota_credito = 0` | ⚪ Gris | Factura sin nota |
| `estado = 'RECHAZADA'` | 🔴 Rojo | Factura rechazada |
| `estado = 'VALIDA'` | 🟢 Verde | Factura válida |
| `valor_transado > 0` | 🟡 Amarillo | Con transacciones |

---

## 🔄 Paginación

Todos los endpoints de grilla soportan paginación:

```javascript
// Ejemplo de paginación
const fetchPage = async (pageNumber, pageSize = 50) => {
  const offset = pageNumber * pageSize;
  const response = await fetch(
    `${API_URL}/api/facturas/rechazadas?limite=${pageSize}&offset=${offset}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );

  const data = await response.json();

  // data.total = total de registros
  // data.items = registros de la página actual
  // data.limite = tamaño de página
  // data.offset = offset actual

  const totalPages = Math.ceil(data.total / pageSize);
  return { ...data, totalPages };
};
```

---

## 🐛 Manejo de Errores

Todos los endpoints pueden retornar:

**401 Unauthorized:**
```json
{
  "msg": "Missing Authorization Header"
}
```

**403 Forbidden:**
```json
{
  "msg": "Usuario bloqueado temporalmente"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Error al obtener facturas rechazadas"
}
```

---

## 📝 Notas Importantes

1. **Múltiples líneas por factura:** Una factura como FME123 puede aparecer 4 veces en la grilla (una por cada producto). Esto es correcto y esperado.

2. **Campo `descripcion_nota_aplicada`:** Este campo es NULL si la factura no tiene notas. Solo las facturas con `tiene_nota_credito = 1` tendrán este campo poblado.

3. **Filtros de fecha:** Use formato `YYYY-MM-DD` para los parámetros de fecha.

4. **Paginación:** Siempre use paginación para grillas grandes. El límite default es 50 registros.

5. **Performance:** Los endpoints están optimizados con índices en la base de datos para consultas rápidas.
