import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Badge } from '@/components/ui/table'
import { DateRangePicker } from '@/components/ui/datepicker'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FileText, Search, Filter, Download, Plus, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react'
import { notasApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import DetailModal from '@/components/DetailModal'

// Función para formatear moneda
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

interface NotaCredito {
  id: number
  numero_nota: string
  fecha_nota: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  valor_total: number
  saldo_pendiente: number
  cantidad: number
  cantidad_pendiente: number
  estado: 'PENDIENTE' | 'APLICADA' | 'NO_APLICADA'
  es_agente?: number
}

interface NotaNoAplicada {
  id: number
  numero_nota: string
  numero_factura: string
  motivo: string
  detalle?: string
  fecha_registro: string
}

export default function NotasPage() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const canWrite = user?.rol === 'admin' || user?.rol === 'editor'
  const [notas, setNotas] = useState<NotaCredito[]>([])
  const [noAplicadas, setNoAplicadas] = useState<NotaNoAplicada[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('todos')
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [notification, setNotification] = useState<string | null>(null)
  const [lastCounts, setLastCounts] = useState({ pendientes: 0, aplicadas: 0, noAplicadas: 0 })
  const [showForm, setShowForm] = useState(false)
  const [selectedNota, setSelectedNota] = useState<NotaCredito | null>(null)
  const [notaForm, setNotaForm] = useState({
    numero_nota: '',
    fecha_nota: '',
    nit_cliente: '',
    nombre_cliente: '',
    codigo_producto: '',
    nombre_producto: '',
    cantidad: '',
    valor_total: '',
    es_agente: false,
  })
  const [aplicarForm, setAplicarForm] = useState({
    nota_id: '',
    numero_factura: '',
    codigo_producto: '',
    indice_linea: '0',
  })

  useEffect(() => {
    fetchNotas()
    fetchNoAplicadas()
    const interval = setInterval(() => {
      fetchNotas(true)
      fetchNoAplicadas()
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchNotas = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true)
      }
      const response = await notasApi.getNotas()
      const items = response.items || []
      setNotas(items)
    } catch (error) {
      console.error('Error al cargar notas:', error)
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }

  const fetchNoAplicadas = async () => {
    try {
      const response = await notasApi.getNoAplicadas({ limite: 10, offset: 0 })
      setNoAplicadas(response.items || [])
    } catch (error) {
      console.error('Error al cargar no aplicadas:', error)
    }
  }

  const counts = useMemo(() => {
    const pendientes = notas.filter((nota) => nota.estado === 'PENDIENTE').length
    const aplicadas = notas.filter((nota) => nota.estado === 'APLICADA').length
    const noAplicadasCount = notas.filter((nota) => nota.estado === 'NO_APLICADA').length
    return { pendientes, aplicadas, noAplicadas: noAplicadasCount }
  }, [notas])

  useEffect(() => {
    if (
      counts.pendientes !== lastCounts.pendientes ||
      counts.aplicadas !== lastCounts.aplicadas ||
      counts.noAplicadas !== lastCounts.noAplicadas
    ) {
      setNotification('Se detectaron cambios en el estado de las notas crédito')
      setLastCounts(counts)
      const timeout = setTimeout(() => setNotification(null), 4000)
      return () => clearTimeout(timeout)
    }
  }, [counts, lastCounts])

  // Filtrar notas
  const filteredNotas = notas.filter((nota) => {
    const matchSearch = 
      nota.numero_nota.toLowerCase().includes(searchTerm.toLowerCase()) ||
      nota.nombre_cliente.toLowerCase().includes(searchTerm.toLowerCase()) ||
      nota.nit_cliente.includes(searchTerm)

    const matchEstado = estadoFilter === 'todos' || nota.estado === estadoFilter

    const matchDateRange = 
      (!dateRange.from || new Date(nota.fecha_nota) >= dateRange.from) &&
      (!dateRange.to || new Date(nota.fecha_nota) <= dateRange.to)

    return matchSearch && matchEstado && matchDateRange
  })

  // Columnas de la tabla
  const columns = [
    {
      key: 'numero_nota',
      label: 'Número de Nota',
      render: (nota: NotaCredito) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{nota.numero_nota}</p>
            <p className="text-xs text-gray-500">
              {new Date(nota.fecha_nota).toLocaleDateString('es-CO', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
              })}
            </p>
          </div>
        </div>
      ),
    },
    {
      key: 'cliente',
      label: 'Cliente',
      render: (nota: NotaCredito) => (
        <div>
          <p className="font-medium text-gray-900">{nota.nombre_cliente}</p>
          <p className="text-xs text-gray-500 font-mono">{nota.nit_cliente}</p>
        </div>
      ),
    },
    {
      key: 'producto',
      label: 'Producto',
      render: (nota: NotaCredito) => (
        <div>
          <p className="font-medium text-gray-900">{nota.nombre_producto}</p>
          <p className="text-xs text-gray-500 font-mono">{nota.codigo_producto}</p>
        </div>
      ),
    },
    {
      key: 'valor_total',
      label: 'Valor Total',
      align: 'right' as const,
      render: (nota: NotaCredito) => (
        <span className="font-semibold text-gray-900">
          {formatCurrency(Math.abs(nota.valor_total))}
        </span>
      ),
    },
    {
      key: 'saldo_pendiente',
      label: 'Saldo Pendiente',
      align: 'right' as const,
      render: (nota: NotaCredito) => (
        <span className={`font-bold ${
          nota.saldo_pendiente > 0 ? 'text-orange-600' : 'text-emerald-600'
        }`}>
          {formatCurrency(Math.abs(nota.saldo_pendiente))}
        </span>
      ),
    },
    {
      key: 'agente',
      label: 'Agente',
      align: 'center' as const,
      render: (nota: NotaCredito) => (
        <Badge variant={nota.es_agente ? 'info' : 'default'}>
          {nota.es_agente ? 'Agente' : 'No'}
        </Badge>
      ),
    },
    {
      key: 'estado',
      label: 'Estado',
      align: 'center' as const,
      render: (nota: NotaCredito) => {
        const variants: Record<string, { variant: 'success' | 'warning' | 'danger' | 'default' | 'info'; icon: typeof CheckCircle; label: string }> = {
          APLICADA: { variant: 'success', icon: CheckCircle, label: 'Aplicada' },
          PENDIENTE: { variant: 'warning', icon: Clock, label: 'Pendiente' },
          NO_APLICADA: { variant: 'danger', icon: XCircle, label: 'No aplicada' }
        }
        const config = variants[nota.estado] || { variant: 'default', icon: FileText, label: nota.estado }
        const Icon = config.icon
        
        return (
          <Badge variant={config.variant}>
            <Icon className="w-3.5 h-3.5" />
            {config.label}
          </Badge>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Notas de Crédito</h1>
          <p className="text-gray-500 mt-1">
            Gestiona y consulta las notas de crédito del sistema
          </p>
        </div>
        {canWrite ? (
          <Button
            onClick={() => setShowForm((prev) => !prev)}
            className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg shadow-emerald-600/30"
          >
            <Plus className="mr-2 h-4 w-4" />
            {showForm ? 'Ocultar Formularios' : 'Nueva Nota'}
          </Button>
        ) : (
          <Badge variant="info">Modo consulta</Badge>
        )}
      </div>

      {notification && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-700">
          <RefreshCw className="h-4 w-4" />
          <span className="text-sm">{notification}</span>
        </div>
      )}

      {/* Filtros */}
      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white pb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <CardTitle className="text-lg">Filtros de Búsqueda</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Búsqueda */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Número, cliente o NIT..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 h-11 border-2 focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Estado */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Estado</label>
              <Select value={estadoFilter} onValueChange={setEstadoFilter}>
                <SelectTrigger className="h-11 border-2 focus:border-emerald-500">
                  <SelectValue placeholder="Todos los estados" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos los estados</SelectItem>
                  <SelectItem value="PENDIENTE">Pendiente</SelectItem>
                  <SelectItem value="APLICADA">Aplicada</SelectItem>
                  <SelectItem value="NO_APLICADA">No aplicada</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Rango de Fechas */}
            <div className="space-y-2 lg:col-span-2">
              <label className="text-sm font-medium text-gray-700">Rango de Fechas</label>
              <DateRangePicker
                dateRange={dateRange}
                onDateRangeChange={setDateRange}
                placeholder="Seleccionar rango de fechas"
              />
            </div>
          </div>

          {/* Stats rápidas */}
          <div className="grid gap-4 md:grid-cols-4 mt-6 pt-6 border-t">
            <div className="text-center">
              <p className="text-sm text-gray-500">Total Notas</p>
              <p className="text-2xl font-bold text-gray-900">{filteredNotas.length}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">Valor Total</p>
              <p className="text-2xl font-bold text-emerald-600">
                {formatCurrency(filteredNotas.reduce((sum, n) => sum + Math.abs(n.valor_total), 0))}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">Saldo Pendiente</p>
              <p className="text-2xl font-bold text-orange-600">
                {formatCurrency(filteredNotas.reduce((sum, n) => sum + Math.abs(n.saldo_pendiente), 0))}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">Aplicadas</p>
              <p className="text-2xl font-bold text-blue-600">
                {filteredNotas.filter(n => n.estado === 'APLICADA').length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {showForm && canWrite && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-0 shadow-md">
            <CardHeader>
              <CardTitle>Registrar Nota Crédito</CardTitle>
              <CardDescription>Registro manual con validación en tiempo real</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Input placeholder="Número nota" value={notaForm.numero_nota} onChange={(e) => setNotaForm({ ...notaForm, numero_nota: e.target.value })} />
                <Input type="date" value={notaForm.fecha_nota} onChange={(e) => setNotaForm({ ...notaForm, fecha_nota: e.target.value })} />
                <Input placeholder="NIT cliente" value={notaForm.nit_cliente} onChange={(e) => setNotaForm({ ...notaForm, nit_cliente: e.target.value })} />
                <Input placeholder="Nombre cliente" value={notaForm.nombre_cliente} onChange={(e) => setNotaForm({ ...notaForm, nombre_cliente: e.target.value })} />
                <Input placeholder="Código producto" value={notaForm.codigo_producto} onChange={(e) => setNotaForm({ ...notaForm, codigo_producto: e.target.value })} />
                <Input placeholder="Nombre producto" value={notaForm.nombre_producto} onChange={(e) => setNotaForm({ ...notaForm, nombre_producto: e.target.value })} />
                <Input placeholder="Cantidad" value={notaForm.cantidad} onChange={(e) => setNotaForm({ ...notaForm, cantidad: e.target.value })} />
                <Input placeholder="Valor total" value={notaForm.valor_total} onChange={(e) => setNotaForm({ ...notaForm, valor_total: e.target.value })} />
              </div>
              <div className="flex items-center justify-between">
                <Select value={notaForm.es_agente ? 'si' : 'no'} onValueChange={(value) => setNotaForm({ ...notaForm, es_agente: value === 'si' })}>
                  <SelectTrigger className="h-10 w-48">
                    <SelectValue placeholder="Es agente" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="si">Agente</SelectItem>
                    <SelectItem value="no">No agente</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  onClick={async () => {
                    if (!canWrite) return
                    await notasApi.createNota({
                      numero_nota: notaForm.numero_nota,
                      fecha_nota: notaForm.fecha_nota,
                      nit_cliente: notaForm.nit_cliente,
                      nombre_cliente: notaForm.nombre_cliente,
                      codigo_producto: notaForm.codigo_producto,
                      nombre_producto: notaForm.nombre_producto,
                      cantidad: Number(notaForm.cantidad || 0),
                      valor_total: Number(notaForm.valor_total || 0),
                      es_agente: notaForm.es_agente ? 1 : 0,
                    })
                    setNotaForm({
                      numero_nota: '',
                      fecha_nota: '',
                      nit_cliente: '',
                      nombre_cliente: '',
                      codigo_producto: '',
                      nombre_producto: '',
                      cantidad: '',
                      valor_total: '',
                      es_agente: false,
                    })
                    fetchNotas()
                  }}
                >
                  Registrar
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-md">
            <CardHeader>
              <CardTitle>Aplicar Nota a Factura</CardTitle>
              <CardDescription>Aplicación directa a línea de factura</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Input placeholder="ID Nota" value={aplicarForm.nota_id} onChange={(e) => setAplicarForm({ ...aplicarForm, nota_id: e.target.value })} />
                <Input placeholder="Número factura" value={aplicarForm.numero_factura} onChange={(e) => setAplicarForm({ ...aplicarForm, numero_factura: e.target.value })} />
                <Input placeholder="Código producto" value={aplicarForm.codigo_producto} onChange={(e) => setAplicarForm({ ...aplicarForm, codigo_producto: e.target.value })} />
                <Input placeholder="Índice línea" value={aplicarForm.indice_linea} onChange={(e) => setAplicarForm({ ...aplicarForm, indice_linea: e.target.value })} />
              </div>
              <Button
                onClick={async () => {
                  if (!canWrite) return
                  await notasApi.aplicarNota({
                    nota_id: Number(aplicarForm.nota_id),
                    numero_factura: aplicarForm.numero_factura,
                    codigo_producto: aplicarForm.codigo_producto,
                    indice_linea: Number(aplicarForm.indice_linea || 0),
                  })
                  setAplicarForm({
                    nota_id: '',
                    numero_factura: '',
                    codigo_producto: '',
                    indice_linea: '0',
                  })
                  fetchNotas()
                  fetchNoAplicadas()
                }}
                className="w-full"
              >
                Aplicar Nota
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="border-0 shadow-md">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <CardTitle>Notas No Aplicadas</CardTitle>
          <CardDescription>Motivos recientes de no aplicación</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {noAplicadas.length === 0 && (
            <p className="text-sm text-gray-500">Sin registros recientes</p>
          )}
          {noAplicadas.map((item) => (
            <div key={item.id} className="flex items-start justify-between border rounded-lg p-3">
              <div>
                <p className="font-medium">{item.numero_nota}</p>
                <p className="text-xs text-gray-500">{item.motivo}</p>
                {item.detalle && <p className="text-xs text-gray-400">{item.detalle}</p>}
              </div>
              <div className="text-right text-xs text-gray-500">
                <p>{item.numero_factura || 'Sin factura'}</p>
                <p>{new Date(item.fecha_registro).toLocaleString('es-CO')}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Tabla */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Listado de Notas</CardTitle>
              <CardDescription>
                {filteredNotas.length} {filteredNotas.length === 1 ? 'nota encontrada' : 'notas encontradas'}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Exportar
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={filteredNotas}
            keyExtractor={(nota) => nota.id.toString()}
            onRowClick={(nota) => setSelectedNota(nota)}
            loading={loading}
            emptyMessage="No se encontraron notas con los filtros aplicados"
            hoverable
            bordered
          />
        </CardContent>
      </Card>
      <DetailModal
        open={!!selectedNota}
        title={`Detalle nota ${selectedNota?.numero_nota ?? ''}`}
        description="Información principal y acceso al detalle completo"
        onClose={() => setSelectedNota(null)}
      >
        {selectedNota ? (
          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs text-emerald-600">Cliente</p>
                <p className="text-sm font-semibold text-emerald-900">{selectedNota.nombre_cliente}</p>
              </div>
              <div>
                <p className="text-xs text-emerald-600">NIT</p>
                <p className="text-sm font-semibold text-emerald-900">{selectedNota.nit_cliente}</p>
              </div>
              <div>
                <p className="text-xs text-emerald-600">Producto</p>
                <p className="text-sm font-semibold text-emerald-900">{selectedNota.nombre_producto}</p>
              </div>
              <div>
                <p className="text-xs text-emerald-600">Código</p>
                <p className="text-sm font-semibold text-emerald-900">{selectedNota.codigo_producto}</p>
              </div>
              <div>
                <p className="text-xs text-emerald-600">Valor total</p>
                <p className="text-sm font-semibold text-emerald-900">{formatCurrency(Math.abs(selectedNota.valor_total))}</p>
              </div>
              <div>
                <p className="text-xs text-emerald-600">Saldo pendiente</p>
                <p className="text-sm font-semibold text-emerald-900">{formatCurrency(Math.abs(selectedNota.saldo_pendiente))}</p>
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={() => navigate(`/notas/${selectedNota.id}`)}>Ver detalle completo</Button>
            </div>
          </div>
        ) : null}
      </DetailModal>
    </div>
  )
}
