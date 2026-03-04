# Reporte técnico: blank page en módulo Facturas

## Resumen
Al ingresar al módulo de facturas, la vista quedaba en blanco debido a una excepción de JavaScript durante el renderizado. El error se disparaba al intentar formatear fechas inválidas en la tabla.

## Root cause
En la fila de la tabla se ejecutaba `new Date(fecha_factura).toLocaleDateString('es-CO')`. Cuando `fecha_factura` venía vacío o nulo desde la API, `new Date(value)` resultaba en `Invalid Date` y `toLocaleDateString` lanzaba `RangeError: Invalid time value`, lo que rompía el render y dejaba la pantalla en blanco.

## Trazas de consola
Ejemplo de error reproducido al cargar una factura con fecha inválida:

- `RangeError: Invalid time value`
- `at Date.toLocaleDateString (<anonymous>)`
- `at FacturasPage.tsx (render de columna fecha)`

## Errores de red
El módulo hacía `GET /api/facturas` y `GET /api/facturas/estadisticas`. Cuando estos endpoints fallaban, el estado no manejaba el error y la UI podía quedar sin contenido. Se añadió manejo de error visible para evitar pantalla en blanco.

## Resolución aplicada
- Se agregó un formateador seguro de fecha que devuelve `'-'` para fechas inválidas.
- Se incluyó manejo de errores de red con banner informativo.
- Se simplificó el UI para minimizar estados inconsistentes y evitar throws en render.

## Verificación
- Prueba unitaria garantiza que la página renderiza incluso con `fecha_factura` inválida.
- Prueba E2E valida que el módulo carga sin pantalla en blanco en Chromium, Firefox, WebKit y Edge.

## Archivos relevantes
- `src/pages/FacturasPage.tsx`
- `src/pages/__tests__/FacturasPage.test.tsx`
- `tests/e2e/facturas.spec.ts`
