import { useCallback, useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table } from '@/components/ui/table'
import { logsApi } from '@/services/api'
import { Filter, RefreshCw } from 'lucide-react'
import type { LogEntry } from '@/types'

export default function LogsPage() {
  const [items, setItems] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    entidad: '',
    accion: '',
    usuario: '',
    fecha_desde: '',
    fecha_hasta: '',
    search: ''
  })
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const pageSize = 25

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const response = await logsApi.getLogs({
        ...filters,
        limite: pageSize,
        offset: page * pageSize
      })
      setItems(response.items || [])
      setTotal(response.total || 0)
    } finally {
      setLoading(false)
    }
  }, [filters, page, pageSize])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  const totalPages = useMemo(() => Math.ceil(total / pageSize), [total, pageSize])
  const pageNumbers = useMemo(() => {
    const pages: number[] = []
    const start = Math.max(1, page + 1 - 2)
    const end = Math.min(totalPages || 1, page + 1 + 2)
    for (let i = start; i <= end; i += 1) {
      pages.push(i)
    }
    return pages
  }, [page, totalPages])

  const columns = [
    {
      key: 'fecha',
      label: 'Fecha',
      render: (item: LogEntry) => <span className="text-sm text-gray-700">{item.fecha_registro}</span>
    },
    {
      key: 'entidad',
      label: 'Entidad',
      render: (item: LogEntry) => <span className="font-medium text-gray-900">{item.entidad}</span>
    },
    {
      key: 'accion',
      label: 'Acción',
      render: (item: LogEntry) => <span className="text-sm text-gray-700">{item.accion}</span>
    },
    {
      key: 'usuario',
      label: 'Usuario',
      render: (item: LogEntry) => <span className="text-sm text-gray-700">{item.usuario || 'N/D'}</span>
    },
    {
      key: 'payload',
      label: 'Detalle',
      render: (item: LogEntry) => (
        <span className="text-xs text-gray-500 break-all">{item.payload || ''}</span>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Logs del Sistema</h1>
          <p className="text-gray-500 mt-1">Auditoría de acciones críticas</p>
        </div>
        <Button onClick={fetchLogs} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <CardTitle className="text-lg">Filtros</CardTitle>
          </div>
          <CardDescription>Filtra por entidad, usuario o fecha</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-6 gap-4 pt-6">
          <Input placeholder="Entidad" value={filters.entidad} onChange={(e) => setFilters({ ...filters, entidad: e.target.value })} />
          <Input placeholder="Acción" value={filters.accion} onChange={(e) => setFilters({ ...filters, accion: e.target.value })} />
          <Input placeholder="Usuario" value={filters.usuario} onChange={(e) => setFilters({ ...filters, usuario: e.target.value })} />
          <Input type="date" value={filters.fecha_desde} onChange={(e) => setFilters({ ...filters, fecha_desde: e.target.value })} />
          <Input type="date" value={filters.fecha_hasta} onChange={(e) => setFilters({ ...filters, fecha_hasta: e.target.value })} />
          <Input placeholder="Buscar" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
          <Button onClick={fetchLogs} variant="outline" className="md:col-span-6">
            Aplicar filtros
          </Button>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>Listado</CardTitle>
          <CardDescription>{total} registros</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table columns={columns} data={items} keyExtractor={(item) => String(item.id)} bordered hoverable enablePagination={false} />
          <div className="flex items-center justify-between p-4">
            <div className="text-sm text-gray-500">
              Página {page + 1} de {totalPages || 1}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
                Anterior
              </Button>
              {pageNumbers.map((pageNumber) => (
                <Button
                  key={pageNumber}
                  variant={pageNumber === page + 1 ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setPage(pageNumber - 1)}
                >
                  {pageNumber}
                </Button>
              ))}
              <Button variant="outline" size="sm" onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page + 1 >= totalPages}>
                Siguiente
              </Button>
            </div>
          </div>
          {loading && <div className="p-4 text-sm text-gray-500">Cargando...</div>}
        </CardContent>
      </Card>
    </div>
  )
}
