import { useQuery } from '@tanstack/react-query'
import { facturasApi } from '@/services/api'

export function useEstadisticasFacturas() {
  return useQuery({
    queryKey: ['facturas-estadisticas'],
    queryFn: () => facturasApi.getEstadisticas(),
    refetchInterval: 60000, // Refetch cada 60 segundos
  })
}

export function useFacturas(params?: {
  estado?: string
  nit_cliente?: string
  fecha_desde?: string
  fecha_hasta?: string
  es_valida?: boolean
  limite?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['facturas', params],
    queryFn: () => facturasApi.getFacturas(params),
  })
}

export function useFactura(id: number) {
  return useQuery({
    queryKey: ['factura', id],
    queryFn: () => facturasApi.getFactura(id),
    enabled: !!id,
  })
}

export function useTransacciones(params?: {
  fecha_desde?: string
  fecha_hasta?: string
  nit_cliente?: string
  codigo_producto?: string
  tipo_inventario?: string
  tiene_nota_credito?: boolean
  estado?: string
  limite?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['transacciones', params],
    queryFn: () => facturasApi.getTransacciones(params),
  })
}
