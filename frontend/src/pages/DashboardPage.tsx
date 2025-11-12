import { useEstadisticas, useNotasPorEstado } from '@/hooks/useNotas'
import { useEstadisticasFacturas, useTransacciones } from '@/hooks/useFacturas'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatCurrency } from '@/lib/utils'
import { FileText, DollarSign, AlertCircle, CheckCircle, RefreshCw, ServerCrash, Receipt, TrendingUp, XCircle } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

const COLORS = ['#3b82f6', '#f59e0b', '#10b981']

export default function DashboardPage() {
  const { data: estadisticas, isLoading: loadingEstadisticas, error: errorEstadisticas, refetch: refetchEstadisticas } = useEstadisticas()
  const { data: notasPorEstado, isLoading: loadingPorEstado, error: errorPorEstado, refetch: refetchPorEstado } = useNotasPorEstado()
  const { data: estadisticasFacturas, isLoading: loadingFacturas, error: errorFacturas, refetch: refetchFacturas } = useEstadisticasFacturas()
  const { data: transacciones, isLoading: loadingTransacciones, error: errorTransacciones } = useTransacciones({ limite: 10 })

  // Manejo de errores
  if (errorEstadisticas || errorPorEstado || errorFacturas) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <ServerCrash className="h-16 w-16 text-muted-foreground" />
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold">Error al cargar el dashboard</h3>
          <p className="text-muted-foreground max-w-md">
            No se pudo conectar con la API. Por favor, verifica que el servidor esté funcionando en{' '}
            <code className="bg-muted px-1 py-0.5 rounded">http://localhost:5000</code>
          </p>
          <p className="text-sm text-muted-foreground">
            Error: {(errorEstadisticas as any)?.message || (errorPorEstado as any)?.message || (errorFacturas as any)?.message || 'Error de conexión'}
          </p>
        </div>
        <Button onClick={() => {
          refetchEstadisticas()
          refetchPorEstado()
          refetchFacturas()
        }}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Reintentar
        </Button>
      </div>
    )
  }

  if (loadingEstadisticas || loadingPorEstado || loadingFacturas) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Cargando estadísticas...</div>
      </div>
    )
  }

  const pieData = notasPorEstado?.map(item => ({
    name: item.estado,
    value: item.cantidad,
    monto: item.valor_total
  })) || []

  const barData = notasPorEstado?.map(item => ({
    estado: item.estado,
    cantidad: item.cantidad,
    valor: Math.abs(item.valor_total)
  })) || []

  const stats = [
    {
      title: 'Total Notas',
      value: estadisticas?.total_notas || 0,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20'
    },
    {
      title: 'Valor Total',
      value: formatCurrency(Math.abs(estadisticas?.total_valor || 0)),
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20'
    },
    {
      title: 'Saldo Pendiente',
      value: formatCurrency(Math.abs(estadisticas?.saldo_pendiente_total || 0)),
      icon: AlertCircle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20'
    },
    {
      title: 'Notas Aplicadas',
      value: estadisticas?.notas_aplicadas || 0,
      icon: CheckCircle,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100 dark:bg-emerald-900/20'
    }
  ]

  const statsFacturas = [
    {
      title: 'Total Facturas',
      value: estadisticasFacturas?.total_facturas || 0,
      icon: Receipt,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20'
    },
    {
      title: 'Facturas Válidas',
      value: estadisticasFacturas?.facturas_validas || 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20'
    },
    {
      title: 'Facturas Inválidas',
      value: estadisticasFacturas?.facturas_invalidas || 0,
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-100 dark:bg-red-900/20'
    },
    {
      title: 'Valor Transado',
      value: formatCurrency(estadisticasFacturas?.valor_total_transado || 0),
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20'
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Visualización de información y estadísticas de notas y facturas
        </p>
      </div>

      {/* Sección Notas de Crédito */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Notas de Crédito</h2>

        {/* Stats Grid - Notas */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <div className={`${stat.bgColor} p-2 rounded-lg`}>
                    <Icon className={`h-4 w-4 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Sección Facturas */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Facturas</h2>

        {/* Stats Grid - Facturas */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {statsFacturas.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <div className={`${stat.bgColor} p-2 rounded-lg`}>
                    <Icon className={`h-4 w-4 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Estado</CardTitle>
            <CardDescription>
              Cantidad de notas por estado
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(props: any) => `${props.name}: ${(props.percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, _name: string, props: any) => [
                    `${value} notas`,
                    props.payload.name
                  ]}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Valor por Estado</CardTitle>
            <CardDescription>
              Monto total de notas por estado
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="estado" />
                <YAxis tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`} />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  labelFormatter={(label) => `Estado: ${label}`}
                />
                <Bar dataKey="valor" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Estado Details */}
      <Card>
        <CardHeader>
          <CardTitle>Detalle por Estado</CardTitle>
          <CardDescription>
            Resumen detallado de notas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {notasPorEstado?.map((item) => (
              <div key={item.estado} className="flex items-center justify-between border-b pb-4 last:border-0">
                <div>
                  <p className="font-medium">{item.estado}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.cantidad} notas
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{formatCurrency(Math.abs(item.valor_total))}</p>
                  <p className="text-sm text-muted-foreground">
                    Pendiente: {formatCurrency(Math.abs(item.saldo_pendiente))}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Grilla de Transacciones */}
      <Card>
        <CardHeader>
          <CardTitle>Grilla de Transacciones</CardTitle>
          <CardDescription>
            Últimas facturas transadas (con valor transado &gt; 0)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTransacciones ? (
            <div className="text-muted-foreground text-center py-8">Cargando transacciones...</div>
          ) : errorTransacciones ? (
            <div className="text-destructive text-center py-8">Error al cargar transacciones</div>
          ) : transacciones?.items && transacciones.items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium">Número</th>
                    <th className="text-left py-3 px-4 font-medium">Fecha</th>
                    <th className="text-left py-3 px-4 font-medium">Cliente</th>
                    <th className="text-left py-3 px-4 font-medium">Producto</th>
                    <th className="text-right py-3 px-4 font-medium">Valor Total</th>
                    <th className="text-right py-3 px-4 font-medium">Valor Transado</th>
                    <th className="text-center py-3 px-4 font-medium">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {transacciones.items.map((transaccion) => (
                    <tr key={transaccion.id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">{transaccion.numero_factura}</td>
                      <td className="py-3 px-4">{new Date(transaccion.fecha_factura).toLocaleDateString('es-CO')}</td>
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">{transaccion.nombre_cliente}</p>
                          <p className="text-xs text-muted-foreground">{transaccion.nit_cliente}</p>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">{transaccion.nombre_producto}</p>
                          <p className="text-xs text-muted-foreground">{transaccion.codigo_producto}</p>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">{formatCurrency(transaccion.valor_total)}</td>
                      <td className="py-3 px-4 text-right font-semibold text-green-600">
                        {formatCurrency(transaccion.valor_transado)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          transaccion.tiene_nota_credito
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                        }`}>
                          {transaccion.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-muted-foreground text-center py-8">No hay transacciones registradas</div>
          )}
          {transacciones?.items && transacciones.items.length > 0 && (
            <div className="mt-4 text-sm text-muted-foreground text-center">
              Mostrando {transacciones.items.length} de {transacciones.total} transacciones
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
