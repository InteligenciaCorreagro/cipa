import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Badge } from '@/components/ui/table'
import { DateRangePicker } from '@/components/ui/datepicker'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { FileText, Search, Filter, Download, Plus, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react'
import { api } from '@/services/api'

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
  valor_total: number
  saldo_pendiente: number
  estado: 'Pendiente' | 'Aplicado' | 'Rechazado' | 'Parcial'
  fecha_creacion: string
}

export default function NotasPage() {
  const navigate = useNavigate()
  const [notas, setNotas] = useState<NotaCredito[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [estadoFilter, setEstadoFilter] = useState<string>('todos')
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({})

  useEffect(() => {
    fetchNotas()
  }, [])

  const fetchNotas = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/notas')
      setNotas(response.data.items || response.data || [])
    } catch (error) {
      console.error('Error al cargar notas:', error)
    } finally {
      setLoading(false)
    }
  }

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
      key: 'estado',
      label: 'Estado',
      align: 'center' as const,
      render: (nota: NotaCredito) => {
        const variants: Record<string, { variant: any; icon: any }> = {
          'Aplicado': { variant: 'success', icon: CheckCircle },
          'Pendiente': { variant: 'warning', icon: Clock },
          'Rechazado': { variant: 'danger', icon: XCircle },
          'Parcial': { variant: 'info', icon: AlertCircle }
        }
        const config = variants[nota.estado] || { variant: 'default', icon: FileText }
        const Icon = config.icon
        
        return (
          <Badge variant={config.variant}>
            <Icon className="w-3.5 h-3.5" />
            {nota.estado}
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
        <Button 
          onClick={() => navigate('/notas/nueva')}
          className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg shadow-emerald-600/30"
        >
          <Plus className="mr-2 h-4 w-4" />
          Nueva Nota
        </Button>
      </div>

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
                  <SelectItem value="Pendiente">Pendiente</SelectItem>
                  <SelectItem value="Aplicado">Aplicado</SelectItem>
                  <SelectItem value="Rechazado">Rechazado</SelectItem>
                  <SelectItem value="Parcial">Parcial</SelectItem>
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
                {filteredNotas.filter(n => n.estado === 'Aplicado').length}
              </p>
            </div>
          </div>
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
            onRowClick={(nota) => navigate(`/notas/${nota.id}`)}
            loading={loading}
            emptyMessage="No se encontraron notas con los filtros aplicados"
            hoverable
            bordered
          />
        </CardContent>
      </Card>
    </div>
  )
}