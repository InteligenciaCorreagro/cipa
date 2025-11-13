import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api } from '@/services/api'
import { useNavigate } from 'react-router-dom'

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
                  <div className="overflow-x-auto">
                    {data.notas_credito.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        No hay notas de crédito para esta fecha
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Número</TableHead>
                            <TableHead>Fecha</TableHead>
                            <TableHead>Cliente</TableHead>
                            <TableHead>Producto</TableHead>
                            <TableHead className="text-right">Valor</TableHead>
                            <TableHead className="text-right">Cantidad</TableHead>
                            <TableHead className="text-right">Saldo</TableHead>
                            <TableHead>Estado</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.notas_credito.map((nota, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{nota.numero_nota}</TableCell>
                              <TableCell>{formatDate(nota.fecha_nota)}</TableCell>
                              <TableCell>
                                <div className="max-w-xs truncate" title={nota.nombre_cliente}>
                                  {nota.nombre_cliente}
                                </div>
                                <div className="text-xs text-muted-foreground">{nota.nit_cliente}</div>
                              </TableCell>
                              <TableCell>
                                <div className="max-w-xs truncate" title={nota.nombre_producto}>
                                  {nota.nombre_producto}
                                </div>
                                <div className="text-xs text-muted-foreground">{nota.codigo_producto}</div>
                              </TableCell>
                              <TableCell className="text-right">{formatCurrency(nota.valor_total)}</TableCell>
                              <TableCell className="text-right">{nota.cantidad.toFixed(2)}</TableCell>
                              <TableCell className="text-right">{formatCurrency(nota.saldo_pendiente)}</TableCell>
                              <TableCell>
                                <span className={`px-2 py-1 rounded text-xs font-semibold ${getEstadoBadgeColor(nota.estado)}`}>
                                  {nota.estado}
                                </span>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </div>
                </TabsContent>

                {/* Aplicaciones */}
                <TabsContent value="aplicaciones">
                  <div className="overflow-x-auto">
                    {data.aplicaciones.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        No hay aplicaciones para esta fecha
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Nota</TableHead>
                            <TableHead>Factura</TableHead>
                            <TableHead>Cliente</TableHead>
                            <TableHead>Producto</TableHead>
                            <TableHead className="text-right">Valor Aplicado</TableHead>
                            <TableHead className="text-right">Cantidad</TableHead>
                            <TableHead>Fecha</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.aplicaciones.map((app, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{app.numero_nota}</TableCell>
                              <TableCell>{app.numero_factura}</TableCell>
                              <TableCell>{app.nit_cliente}</TableCell>
                              <TableCell>{app.codigo_producto}</TableCell>
                              <TableCell className="text-right">{formatCurrency(app.valor_aplicado)}</TableCell>
                              <TableCell className="text-right">{app.cantidad_aplicada.toFixed(2)}</TableCell>
                              <TableCell>{formatDateTime(app.fecha_aplicacion)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </div>
                </TabsContent>

                {/* Facturas Rechazadas */}
                <TabsContent value="rechazadas">
                  <div className="overflow-x-auto">
                    {data.facturas_rechazadas.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        No hay facturas rechazadas para esta fecha
                      </p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Número</TableHead>
                            <TableHead>Fecha</TableHead>
                            <TableHead>Cliente</TableHead>
                            <TableHead>Producto</TableHead>
                            <TableHead>Tipo Inv.</TableHead>
                            <TableHead className="text-right">Valor</TableHead>
                            <TableHead>Razón</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {data.facturas_rechazadas.map((factura, idx) => (
                            <TableRow key={idx}>
                              <TableCell className="font-medium">{factura.numero_factura}</TableCell>
                              <TableCell>{formatDate(factura.fecha_factura)}</TableCell>
                              <TableCell>
                                <div className="max-w-xs truncate" title={factura.nombre_cliente}>
                                  {factura.nombre_cliente}
                                </div>
                                <div className="text-xs text-muted-foreground">{factura.nit_cliente}</div>
                              </TableCell>
                              <TableCell>
                                <div className="max-w-xs truncate" title={factura.nombre_producto}>
                                  {factura.nombre_producto}
                                </div>
                                <div className="text-xs text-muted-foreground">{factura.codigo_producto}</div>
                              </TableCell>
                              <TableCell>{factura.tipo_inventario}</TableCell>
                              <TableCell className="text-right">{formatCurrency(factura.valor_total)}</TableCell>
                              <TableCell>
                                <span className="text-sm text-muted-foreground">
                                  {factura.razon_rechazo}
                                </span>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
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
