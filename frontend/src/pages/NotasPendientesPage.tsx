import { useCallback, useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, Badge } from '@/components/ui/table'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { notasPendientesApi } from '@/services/api'
import { Calendar, CheckCircle, Clock, Plus, RefreshCw } from 'lucide-react'
import type { NotaPendiente } from '@/types'
import { useAuthStore } from '@/store/authStore'

const prioridadVariant = (prioridad: string) => {
  if (prioridad === 'alta') return 'danger'
  if (prioridad === 'media') return 'warning'
  return 'default'
}

export default function NotasPendientesPage() {
  const user = useAuthStore((state) => state.user)
  const canWrite = user?.rol === 'admin' || user?.rol === 'editor'
  const [items, setItems] = useState<NotaPendiente[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    estado: '',
    prioridad: '',
    responsable: '',
    fecha_desde: '',
    fecha_hasta: ''
  })
  const [form, setForm] = useState<{
    numero_nota: string
    prioridad: 'alta' | 'media' | 'baja'
    fecha_vencimiento: string
    responsable: string
    estado: 'PENDIENTE' | 'EN_PROGRESO' | 'COMPLETADA'
    descripcion: string
  }>({
    numero_nota: '',
    prioridad: 'media',
    fecha_vencimiento: '',
    responsable: '',
    estado: 'PENDIENTE',
    descripcion: ''
  })
  const [alertas, setAlertas] = useState<{ vencidas: NotaPendiente[]; proximas: NotaPendiente[] }>({
    vencidas: [],
    proximas: []
  })
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const fetchNotas = useCallback(async () => {
    setLoading(true)
    try {
      const response = await notasPendientesApi.getNotas({
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
    fetchNotas()
  }, [fetchNotas])

  useEffect(() => {
    const fetchAlertas = async () => {
      const data = await notasPendientesApi.getAlertas()
      setAlertas(data)
    }
    fetchAlertas()
  }, [])

  const totalPages = useMemo(() => Math.ceil(total / pageSize), [total, pageSize])

  const handleCreate = async () => {
    if (!canWrite) return
    await notasPendientesApi.createNota({
      ...form,
      fecha_vencimiento: form.fecha_vencimiento || null
    })
    setForm({
      numero_nota: '',
      prioridad: 'media',
      fecha_vencimiento: '',
      responsable: '',
      estado: 'PENDIENTE',
      descripcion: ''
    })
    setPage(0)
    fetchNotas()
  }

  const columns = [
    {
      key: 'numero_nota',
      label: 'Nota',
      render: (item: NotaPendiente) => (
        <div className="font-medium text-foreground">{item.numero_nota}</div>
      )
    },
    {
      key: 'prioridad',
      label: 'Prioridad',
      align: 'center' as const,
      render: (item: NotaPendiente) => (
        <Badge variant={prioridadVariant(item.prioridad)}>
          {item.prioridad}
        </Badge>
      )
    },
    {
      key: 'vencimiento',
      label: 'Vencimiento',
      render: (item: NotaPendiente) => (
        <div className="flex items-center gap-2 text-sm text-foreground">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          {item.fecha_vencimiento || 'Sin fecha'}
        </div>
      )
    },
    {
      key: 'responsable',
      label: 'Responsable',
      render: (item: NotaPendiente) => (
        <div className="text-sm text-foreground">{item.responsable || 'Sin asignar'}</div>
      )
    },
    {
      key: 'estado',
      label: 'Estado',
      align: 'center' as const,
      render: (item: NotaPendiente) => (
        <Badge variant={item.estado === 'COMPLETADA' ? 'success' : 'warning'}>
          {item.estado === 'COMPLETADA' ? <CheckCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
          {item.estado}
        </Badge>
      )
    }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Notas Pendientes</h1>
          <p className="text-muted-foreground mt-1 text-sm">Gestion con prioridades y responsables</p>
        </div>
        <Button onClick={fetchNotas} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Vencidas</CardTitle>
            <CardDescription>Requieren accion inmediata</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-destructive">
            {alertas.vencidas.length}
          </CardContent>
        </Card>
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Proximas</CardTitle>
            <CardDescription>Vencen en 7 dias</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-primary">
            {alertas.proximas.length}
          </CardContent>
        </Card>
      </div>

      {canWrite && (
      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>Crear Nota Pendiente</CardTitle>
          <CardDescription>Define prioridad, vencimiento y responsable</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Número de nota</Label>
              <Input value={form.numero_nota} onChange={(e) => setForm({ ...form, numero_nota: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Prioridad</Label>
              <Select value={form.prioridad} onValueChange={(value) => setForm({ ...form, prioridad: value as 'alta' | 'media' | 'baja' })}>
                <SelectTrigger>
                  <SelectValue placeholder="Prioridad" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="alta">Alta</SelectItem>
                  <SelectItem value="media">Media</SelectItem>
                  <SelectItem value="baja">Baja</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Fecha vencimiento</Label>
              <Input type="date" value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>Responsable</Label>
              <Input value={form.responsable} onChange={(e) => setForm({ ...form, responsable: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label>Estado</Label>
              <Select value={form.estado} onValueChange={(value) => setForm({ ...form, estado: value as 'PENDIENTE' | 'EN_PROGRESO' | 'COMPLETADA' })}>
                <SelectTrigger>
                  <SelectValue placeholder="Estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PENDIENTE">Pendiente</SelectItem>
                  <SelectItem value="EN_PROGRESO">En progreso</SelectItem>
                  <SelectItem value="COMPLETADA">Completada</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Descripción</Label>
              <Input value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
            </div>
          </div>
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="h-4 w-4" />
            Registrar
          </Button>
        </CardContent>
      </Card>
      )}

      <Card className="border-0 shadow-md">
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Refina por estado, prioridad o fechas</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Input placeholder="Responsable" value={filters.responsable} onChange={(e) => setFilters({ ...filters, responsable: e.target.value })} />
            <Select value={filters.estado || 'ALL'} onValueChange={(value) => setFilters({ ...filters, estado: value === 'ALL' ? '' : value })}>
            <SelectTrigger>
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="ALL">Todos</SelectItem>
              <SelectItem value="PENDIENTE">Pendiente</SelectItem>
              <SelectItem value="EN_PROGRESO">En progreso</SelectItem>
              <SelectItem value="COMPLETADA">Completada</SelectItem>
            </SelectContent>
          </Select>
            <Select value={filters.prioridad || 'ALL'} onValueChange={(value) => setFilters({ ...filters, prioridad: value === 'ALL' ? '' : value })}>
            <SelectTrigger>
              <SelectValue placeholder="Prioridad" />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="ALL">Todas</SelectItem>
              <SelectItem value="alta">Alta</SelectItem>
              <SelectItem value="media">Media</SelectItem>
              <SelectItem value="baja">Baja</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" value={filters.fecha_desde} onChange={(e) => setFilters({ ...filters, fecha_desde: e.target.value })} />
          <Input type="date" value={filters.fecha_hasta} onChange={(e) => setFilters({ ...filters, fecha_hasta: e.target.value })} />
          <Button onClick={() => { setPage(0); fetchNotas() }} variant="outline" className="md:col-span-5">
            Aplicar filtros
          </Button>
        </CardContent>
      </Card>

      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Listado</CardTitle>
          <CardDescription>{total} registros</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table columns={columns} data={items} keyExtractor={(item) => String(item.id)} bordered hoverable />
          <div className="flex items-center justify-between p-4">
            <div className="text-sm text-muted-foreground">
              Pagina {page + 1} de {totalPages || 1}
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
          {loading && <div className="p-4 text-sm text-muted-foreground">Cargando...</div>}
        </CardContent>
      </Card>
    </div>
  )
}
