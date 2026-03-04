import { useCallback, useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, Badge } from '@/components/ui/table'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { aplicacionesSistemaApi } from '@/services/api'
import { CheckCircle, Clock, Plus, RefreshCw } from 'lucide-react'
import type { AplicacionSistema } from '@/types'
import { useAuthStore } from '@/store/authStore'

export default function AplicacionesSistemaPage() {
  const user = useAuthStore((state) => state.user)
  const canWrite = user?.rol === 'admin' || user?.rol === 'editor'
  const [items, setItems] = useState<AplicacionSistema[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({ estado: '', search: '' })
  const [form, setForm] = useState<{
    nombre: string
    version: string
    fecha_instalacion: string
    estado: 'ACTIVA' | 'INACTIVA'
  }>({
    nombre: '',
    version: '',
    fecha_instalacion: '',
    estado: 'ACTIVA'
  })
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const fetchApps = useCallback(async () => {
    setLoading(true)
    try {
      const response = await aplicacionesSistemaApi.getAplicaciones({
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
    fetchApps()
  }, [fetchApps])

  const totalPages = useMemo(() => Math.ceil(total / pageSize), [total, pageSize])

  const handleCreate = async () => {
    if (!canWrite) return
    await aplicacionesSistemaApi.createAplicacion({
      ...form,
      fecha_instalacion: form.fecha_instalacion || null
    })
    setForm({
      nombre: '',
      version: '',
      fecha_instalacion: '',
      estado: 'ACTIVA'
    })
    setPage(0)
    fetchApps()
  }

  const columns = [
    {
      key: 'nombre',
      label: 'Aplicación',
      render: (item: AplicacionSistema) => (
        <div>
          <div className="font-semibold text-gray-900">{item.nombre}</div>
          <div className="text-xs text-gray-500">v{item.version}</div>
        </div>
      )
    },
    {
      key: 'estado',
      label: 'Estado',
      align: 'center' as const,
      render: (item: AplicacionSistema) => (
        <Badge variant={item.estado === 'ACTIVA' ? 'success' : 'danger'}>
          {item.estado === 'ACTIVA' ? <CheckCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
          {item.estado}
        </Badge>
      )
    },
    {
      key: 'instalacion',
      label: 'Instalación',
      render: (item: AplicacionSistema) => (
        <span className="text-sm text-gray-700">{item.fecha_instalacion || 'N/D'}</span>
      )
    },
    {
      key: 'uso',
      label: 'Uso',
      align: 'right' as const,
      render: (item: AplicacionSistema) => (
        <span className="font-semibold text-gray-900">{item.uso_total || 0}</span>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Aplicaciones</h1>
          <p className="text-gray-500 mt-1">Estado y métricas de uso</p>
        </div>
        <Button onClick={fetchApps} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      {canWrite && (
      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>Registrar aplicación</CardTitle>
          <CardDescription>Nombre, versión y fecha de instalación</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <Label>Nombre</Label>
            <Input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          </div>
          <div className="space-y-2">
            <Label>Versión</Label>
            <Input value={form.version} onChange={(e) => setForm({ ...form, version: e.target.value })} />
          </div>
          <div className="space-y-2">
            <Label>Fecha instalación</Label>
            <Input type="date" value={form.fecha_instalacion} onChange={(e) => setForm({ ...form, fecha_instalacion: e.target.value })} />
          </div>
          <div className="space-y-2">
            <Label>Estado</Label>
            <Select value={form.estado} onValueChange={(value) => setForm({ ...form, estado: value as 'ACTIVA' | 'INACTIVA' })}>
              <SelectTrigger>
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVA">Activa</SelectItem>
                <SelectItem value="INACTIVA">Inactiva</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleCreate} className="gap-2 md:col-span-4">
            <Plus className="h-4 w-4" />
            Guardar
          </Button>
        </CardContent>
      </Card>
      )}

      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Buscar por nombre o estado</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input placeholder="Buscar" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
          <Select value={filters.estado || 'ALL'} onValueChange={(value) => setFilters({ ...filters, estado: value === 'ALL' ? '' : value })}>
            <SelectTrigger>
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todas</SelectItem>
              <SelectItem value="ACTIVA">Activa</SelectItem>
              <SelectItem value="INACTIVA">Inactiva</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={() => { setPage(0); fetchApps() }} variant="outline">
            Aplicar
          </Button>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>Listado</CardTitle>
          <CardDescription>{total} registros</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table columns={columns} data={items} keyExtractor={(item) => String(item.id)} bordered hoverable />
          <div className="flex items-center justify-between p-4">
            <div className="text-sm text-gray-500">
              Página {page + 1} de {totalPages || 1}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
                Anterior
              </Button>
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
