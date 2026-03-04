import { test, expect } from '@playwright/test'

test('carga facturas sin pantalla en blanco', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'test-token')
    localStorage.setItem('user', JSON.stringify({ username: 'demo', rol: 'viewer' }))
  })

  await page.route('**/api/facturas/estadisticas*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        facturas_validas: 1,
        facturas_registrables: 1,
        facturas_no_registrables: 0,
        facturas_rechazadas: 0,
        total_aplicado: 0,
        valor_total_facturado: 200000,
      }),
    })
  })

  await page.route('**/api/facturas*', async (route) => {
    if (route.request().url().includes('/api/facturas/estadisticas')) {
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 1,
            numero_factura: 'F-1',
            codigo_factura: 'F-1',
            fecha_factura: '2026-01-10',
            nit_cliente: '900123',
            nombre_cliente: 'Cliente Demo',
            codigo_producto: 'P-1',
            nombre_producto: 'Producto',
            cantidad_original: 10,
            cantidad_restante: 10,
            valor_total: 200000,
            valor_restante: 200000,
            registrable: 1,
            total_repeticiones: 1,
            suma_total_repeticiones: 200000,
          },
        ],
        total: 1,
      }),
    })
  })

  await page.goto('/facturas')

  await expect(page.getByRole('heading', { name: 'Facturas' })).toBeVisible()
  await expect(page.getByText('F-1')).toBeVisible()
  await expect(page.locator('body')).not.toHaveText('')
})
