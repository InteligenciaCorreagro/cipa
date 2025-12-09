import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, Badge } from '@/components/ui/Table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api } from '@/services/api'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  CheckCircle,
  XCircle,
  Calendar,
  DollarSign,
  ArrowLeft,
  Loader2,
  AlertCircle,
  TrendingUp,
  Clock,
  Users,
  Package,
  Search
} from 'lucide-react'

interface NotaCredito {
  numero_nota: string
  fecha_nota: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  valor_total: number
  cantidad: number
  saldo_pendiente: number
  cantidad_pendiente: number
  estado: string
}

interface Aplicacion {
  numero_nota: string
  numero_factura: string
  fecha_factura: string
  nit_cliente: string
  codigo_producto: string
  valor_aplicado: number
  cantidad_aplicada: number
  fecha_aplicacion: string
}

interface FacturaRechazada {
  numero_factura: string
  fecha_factura: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  tipo_inventario: string
  valor_total: number
  razon_rechazo: string
}

interface Resumen {
  total_notas: number
  total_aplicaciones: number
  total_rechazadas: number
  resumen_notas: {
    total: number
    pendientes: number
    aplicadas: number
    saldo_pendiente: number
  }
}

interface ReporteData {
  fecha: string
  notas_credito: NotaCredito[]
  aplicaciones: Aplicacion[]
  facturas_rechazadas: FacturaRechazada[]
  resumen: Resumen
}

export default function OperativeReportPage() {
  const navigate = useNavigate()

  const [fecha, setFecha] = useState(() => {
    // Por defecto, ayer
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    return yesterday.toISOString().split('T')[0]
  })

  const [data, setData] = useState<ReporteData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/api/reporte/operativo?fecha=${fecha}`)
      setData(response.data)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al cargar reporte')
    } finally {
      setLoading(false)
    }
  }

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFecha(e.target.value)
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(Math.abs(value))
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-CO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Columnas para Notas de Crédito
  const notasColumns = [
    {
      key: 'numero',
      label: 'Nota',
      render: (nota: NotaCredito) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{nota.numero_nota}</p>
            <p className="text-xs text-gray-500">{formatDate(nota.fecha_nota)}</p>
          </div>
        </div>
      )
    },
    {
      key: 'cliente',
      label: 'Cliente',
      render: (nota: NotaCredito) => (
        <div>
          <p className="font-medium text-gray-900 truncate max-w-[200px]">{nota.nombre_cliente}</p>
          <p className="text-xs text-gray-500">{nota.nit_cliente}</p>
        </div>
      )
    },
    {
      key: 'producto',
      label: 'Producto',
      render: (nota: NotaCredito) => (
        <div>
          <p className="font-medium text-gray-900 truncate max-w-[200px]">{nota.nombre_producto}</p>
          <p className="text-xs text-gray-500">{nota.codigo_producto}</p>
        </div>
      )
    },
    {
      key: 'valor',
      label: 'Valor',
      align: 'right' as const,
      render: (nota: NotaCredito) => (
        <div className="text-right">
          <p className="font-bold text-gray-900">{formatCurrency(nota.valor_total)}</p>
          <p className="text-xs text-gray-500">Cant: {nota.cantidad.toFixed(2)}</p>
        </div>
      )
    },
    {
      key: 'saldo',
      label: 'Saldo',
      align: 'right' as const,
      render: (nota: NotaCredito) => (
        <div className="text-right">
          <p className="font-bold text-orange-600">{formatCurrency(nota.saldo_pendiente)}</p>
          <p className="text-xs text-gray-500">Pend: {nota.cantidad_pendiente.toFixed(2)}</p>
        </div>
      )
    },
    {
      key: 'estado',
      label: 'Estado',
      align: 'center' as const,
      render: (nota: NotaCredito) => (
        <Badge variant={nota.estado === 'APLICADA' ? 'success' : nota.estado === 'PENDIENTE' ? 'warning' : 'default'}>
          {nota.estado === 'APLICADA' ? <CheckCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
          {nota.estado}
        </Badge>
      )
    }
  ]

  // Columnas para Aplicaciones
  const aplicacionesColumns = [
    {
      key: 'nota_factura',
      label: 'Documentos',
      render: (app: Aplicacion) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-emerald-600" />
            <p className="font-semibold text-gray-900">{app.numero_nota}</p>
          </div>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <p className="text-sm text-gray-600">{app.numero_factura}</p>
          </div>
        </div>
      )
    },
    {
      key: 'cliente',
      label: 'Cliente / Producto',
      render: (app: Aplicacion) => (
        <div className="space-y-1">
          <p className="font-medium text-gray-900">{app.nit_cliente}</p>
          <p className="text-xs text-gray-500">{app.codigo_producto}</p>
        </div>
      )
    },
    {
      key: 'valor',
      label: 'Aplicado',
      align: 'right' as const,
      render: (app: Aplicacion) => (
        <div className="text-right">
          <p className="font-bold text-emerald-600">{formatCurrency(app.valor_aplicado)}</p>
          <p className="text-xs text-gray-500">Cant: {app.cantidad_aplicada.toFixed(2)}</p>
        </div>
      )
    },
    {
      key: 'fecha',
      label: 'Fecha',
      render: (app: Aplicacion) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-700">{formatDateTime(app.fecha_aplicacion)}</span>
        </div>
      )
    }
  ]

  // Columnas para Facturas Rechazadas
  const rechazadasColumns = [
    {
      key: 'factura',
      label: 'Factura',
      render: (factura: FacturaRechazada) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0">
            <XCircle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{factura.numero_factura}</p>
            <p className="text-xs text-gray-500">{formatDate(factura.fecha_factura)}</p>
          </div>
        </div>
      )
    },
    {
      key: 'cliente',
      label: 'Cliente',
      render: (factura: FacturaRechazada) => (
        <div>
          <p className="font-medium text-gray-900 truncate max-w-[200px]">{factura.nombre_cliente}</p>
          <p className="text-xs text-gray-500">{factura.nit_cliente}</p>
        </div>
      )
    },
    {
      key: 'producto',
      label: 'Producto',
      render: (factura: FacturaRechazada) => (
        <div>
          <p className="font-medium text-gray-900 truncate max-w-[200px]">{factura.nombre_producto}</p>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-gray-500">{factura.codigo_producto}</p>
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
              {factura.tipo_inventario}
            </span>
          </div>
        </div>
      )
    },
    {
      key: 'valor',
      label: 'Valor',
      align: 'right' as const,
      render: (factura: FacturaRechazada) => (
        <p className="font-bold text-gray-900">{formatCurrency(factura.valor_total)}</p>
      )
    },
    {
      key: 'razon',
      label: 'Razón de Rechazo',
      render: (factura: FacturaRechazada) => (
        <div className="flex items-start gap-2 max-w-[300px]">
          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-gray-600">{factura.razon_rechazo}</p>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header con gradiente */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg">
              <FileText className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                Reporte Operativo Diario
              </h1>
              <p className="text-gray-600 mt-1">
                Resumen consolidado de operaciones
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/')}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Dashboard
          </Button>
        </div>
      </div>

      {/* Selector de Fecha */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <div>
              <CardTitle className="text-lg">Seleccionar Fecha</CardTitle>
              <CardDescription className="mt-1">
                Consulte el reporte operativo de un día específico
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex gap-4 items-end">
            <div className="space-y-2 flex-1 max-w-xs">
              <Label htmlFor="fecha" className="text-sm font-semibold text-gray-700">
                Fecha del Reporte
              </Label>
              <Input
                id="fecha"
                type="date"
                value={fecha}
                onChange={handleDateChange}
                className="h-11 border-2 focus:border-blue-500"
              />
            </div>
            <Button 
              onClick={loadReport} 
              disabled={loading}
              className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg h-11"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Cargando...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Consultar
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="mt-4 flex items-center gap-3 text-sm text-red-700 bg-red-50 p-4 rounded-lg border-2 border-red-200">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resumen */}
      {data && (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card className="border-2 border-emerald-200 shadow-md hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-emerald-600" />
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-600 mb-1">Notas del Día</p>
                <p className="text-4xl font-bold text-gray-900">{data.resumen.total_notas}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-blue-200 shadow-md hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-600 mb-1">Aplicaciones</p>
                <p className="text-4xl font-bold text-gray-900">{data.resumen.total_aplicaciones}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-red-200 shadow-md hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center">
                    <XCircle className="w-6 h-6 text-red-600" />
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-600 mb-1">Rechazadas</p>
                <p className="text-4xl font-bold text-gray-900">{data.resumen.total_rechazadas}</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-orange-200 shadow-md hover:shadow-lg transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-orange-600" />
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-600 mb-1">Saldo Pendiente</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(data.resumen.resumen_notas.saldo_pendiente)}</p>
              </CardContent>
            </Card>
          </div>

          {/* Tabs con Datos */}
          <Card className="border-0 shadow-lg">
            <CardContent className="pt-6">
              <Tabs defaultValue="notas">
                <TabsList className="grid w-full grid-cols-3 bg-gray-100 p-1">
                  <TabsTrigger 
                    value="notas"
                    className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Notas ({data.notas_credito.length})
                  </TabsTrigger>
                  <TabsTrigger 
                    value="aplicaciones"
                    className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Aplicaciones ({data.aplicaciones.length})
                  </TabsTrigger>
                  <TabsTrigger 
                    value="rechazadas"
                    className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Rechazadas ({data.facturas_rechazadas.length})
                  </TabsTrigger>
                </TabsList>

                {/* Notas de Crédito */}
                <TabsContent value="notas" className="mt-6">
                  {data.notas_credito.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 space-y-3">
                      <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
                        <FileText className="w-8 h-8 text-gray-400" />
                      </div>
                      <div className="text-center">
                        <p className="text-gray-900 font-medium">Sin notas de crédito</p>
                        <p className="text-sm text-gray-500 mt-1">
                          No hay notas de crédito para esta fecha
                        </p>
                      </div>
                    </div>
                  ) : (
                    <Table
                      columns={notasColumns}
                      data={data.notas_credito}
                      keyExtractor={(nota, idx) => nota.numero_nota + idx}
                      hoverable
                      bordered
                    />
                  )}
                </TabsContent>

                {/* Aplicaciones */}
                <TabsContent value="aplicaciones" className="mt-6">
                  {data.aplicaciones.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 space-y-3">
                      <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
                        <CheckCircle className="w-8 h-8 text-gray-400" />
                      </div>
                      <div className="text-center">
                        <p className="text-gray-900 font-medium">Sin aplicaciones</p>
                        <p className="text-sm text-gray-500 mt-1">
                          No hay aplicaciones para esta fecha
                        </p>
                      </div>
                    </div>
                  ) : (
                    <Table
                      columns={aplicacionesColumns}
                      data={data.aplicaciones}
                      keyExtractor={(app, idx) => app.numero_nota + app.numero_factura + idx}
                      hoverable
                      bordered
                    />
                  )}
                </TabsContent>

                {/* Facturas Rechazadas */}
                <TabsContent value="rechazadas" className="mt-6">
                  {data.facturas_rechazadas.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 space-y-3">
                      <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
                        <CheckCircle className="w-8 h-8 text-emerald-400" />
                      </div>
                      <div className="text-center">
                        <p className="text-gray-900 font-medium">¡Excelente!</p>
                        <p className="text-sm text-gray-500 mt-1">
                          No hay facturas rechazadas para esta fecha
                        </p>
                      </div>
                    </div>
                  ) : (
                    <Table
                      columns={rechazadasColumns}
                      data={data.facturas_rechazadas}
                      keyExtractor={(factura, idx) => factura.numero_factura + idx}
                      hoverable
                      bordered
                    />
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Resumen General de Notas */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                <div>
                  <CardTitle className="text-lg">Resumen General de Notas de Crédito</CardTitle>
                  <CardDescription className="mt-1">Estado global del sistema</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 bg-gray-50 rounded-xl border-2 border-gray-200">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-gray-600" />
                    </div>
                    <p className="text-sm font-medium text-gray-600">Total de Notas</p>
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{data.resumen.resumen_notas.total}</p>
                </div>
                
                <div className="p-4 bg-orange-50 rounded-xl border-2 border-orange-200">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                      <Clock className="w-5 h-5 text-orange-600" />
                    </div>
                    <p className="text-sm font-medium text-gray-600">Notas Pendientes</p>
                  </div>
                  <p className="text-3xl font-bold text-orange-600">{data.resumen.resumen_notas.pendientes}</p>
                </div>
                
                <div className="p-4 bg-emerald-50 rounded-xl border-2 border-emerald-200">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                    </div>
                    <p className="text-sm font-medium text-gray-600">Notas Aplicadas</p>
                  </div>
                  <p className="text-3xl font-bold text-emerald-600">{data.resumen.resumen_notas.aplicadas}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}