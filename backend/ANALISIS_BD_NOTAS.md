# Análisis de Aplicación de Notas de Crédito - Base de Datos Real

**Fecha**: 2025-12-09
**Base de datos analizada**: `/home/user/cipa/data/notas_credito.db`

---

## 📊 Estado Actual de la Base de Datos

### Notas de Crédito
- **Total notas PENDIENTES**: 42 notas
- **Saldo total pendiente**: $24,114,135.00 (valor absoluto)
- **Estado**: Todas en estado PENDIENTE

### Facturas
- **Facturas sin nota aplicada**: 3,395 facturas
- **Valor total**: $17,178,883,201.00
- **Facturas con nota aplicada**: 0 (ninguna)

---

## ❌ Problema Identificado: NOTAS NO SE PUEDEN APLICAR

### Resultado del Análisis
**42 de 42 notas (100%) NO pueden aplicarse a ninguna factura**

**Razón principal**: No se encuentran facturas del mismo cliente y producto

---

## 🔍 Análisis Técnico del Problema

### Problema 1: Código de Producto Vacío en Facturas

Al inspeccionar los datos reales, encontramos:

#### Ejemplo de Factura:
```
numero_factura: FME152106
producto: GESTACION REEMPLAZO ESPECIAL PDO
codigo_producto: "" (VACÍO)
nit_cliente: 811037781
```

#### Ejemplo de Nota:
```
numero_nota: NAG11
codigo_producto: CERDAS LACT PRIMERIZAS PLUS PDO
nit_cliente: 811037781
```

**El campo `codigo_producto` en las facturas está VACÍO**, mientras que las notas sí tienen este campo poblado.

### Problema 2: Nombres de Productos No Coinciden

Incluso comparando por nombre de producto, encontramos discrepancias:

| Cliente | Factura (nombre producto) | Nota (código producto) | ¿Coincide? |
|---------|---------------------------|------------------------|------------|
| 811037781 | CERDAS LACTANCIA PRIMERIZAS ESPECIAL | CERDAS LACT PRIMERIZAS PLUS PDO | ❌ NO |
| 811037781 | GESTACION REEMPLAZO ESPECIAL PDO | PACA SUELTAS PDO X 1 KG | ❌ NO |
| 811037781 | (sin productos de perros/gatos) | CIPACAN CROQUETAS POLLO X 30 KG | ❌ NO |

---

## 📝 Por Qué NO Se Aplican las Notas

El sistema verifica 4 condiciones para aplicar una nota:

1. ✅ **Cliente (NIT) coincide** - Esta condición SÍ se cumple en muchos casos
2. ❌ **Producto (código) coincide** - Esta condición FALLA porque:
   - Campo `codigo_producto` en facturas está vacío
   - Nombres de productos son diferentes
3. ⚠️  **Cantidad nota ≤ Cantidad factura** - No se puede verificar sin match de producto
4. ⚠️  **Valor nota ≤ Valor factura** - No se puede verificar sin match de producto

**Conclusión**: Las condiciones 1 y 2 son prerequisitos. Si el producto no coincide, ni siquiera se evalúan las condiciones de cantidad y valor.

---

## 💡 Ejemplos Detallados

### Ejemplo 1: Cliente 811037781 - MUNDIAL DE GRANOS Y PANELAS

#### Nota Pendiente:
```
Nota: NAG11
Producto: CERDAS LACT PRIMERIZAS PLUS PDO
Cantidad: -16.0
Valor: $-1,499,755.00
```

#### Facturas Disponibles del Mismo Cliente:
```
1. Factura FME152106
   Producto: GESTACION REEMPLAZO ESPECIAL PDO
   Cantidad: 800.0, Valor: $1,382,207.00

2. Factura FME152106
   Producto: CERDAS LACTANCIA ESPECIAL PDO
   Cantidad: 2400.0, Valor: $4,633,339.00

3. Factura FME152106
   Producto: CERDAS LACTANCIA PRIMERIZAS ESPECIAL
   Cantidad: 400.0, Valor: $820,607.00
```

**Resultado**: ❌ NO SE APLICA

**Razón**: Aunque existe una factura con producto similar ("CERDAS LACTANCIA PRIMERIZAS ESPECIAL" vs "CERDAS LACT PRIMERIZAS PLUS PDO"), los nombres NO son idénticos y el sistema requiere coincidencia exacta.

---

### Ejemplo 2: Cliente 890900608 - ALMACENES EXITO

#### Notas Pendientes (6 notas):
```
1. Nota NPE507 - LOMO DE CERDO: $-645,000.00
2. Nota NPE507 - PIERNA CERDO* CORRIENTE: $-2,138,080.00
3. Nota NPE507 - COSTILLA CERDO: $-1,672,800.00
4. Nota NPE507 - PAPADA: $-219,000.00
5. Nota NPE507 - ESPINAZO CERDO: $-412,720.00
6. Nota NPE507 - LOMO CERDO DESCARNADO: $-4,653,360.00
```

**Facturas Disponibles**: No se encontraron facturas de este cliente sin nota aplicada.

**Resultado**: ❌ NO SE PUEDE APLICAR

**Razón**: No hay facturas disponibles de este cliente que no tengan ya una nota aplicada, O las facturas no existen en la base de datos para el rango de fechas procesado.

---

## 🔧 Causas Raíz del Problema

### 1. Proceso de Carga de Facturas
El campo `codigo_producto` no se está poblando correctamente al registrar facturas.

**Código relevante**: `backend/core/notas_credito_manager.py`, método `registrar_factura()` (línea 413-485)

```python
codigo_producto = str(factura_transformada.get('codigo_producto_api', '')).strip()
```

Si `codigo_producto_api` viene vacío del procesador de Excel, se guarda vacío en la BD.

### 2. Transformación de Datos de la API
Las facturas y notas provienen de fuentes diferentes o usan nomenclaturas diferentes para los productos.

### 3. Sin Normalización de Nombres
No existe un proceso de normalización o mapeo entre nombres de productos de facturas y notas.

---

## ✅ Posibles Soluciones

### Solución 1: Poblar el Código de Producto en Facturas (RECOMENDADA)

**Objetivo**: Asegurar que el campo `codigo_producto` en facturas tenga el mismo valor que en las notas.

**Pasos**:
1. Revisar el proceso de transformación de facturas (ExcelProcessor)
2. Verificar que el campo `codigo_producto_api` se esté extrayendo correctamente
3. Si no existe en el Excel, usar el nombre del producto como código
4. Re-procesar las facturas históricas con el código corregido

**Ventajas**:
- Solución permanente
- Respeta la lógica actual del sistema
- No requiere cambios en la lógica de aplicación

### Solución 2: Match Flexible por Nombre de Producto

**Objetivo**: Permitir coincidencia aproximada de nombres de productos.

**Implementación**:
```python
def productos_coinciden(producto_factura, producto_nota):
    """
    Verifica si dos productos son el mismo usando coincidencia flexible
    """
    # Normalizar: quitar espacios extras, mayúsculas, caracteres especiales
    p1 = normalizar_producto(producto_factura)
    p2 = normalizar_producto(producto_nota)

    # Coincidencia exacta
    if p1 == p2:
        return True

    # Coincidencia parcial (ej: ambos contienen "CERDAS LACTANCIA PRIMERIZAS")
    palabras_clave_p1 = set(p1.split())
    palabras_clave_p2 = set(p2.split())

    # Si 80% de las palabras coinciden
    coincidencias = len(palabras_clave_p1 & palabras_clave_p2)
    total = max(len(palabras_clave_p1), len(palabras_clave_p2))

    return (coincidencias / total) >= 0.8
```

**Ventajas**:
- Permite aplicar notas con nombres similares
- No requiere re-procesar datos históricos

**Desventajas**:
- Riesgo de falsos positivos
- Más complejo de mantener
- Puede aplicar notas a productos incorrectos

### Solución 3: Tabla de Mapeo de Productos

**Objetivo**: Crear una tabla que mapee nombres de productos de facturas a códigos de notas.

**Estructura**:
```sql
CREATE TABLE mapeo_productos (
    nombre_factura TEXT,
    codigo_nota TEXT,
    PRIMARY KEY (nombre_factura, codigo_nota)
);
```

**Ejemplo**:
```sql
INSERT INTO mapeo_productos VALUES
('CERDAS LACTANCIA PRIMERIZAS ESPECIAL', 'CERDAS LACT PRIMERIZAS PLUS PDO'),
('GESTACION REEMPLAZO ESPECIAL PDO', 'GESTACION REEMPLAZO PLUS PDO');
```

**Ventajas**:
- Control preciso sobre qué productos se mapean
- Evita falsos positivos
- Auditable y modificable

**Desventajas**:
- Requiere mantenimiento manual
- Necesita poblar la tabla inicialmente

---

## 📊 Resumen Ejecutivo

### Estado Actual
- ❌ **0% de notas pueden aplicarse automáticamente**
- 💰 **$24.1M en notas pendientes bloqueadas**
- 📄 **3,395 facturas disponibles sin poder usar**

### Causa Principal
El campo `codigo_producto` en las facturas está vacío, impidiendo que el sistema pueda hacer el match con las notas de crédito.

### Recomendación
**Solución 1**: Corregir el proceso de carga de facturas para poblar correctamente el campo `codigo_producto`. Esto es la solución más limpia y sostenible.

---

## 🚀 Próximos Pasos Sugeridos

1. **Inmediato**: Verificar el origen de las facturas y cómo se extrae el código de producto
2. **Corto plazo**: Implementar Solución 1 (poblar código de producto)
3. **Mediano plazo**: Re-procesar facturas históricas con códigos corregidos
4. **Opcional**: Implementar Solución 3 (tabla de mapeo) como respaldo para casos edge

---

## 📝 Notas Técnicas

### Cómo Ejecutar este Análisis

```bash
cd backend
python3 test_aplicacion_notas_bd.py --db /home/user/cipa/data/notas_credito.db
```

### Archivos Relevantes

- `backend/test_aplicacion_notas_bd.py` - Script de análisis
- `backend/core/notas_credito_manager.py` - Lógica de aplicación de notas
- `backend/core/business_rules.py` - Reglas de negocio
- `/home/user/cipa/data/notas_credito.db` - Base de datos analizada

---

**Generado por**: Test de Aplicación de Notas v2.0
**Fecha**: 2025-12-09
