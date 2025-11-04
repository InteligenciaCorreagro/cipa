import { useQuery } from '@tanstack/react-query'
import { notasApi, aplicacionesApi } from '@/services/api'

export function useNotas(params?: {
  estado?: string
  nit_cliente?: string
  fecha_desde?: string
  fecha_hasta?: string
  limite?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['notas', params],
    queryFn: () => notasApi.getNotas(params),
  })
}

export function useNota(id: number) {
  return useQuery({
    queryKey: ['nota', id],
    queryFn: () => notasApi.getNota(id),
    enabled: !!id,
  })
}

export function useNotasPorEstado() {
  return useQuery({
    queryKey: ['notas-por-estado'],
    queryFn: () => notasApi.getNotasPorEstado(),
  })
}

export function useEstadisticas() {
  return useQuery({
    queryKey: ['estadisticas'],
    queryFn: () => notasApi.getEstadisticas(),
  })
}

export function useAplicaciones(numeroNota: string) {
  return useQuery({
    queryKey: ['aplicaciones', numeroNota],
    queryFn: () => aplicacionesApi.getAplicaciones(numeroNota),
    enabled: !!numeroNota,
  })
}
