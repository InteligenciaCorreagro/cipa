import { useState, useEffect, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { SortableTable, Column } from '@/components/ui/sortable-table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api } from '@/services/api'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'

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

  // Filtros
  const [filtroNotasCliente, setFiltroNotasCliente] = useState('')
  const [filtroAplicacionesCliente, setFiltroAplicacionesCliente] = useState('')
  const [filtroRechazadasCliente, setFiltroRechazadasCliente] = useState('')

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
    }).format(value)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-CO')
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CO')
  }

  const getEstadoBadgeColor = (estado: string) => {
    switch (estado) {
      case 'PENDIENTE':
        return 'bg-yellow-100 text-yellow-800'
      case 'APLICADA':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Datos filtrados
  const notasFiltradas = useMemo(() => {
    if (!data) return []
    return data.notas_credito.filter(nota => {
      const searchTerm = filtroNotasCliente.toLowerCase()
      return (
        nota.nombre_cliente.toLowerCase().includes(searchTerm) ||
        nota.nit_cliente.toLowerCase().includes(searchTerm) ||
        nota.numero_nota.toLowerCase().includes(searchTerm) ||
        nota.nombre_producto.toLowerCase().includes(searchTerm)
      )
    })
  }, [data, filtroNotasCliente])

  const aplicacionesFiltradas = useMemo(() => {
    if (!data) return []
    return data.aplicaciones.filter(app => {
      const searchTerm = filtroAplicacionesCliente.toLowerCase()
      return (
        app.nit_cliente.toLowerCase().includes(searchTerm) ||
        app.numero_nota.toLowerCase().includes(searchTerm) ||
        app.numero_factura.toLowerCase().includes(searchTerm)
      )
    })
  }, [data, filtroAplicacionesCliente])

  const rechazadasFiltradas = useMemo(() => {
    if (!data) return []
    return data.facturas_rechazadas.filter(factura => {
      const searchTerm = filtroRechazadasCliente.toLowerCase()
      return (
        factura.nombre_cliente.toLowerCase().includes(searchTerm) ||
        factura.nit_cliente.toLowerCase().includes(searchTerm) ||
        factura.numero_factura.toLowerCase().includes(searchTerm) ||
        factura.nombre_producto.toLowerCase().includes(searchTerm)
      )
    })
  }, [data, filtroRechazadasCliente])

  // Columnas para las tablas
  const notasColumns: Column<NotaCredito>[] = [
    {
      key: 'numero_nota',
      label: 'Número',
      render: (nota) => <span className="font-medium">{nota.numero_nota}</span>,
    },
    {
      key: 'fecha_nota',
      label: 'Fecha',
      render: (nota) => formatDate(nota.fecha_nota),
      getValue: (nota) => new Date(nota.fecha_nota).getTime(),
    },
    {
      key: 'nombre_cliente',
      label: 'Cliente',
      render: (nota) => (
        <div>
          <div className="max-w-xs truncate" title={nota.nombre_cliente}>
            {nota.nombre_cliente}
          </div>
          <div className="text-xs text-muted-foreground">{nota.nit_cliente}</div>
        </div>
      ),
    },
    {
      key: 'nombre_producto',
      label: 'Producto',
      render: (nota) => (
        <div>
          <div className="max-w-xs truncate" title={nota.nombre_producto}>
            {nota.nombre_producto}
          </div>
          <div className="text-xs text-muted-foreground">{nota.codigo_producto}</div>
        </div>
      ),
    },
    {
      key: 'valor_total',
      label: 'Valor',
      className: 'text-right',
      render: (nota) => formatCurrency(nota.valor_total),
    },
    {
      key: 'cantidad',
      label: 'Cantidad',
      className: 'text-right',
      render: (nota) => nota.cantidad.toFixed(2),
    },
    {
      key: 'saldo_pendiente',
      label: 'Saldo',
      className: 'text-right',
      render: (nota) => formatCurrency(nota.saldo_pendiente),
    },
    {
      key: 'estado',
      label: 'Estado',
      render: (nota) => (
        <span className={`px-2 py-1 rounded text-xs font-semibold ${getEstadoBadgeColor(nota.estado)}`}>
          {nota.estado}
        </span>
      ),
    },
  ]

  const aplicacionesColumns: Column<Aplicacion>[] = [
    {
      key: 'numero_nota',
      label: 'Nota',
      render: (app) => <span className="font-medium">{app.numero_nota}</span>,
    },
    {
      key: 'numero_factura',
      label: 'Factura',
    },
    {
      key: 'nit_cliente',
      label: 'Cliente',
    },
    {
      key: 'codigo_producto',
      label: 'Producto',
    },
    {
      key: 'valor_aplicado',
      label: 'Valor Aplicado',
      className: 'text-right',
      render: (app) => formatCurrency(app.valor_aplicado),
    },
    {
      key: 'cantidad_aplicada',
      label: 'Cantidad',
      className: 'text-right',
      render: (app) => app.cantidad_aplicada.toFixed(2),
    },
    {
      key: 'fecha_aplicacion',
      label: 'Fecha',
      render: (app) => formatDateTime(app.fecha_aplicacion),
      getValue: (app) => new Date(app.fecha_aplicacion).getTime(),
    },
  ]

  const rechazadasColumns: Column<FacturaRechazada>[] = [
    {
      key: 'numero_factura',
      label: 'Número',
      render: (factura) => <span className="font-medium">{factura.numero_factura}</span>,
    },
    {
      key: 'fecha_factura',
      label: 'Fecha',
      render: (factura) => formatDate(factura.fecha_factura),
      getValue: (factura) => new Date(factura.fecha_factura).getTime(),
    },
    {
      key: 'nombre_cliente',
      label: 'Cliente',
      render: (factura) => (
        <div>
          <div className="max-w-xs truncate" title={factura.nombre_cliente}>
            {factura.nombre_cliente}
          </div>
          <div className="text-xs text-muted-foreground">{factura.nit_cliente}</div>
        </div>
      ),
    },
    {
      key: 'nombre_producto',
      label: 'Producto',
      render: (factura) => (
        <div>
          <div className="max-w-xs truncate" title={factura.nombre_producto}>
            {factura.nombre_producto}
          </div>
          <div className="text-xs text-muted-foreground">{factura.codigo_producto}</div>
        </div>
      ),
    },
    {
      key: 'tipo_inventario',
      label: 'Tipo Inv.',
    },
    {
      key: 'valor_total',
      label: 'Valor',
      className: 'text-right',
      render: (factura) => formatCurrency(factura.valor_total),
    },
    {
      key: 'razon_rechazo',
      label: 'Razón',
      render: (factura) => (
        <span className="text-sm text-muted-foreground">
          {factura.razon_rechazo}
        </span>
      ),
    },
  ]

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Reporte Operativo Diario</h1>
        <Button variant="outline" onClick={() => navigate('/')}>
          Volver al Dashboard
        </Button>
      </div>

      {/* Selector de Fecha */}
      <Card>
        <CardHeader>
          <CardTitle>Seleccionar Fecha</CardTitle>
          <CardDescription>
            Consulte el reporte operativo de un día específico
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="space-y-2 flex-1 max-w-xs">
              <Label htmlFor="fecha">Fecha del Reporte</Label>
              <Input
                id="fecha"
                type="date"
                value={fecha}
                onChange={handleDateChange}
              />
            </div>
            <Button onClick={loadReport} disabled={loading}>
              {loading ? 'Cargando...' : 'Consultar'}
            </Button>
          </div>

          {error && (
            <div className="mt-4 text-sm text-red-600 bg-red-50 p-3 rounded">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resumen */}
      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Notas del Día</CardDescription>
                <CardTitle className="text-3xl">{data.resumen.total_notas}</CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Aplicaciones</CardDescription>
                <CardTitle className="text-3xl">{data.resumen.total_aplicaciones}</CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Rechazadas</CardDescription>
                <CardTitle className="text-3xl">{data.resumen.total_rechazadas}</CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Saldo Pendiente</CardDescription>
                <CardTitle className="text-2xl">{formatCurrency(data.resumen.resumen_notas.saldo_pendiente)}</CardTitle>
              </CardHeader>
            </Card>
          </div>

          {/* Tabs con Datos */}
          <Card>
            <CardContent className="pt-6">
              <Tabs defaultValue="notas">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="notas">
                    Notas de Crédito ({data.notas_credito.length})
                  </TabsTrigger>
                  <TabsTrigger value="aplicaciones">
                    Aplicaciones ({data.aplicaciones.length})
                  </TabsTrigger>
                  <TabsTrigger value="rechazadas">
                    Rechazadas ({data.facturas_rechazadas.length})
                  </TabsTrigger>
                </TabsList>

                {/* Notas de Crédito */}
                <TabsContent value="notas">
                  <div className="space-y-4">
                    {/* Filtro */}
                    <div className="flex items-center gap-2">
                      <Search className="h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Buscar por cliente, NIT, número de nota o producto..."
                        value={filtroNotasCliente}
                        onChange={(e) => setFiltroNotasCliente(e.target.value)}
                        className="max-w-md"
                      />
                    </div>
                    <SortableTable
                      data={notasFiltradas}
                      columns={notasColumns}
                      loading={loading}
                      emptyMessage="No hay notas de crédito para esta fecha"
                    />
                  </div>
                </TabsContent>

                {/* Aplicaciones */}
                <TabsContent value="aplicaciones">
                  <div className="space-y-4">
                    {/* Filtro */}
                    <div className="flex items-center gap-2">
                      <Search className="h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Buscar por NIT, número de nota o factura..."
                        value={filtroAplicacionesCliente}
                        onChange={(e) => setFiltroAplicacionesCliente(e.target.value)}
                        className="max-w-md"
                      />
                    </div>
                    <SortableTable
                      data={aplicacionesFiltradas}
                      columns={aplicacionesColumns}
                      loading={loading}
                      emptyMessage="No hay aplicaciones para esta fecha"
                    />
                  </div>
                </TabsContent>

                {/* Facturas Rechazadas */}
                <TabsContent value="rechazadas">
                  <div className="space-y-4">
                    {/* Filtro */}
                    <div className="flex items-center gap-2">
                      <Search className="h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Buscar por cliente, NIT, número de factura o producto..."
                        value={filtroRechazadasCliente}
                        onChange={(e) => setFiltroRechazadasCliente(e.target.value)}
                        className="max-w-md"
                      />
                    </div>
                    <SortableTable
                      data={rechazadasFiltradas}
                      columns={rechazadasColumns}
                      loading={loading}
                      emptyMessage="No hay facturas rechazadas para esta fecha"
                    />
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Resumen General de Notas */}
          <Card>
            <CardHeader>
              <CardTitle>Resumen General de Notas de Crédito</CardTitle>
              <CardDescription>Estado global del sistema</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Total de Notas</p>
                  <p className="text-2xl font-bold">{data.resumen.resumen_notas.total}</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Notas Pendientes</p>
                  <p className="text-2xl font-bold text-yellow-600">{data.resumen.resumen_notas.pendientes}</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Notas Aplicadas</p>
                  <p className="text-2xl font-bold text-green-600">{data.resumen.resumen_notas.aplicadas}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
