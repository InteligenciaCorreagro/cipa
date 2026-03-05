import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, Badge } from '@/components/ui/table'
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
  es_agente?: number
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
  producto: string
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
    no_aplicadas: number
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

  const loadReport = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/api/reporte/operativo?fecha=${fecha}`)
      const payload = response.data ?? {}
      const resumenPayload = payload.resumen ?? {}
      const resumenNotasPayload = resumenPayload.resumen_notas ?? {}

      setData({
        fecha: payload.fecha ?? fecha,
        notas_credito: Array.isArray(payload.notas_credito) ? payload.notas_credito : [],
        aplicaciones: Array.isArray(payload.aplicaciones) ? payload.aplicaciones : [],
        facturas_rechazadas: Array.isArray(payload.facturas_rechazadas) ? payload.facturas_rechazadas : [],
        resumen: {
          total_notas: Number(resumenPayload.total_notas ?? 0),
          total_aplicaciones: Number(resumenPayload.total_aplicaciones ?? 0),
          total_rechazadas: Number(resumenPayload.total_rechazadas ?? 0),
          resumen_notas: {
            total: Number(resumenNotasPayload.total ?? 0),
            pendientes: Number(resumenNotasPayload.pendientes ?? 0),
            aplicadas: Number(resumenNotasPayload.aplicadas ?? 0),
            saldo_pendiente: Number(resumenNotasPayload.saldo_pendiente ?? 0),
            no_aplicadas: Number(resumenNotasPayload.no_aplicadas ?? 0),
          }
        }
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar reporte'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [fecha])

  useEffect(() => {
    loadReport()
  }, [loadReport])

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
          <p className="font-medium text-gray-900 truncate max-w-[200px]">{factura.producto}</p>
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Reporte Operativo Diario
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Resumen consolidado de operaciones
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/')}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Dashboard
        </Button>
      </div>

      {/* Selector de Fecha */}
      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary" />
            <div>
              <CardTitle className="text-base font-semibold text-foreground">Seleccionar Fecha</CardTitle>
              <CardDescription className="mt-1">
                Consulte el reporte operativo de un dia especifico
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="space-y-2 flex-1 max-w-xs">
              <Label htmlFor="fecha" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Fecha del Reporte
              </Label>
              <Input
                id="fecha"
                type="date"
                value={fecha}
                onChange={handleDateChange}
                className="h-10"
              />
            </div>
            <Button 
              onClick={loadReport} 
              disabled={loading}
              size="sm"
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
            <div className="mt-4 flex items-center gap-3 text-sm text-destructive bg-destructive/5 p-4 rounded-lg border border-destructive/20">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resumen */}
      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="border border-border">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Notas del Dia</p>
                    <p className="text-2xl font-semibold text-foreground mt-2">{data.resumen.total_notas}</p>
                  </div>
                  <div className="h-9 w-9 rounded-lg bg-primary/8 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-border">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Aplicaciones</p>
                    <p className="text-2xl font-semibold text-foreground mt-2">{data.resumen.total_aplicaciones}</p>
                  </div>
                  <div className="h-9 w-9 rounded-lg bg-primary/8 flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-border">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Rechazadas</p>
                    <p className="text-2xl font-semibold text-foreground mt-2">{data.resumen.total_rechazadas}</p>
                  </div>
                  <div className="h-9 w-9 rounded-lg bg-destructive/8 flex items-center justify-center">
                    <XCircle className="w-4 h-4 text-destructive" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-border">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Saldo Pendiente</p>
                    <p className="text-xl font-semibold text-foreground mt-2">{formatCurrency(data.resumen.resumen_notas.saldo_pendiente)}</p>
                  </div>
                  <div className="h-9 w-9 rounded-lg bg-primary/8 flex items-center justify-center">
                    <DollarSign className="w-4 h-4 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tabs con Datos */}
          <Card className="border border-border">
            <CardContent className="pt-6">
              <Tabs defaultValue="notas">
                <TabsList className="grid w-full grid-cols-3 bg-muted p-1">
                  <TabsTrigger 
                    value="notas"
                    className="data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-sm text-muted-foreground"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Notas ({data.notas_credito.length})
                  </TabsTrigger>
                  <TabsTrigger 
                    value="aplicaciones"
                    className="data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-sm text-muted-foreground"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Aplicaciones ({data.aplicaciones.length})
                  </TabsTrigger>
                  <TabsTrigger 
                    value="rechazadas"
                    className="data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:shadow-sm text-muted-foreground"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Rechazadas ({data.facturas_rechazadas.length})
                  </TabsTrigger>
                </TabsList>

                {/* Notas de Crédito */}
                <TabsContent value="notas" className="mt-6">
                  {data.notas_credito.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 space-y-3">
                      <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center">
                        <FileText className="w-6 h-6 text-muted-foreground" />
                      </div>
                      <div className="text-center">
                        <p className="text-foreground font-medium text-sm">Sin notas de credito</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          No hay notas de credito para esta fecha
                        </p>
                      </div>
                    </div>
                  ) : (
                    <Table
                      columns={notasColumns}
                      data={data.notas_credito}
                      keyExtractor={(nota) => `${nota.numero_nota}-${nota.fecha_nota}`}
                      hoverable
                      bordered
                    />
                  )}
                </TabsContent>

                {/* Aplicaciones */}
                <TabsContent value="aplicaciones" className="mt-6">
                  {data.aplicaciones.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 space-y-3">
                      <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center">
                        <CheckCircle className="w-6 h-6 text-muted-foreground" />
                      </div>
                      <div className="text-center">
                        <p className="text-foreground font-medium text-sm">Sin aplicaciones</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          No hay aplicaciones para esta fecha
                        </p>
                      </div>
                    </div>
                  ) : (
                    <Table
                      columns={aplicacionesColumns}
                      data={data.aplicaciones}
                      keyExtractor={(app) => `${app.numero_nota}-${app.numero_factura}-${app.fecha_aplicacion}`}
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
                      keyExtractor={(factura) => `${factura.numero_factura}-${factura.fecha_factura}`}
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
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
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

                <div className="p-4 bg-red-50 rounded-xl border-2 border-red-200">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                      <AlertCircle className="w-5 h-5 text-red-600" />
                    </div>
                    <p className="text-sm font-medium text-gray-600">No Aplicadas</p>
                  </div>
                  <p className="text-3xl font-bold text-red-600">{data.resumen.resumen_notas.no_aplicadas}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
