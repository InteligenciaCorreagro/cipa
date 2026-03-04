import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import FacturasPage from '@/pages/FacturasPage'
import { facturasApi } from '@/services/api'

vi.mock('@/services/api', () => ({
  facturasApi: {
    getFacturas: vi.fn(),
    getEstadisticas: vi.fn(),
  },
}))

const mockFacturasApi = facturasApi as unknown as {
  getFacturas: ReturnType<typeof vi.fn>
  getEstadisticas: ReturnType<typeof vi.fn>
}

describe('FacturasPage', () => {
  it('renderiza sin errores cuando la fecha es inválida', async () => {
    mockFacturasApi.getFacturas.mockResolvedValue({
      items: [
        {
          id: 1,
          numero_factura: 'F-1',
          codigo_factura: 'F-1',
          fecha_factura: '',
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
    })
    mockFacturasApi.getEstadisticas.mockResolvedValue({
      facturas_validas: 1,
      facturas_registrables: 1,
      facturas_no_registrables: 0,
      facturas_rechazadas: 0,
      total_aplicado: 0,
      valor_total_facturado: 200000,
    })

    render(<FacturasPage />)

    await waitFor(() => {
      expect(screen.getByText('Facturas')).toBeInTheDocument()
    })

    expect(screen.getByText('F-1')).toBeInTheDocument()
  })
})
