import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, DollarSign, AlertCircle, CheckCircle, RefreshCw, ServerCrash, Receipt, TrendingUp, XCircle, TrendingDown, Loader2 } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import { api } from '@/services/api'

const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444']

// Función para formatear moneda
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

// Tipos
interface Estadisticas {
  total_notas: number
  total_valor: number
  saldo_pendiente_total: number
  notas_aplicadas: number
}

interface NotaPorEstado {
  estado: string
  cantidad: number
  valor_total: number
}

interface EstadisticasFacturas {
  total_facturas: number
  facturas_validas: number
  facturas_invalidas: number
  valor_total_transado: number
}

interface Transaccion {
  id: number
  numero_factura: string
  fecha_factura: string
  nombre_cliente: string
  nit_cliente: string
  valor_total: number
  valor_transado: number
  estado: string
  tiene_nota_credito: boolean
}

export default function DashboardPage() {
  const [estadisticas, setEstadisticas] = useState<Estadisticas | null>(null)
  const [notasPorEstado, setNotasPorEstado] = useState<NotaPorEstado[]>([])
  const [estadisticasFacturas, setEstadisticasFacturas] = useState<EstadisticasFacturas | null>(null)
  const [transacciones, setTransacciones] = useState<Transaccion[]>([])
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Obtener estadísticas de notas
      const [statsRes, porEstadoRes, facturasRes, transaccionesRes] = await Promise.allSettled([
        api.get('/api/notas/estadisticas'),
        api.get('/api/notas/por-estado'),
        api.get('/api/facturas/estadisticas'),
        api.get('/api/facturas/transacciones?limite=10')
      ])

      if (statsRes.status === 'fulfilled') {
        setEstadisticas(statsRes.value.data)
      }
      
      if (porEstadoRes.status === 'fulfilled') {
        setNotasPorEstado(porEstadoRes.value.data)
      }
      
      if (facturasRes.status === 'fulfilled') {
        setEstadisticasFacturas(facturasRes.value.data)
      }
      
      if (transaccionesRes.status === 'fulfilled') {
        setTransacciones(transaccionesRes.value.data.items || transaccionesRes.value.data || [])
      }

      setLoading(false)
    } catch (err: any) {
      console.error('Error al cargar dashboard:', err)
      setError(err.message || 'Error al conectar con el servidor')
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Manejo de errores
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
          <ServerCrash className="h-8 w-8 text-red-600" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-gray-900">Error al cargar el dashboard</h3>
          <p className="text-gray-500 max-w-md">{error}</p>
        </div>
        <Button 
          onClick={fetchData}
          className="bg-emerald-600 hover:bg-emerald-700"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Reintentar
        </Button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-3">
          <Loader2 className="w-12 h-12 text-emerald-600 animate-spin mx-auto" />
          <p className="text-gray-500">Cargando estadísticas...</p>
        </div>
      </div>
    )
  }

  const pieData = notasPorEstado.map(item => ({
    name: item.estado,
    value: item.cantidad,
    monto: item.valor_total
  }))

  const barData = notasPorEstado.map(item => ({
    estado: item.estado,
    cantidad: item.cantidad,
    valor: Math.abs(item.valor_total)
  }))

  const stats = [
    {
      title: 'Total Notas',
      value: estadisticas?.total_notas || 0,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      trend: '+12%',
      trendUp: true
    },
    {
      title: 'Valor Total',
      value: formatCurrency(Math.abs(estadisticas?.total_valor || 0)),
      icon: DollarSign,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      trend: '+8%',
      trendUp: true
    },
    {
      title: 'Saldo Pendiente',
      value: formatCurrency(Math.abs(estadisticas?.saldo_pendiente_total || 0)),
      icon: AlertCircle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      trend: '-5%',
      trendUp: false
    },
    {
      title: 'Notas Aplicadas',
      value: estadisticas?.notas_aplicadas || 0,
      icon: CheckCircle,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      trend: '+15%',
      trendUp: true
    }
  ]

  const statsFacturas = [
    {
      title: 'Total Facturas',
      value: estadisticasFacturas?.total_facturas || 0,
      icon: Receipt,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      trend: '+3%',
      trendUp: true
    },
    {
      title: 'Facturas Válidas',
      value: estadisticasFacturas?.facturas_validas || 0,
      icon: CheckCircle,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      trend: '+5%',
      trendUp: true
    },
    {
      title: 'Facturas Rechazadas',
      value: estadisticasFacturas?.facturas_invalidas || 0,
      icon: XCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      trend: '-2%',
      trendUp: false
    },
    {
      title: 'Valor Transado',
      value: formatCurrency(estadisticasFacturas?.valor_total_transado || 0),
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      trend: '+18%',
      trendUp: true
    }
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Panel de control y estadísticas del sistema
          </p>
        </div>
        <Button 
          onClick={fetchData}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      {/* Stats Notas de Crédito */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <div className="w-1 h-6 bg-emerald-600 rounded-full"></div>
          Notas de Crédito
        </h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.title} className={`border-2 ${stat.borderColor} shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`w-14 h-14 rounded-2xl ${stat.bgColor} flex items-center justify-center ring-4 ring-white shadow-sm`}>
                      <Icon className={`h-7 w-7 ${stat.color}`} />
                    </div>
                    <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full ${
                      stat.trendUp ? 'bg-emerald-50' : 'bg-red-50'
                    }`}>
                      {stat.trendUp ? (
                        <TrendingUp className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <TrendingDown className="h-3.5 w-3.5 text-red-600" />
                      )}
                      <span className={`text-xs font-semibold ${
                        stat.trendUp ? 'text-emerald-600' : 'text-red-600'
                      }`}>
                        {stat.trend}
                      </span>
                    </div>
                  </div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">{stat.title}</h3>
                  <p className="text-3xl font-bold text-gray-900 tracking-tight">{stat.value}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Stats Facturas */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <div className="w-1 h-6 bg-blue-600 rounded-full"></div>
          Facturas
        </h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {statsFacturas.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.title} className={`border-2 ${stat.borderColor} shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`w-14 h-14 rounded-2xl ${stat.bgColor} flex items-center justify-center ring-4 ring-white shadow-sm`}>
                      <Icon className={`h-7 w-7 ${stat.color}`} />
                    </div>
                    <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full ${
                      stat.trendUp ? 'bg-emerald-50' : 'bg-red-50'
                    }`}>
                      {stat.trendUp ? (
                        <TrendingUp className="h-3.5 w-3.5 text-emerald-600" />
                      ) : (
                        <TrendingDown className="h-3.5 w-3.5 text-red-600" />
                      )}
                      <span className={`text-xs font-semibold ${
                        stat.trendUp ? 'text-emerald-600' : 'text-red-600'
                      }`}>
                        {stat.trend}
                      </span>
                    </div>
                  </div>
                  <h3 className="text-sm font-medium text-gray-600 mb-2">{stat.title}</h3>
                  <p className="text-3xl font-bold text-gray-900 tracking-tight">{stat.value}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-0 shadow-lg">
          <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
            <CardTitle className="text-lg">Distribución por Estado</CardTitle>
            <CardDescription>Porcentaje de notas según su estado</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: any) => `${props.name}: ${(props.percent * 100).toFixed(0)}%`}
                    outerRadius={110}
                    fill="#8884d8"
                    dataKey="value"
                    strokeWidth={2}
                    stroke="#fff"
                  >
                    {pieData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Legend 
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[320px] flex items-center justify-center text-gray-500">
                No hay datos disponibles
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
            <CardTitle className="text-lg">Valor por Estado</CardTitle>
            <CardDescription>Monto total en millones de pesos</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis 
                    dataKey="estado" 
                    stroke="#6b7280"
                    tick={{ fill: '#6b7280', fontSize: 12 }}
                  />
                  <YAxis 
                    tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                    stroke="#6b7280"
                    tick={{ fill: '#6b7280', fontSize: 12 }}
                  />
                  <Tooltip 
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Bar 
                    dataKey="valor" 
                    fill="#10b981" 
                    radius={[8, 8, 0, 0]}
                    maxBarSize={60}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[320px] flex items-center justify-center text-gray-500">
                No hay datos disponibles
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Transacciones Recientes - Tabla Mejorada */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Transacciones Recientes</CardTitle>
              <CardDescription>Últimas facturas procesadas con notas aplicadas</CardDescription>
            </div>
            {transacciones.length > 0 && (
              <span className="text-sm font-medium text-gray-500">
                {transacciones.length} registros
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {transacciones.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50/50 border-b border-gray-200">
                    <th className="text-left py-4 px-6 font-semibold text-sm text-gray-700">Factura</th>
                    <th className="text-left py-4 px-6 font-semibold text-sm text-gray-700">Cliente</th>
                    <th className="text-right py-4 px-6 font-semibold text-sm text-gray-700">Valor Total</th>
                    <th className="text-right py-4 px-6 font-semibold text-sm text-gray-700">Valor Transado</th>
                    <th className="text-center py-4 px-6 font-semibold text-sm text-gray-700">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {transacciones.slice(0, 5).map((t, index) => (
                    <tr 
                      key={t.id} 
                      className="hover:bg-gray-50/50 transition-colors group"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                            <Receipt className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 group-hover:text-emerald-600 transition-colors">
                              {t.numero_factura}
                            </p>
                            <p className="text-xs text-gray-500">
                              {new Date(t.fecha_factura).toLocaleDateString('es-CO', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric'
                              })}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <div>
                          <p className="font-medium text-gray-900 truncate max-w-xs">
                            {t.nombre_cliente}
                          </p>
                          <p className="text-xs text-gray-500 font-mono">
                            {t.nit_cliente}
                          </p>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <span className="font-semibold text-gray-900">
                          {formatCurrency(t.valor_total)}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <span className="font-bold text-emerald-600">
                          {formatCurrency(t.valor_transado)}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-center">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${
                          t.tiene_nota_credito
                            ? 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border border-blue-200'
                            : 'bg-gradient-to-r from-gray-50 to-gray-100 text-gray-700 border border-gray-200'
                        }`}>
                          {t.tiene_nota_credito && (
                            <CheckCircle className="w-3.5 h-3.5" />
                          )}
                          {t.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Receipt className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500 font-medium">No hay transacciones registradas</p>
              <p className="text-sm text-gray-400 mt-1">Las transacciones aparecerán aquí una vez procesadas</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}