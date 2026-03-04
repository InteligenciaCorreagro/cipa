import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw, ServerCrash, Receipt, Loader2, CheckCircle2, Layers } from 'lucide-react'
import { ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import { api } from '@/services/api'

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

interface Estadisticas {
  total_notas: number
  valor_total: number
  saldo_pendiente_total: number
  notas_pendientes: number
  notas_aplicadas: number
  notas_no_aplicadas: number
  total_aplicaciones: number
  monto_total_aplicado: number
}

interface EstadisticasFacturas {
  facturas_validas: number
  valor_total_facturado: number
  facturas_registrables: number
  facturas_no_registrables: number
  facturas_rechazadas: number
  aplicaciones_total: number
  total_aplicado: number
}

interface Transaccion {
  id: number
  numero_nota: string
  numero_factura: string
  nit_cliente?: string
  valor_aplicado: number
  cantidad_aplicada: number
  cantidad_aplicada_kilos?: number
  fecha_aplicacion: string
}

export default function DashboardPage() {
  const [estadisticas, setEstadisticas] = useState<Estadisticas | null>(null)
  const [estadisticasFacturas, setEstadisticasFacturas] = useState<EstadisticasFacturas | null>(null)
  const [transacciones, setTransacciones] = useState<Transaccion[]>([])
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [statsRes, facturasRes, transaccionesRes] = await Promise.allSettled([
        api.get('/api/notas/estadisticas'),
        api.get('/api/facturas/estadisticas'),
        api.get('/api/facturas/transacciones', { params: { limite: 1200, offset: 0 } })
      ])

      if (statsRes.status === 'fulfilled') {
        setEstadisticas(statsRes.value.data)
      }
      
      if (facturasRes.status === 'fulfilled') {
        setEstadisticasFacturas(facturasRes.value.data)
      }
      
      if (transaccionesRes.status === 'fulfilled') {
        const data = transaccionesRes.value.data
        setTransacciones(data.items || data.ultimas_aplicaciones || [])
      }

      setLoading(false)
    } catch (err) {
      console.error('Error al cargar dashboard:', err)
      const message = err instanceof Error ? err.message : 'Error al conectar con el servidor'
      setError(message)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const transadoPorMes = useMemo(() => {
    const map = new Map<string, { mes: string; valor: number }>()
    for (const item of transacciones) {
      if (!item.fecha_aplicacion) continue
      const date = new Date(item.fecha_aplicacion)
      if (Number.isNaN(date.getTime())) continue
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const mes = new Intl.DateTimeFormat('es-CO', { month: 'short', year: '2-digit' }).format(date)
      const acumulado = map.get(key)?.valor || 0
      map.set(key, { mes, valor: acumulado + Number(item.valor_aplicado || 0) })
    }
    return [...map.entries()]
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([, value]) => value)
      .slice(-12)
  }, [transacciones])

  const notasPorEstado = useMemo(() => {
    return [
      { estado: 'Pendientes', cantidad: Number(estadisticas?.notas_pendientes || 0) },
      { estado: 'Aplicadas', cantidad: Number(estadisticas?.notas_aplicadas || 0) },
      { estado: 'No aplicadas', cantidad: Number(estadisticas?.notas_no_aplicadas || 0) }
    ]
  }, [estadisticas])

  const cards = [
    { label: 'Transado Facturas Buenas', value: formatCurrency(estadisticasFacturas?.valor_total_facturado || 0), icon: Receipt },
    { label: 'Aplicado por Notas', value: formatCurrency(estadisticas?.monto_total_aplicado || 0), icon: CheckCircle2 },
    { label: 'Pendiente por Notas', value: formatCurrency(estadisticas?.saldo_pendiente_total || 0), icon: AlertCircle },
    { label: 'Líneas Registradas', value: estadisticasFacturas?.facturas_validas || 0, icon: Layers }
  ]

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
        <Button onClick={fetchData} className="bg-emerald-600 hover:bg-emerald-700">
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-emerald-900">Dashboard</h1>
          <p className="text-emerald-700 mt-1">Vista minimalista de notas, facturas y transado mensual</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm" className="gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <Card key={card.label} className="border border-emerald-100 shadow-sm">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-emerald-700">{card.label}</p>
                    <p className="text-2xl font-bold text-emerald-900 mt-1">{card.value}</p>
                  </div>
                  <div className="h-10 w-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-emerald-700" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border border-emerald-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-emerald-900">Transado Mes a Mes</CardTitle>
            <CardDescription className="text-emerald-700">Valor aplicado por mes (últimos 12 meses)</CardDescription>
          </CardHeader>
          <CardContent>
            {transadoPorMes.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={transadoPorMes}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
                  <XAxis dataKey="mes" stroke="#047857" />
                  <YAxis stroke="#047857" tickFormatter={(value) => `${Math.round(value / 1000000)}M`} />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} contentStyle={{ border: '1px solid #a7f3d0', borderRadius: '8px' }} />
                  <Bar dataKey="valor" fill="#059669" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-emerald-600">No hay transacciones para graficar</div>
            )}
          </CardContent>
        </Card>

        <Card className="border border-emerald-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-emerald-900">Notas por Estado</CardTitle>
            <CardDescription className="text-emerald-700">Distribución de notas en el sistema</CardDescription>
          </CardHeader>
          <CardContent>
            {notasPorEstado.some((item) => item.cantidad > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={notasPorEstado}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d1fae5" />
                  <XAxis dataKey="estado" stroke="#047857" />
                  <YAxis stroke="#047857" allowDecimals={false} />
                  <Tooltip contentStyle={{ border: '1px solid #a7f3d0', borderRadius: '8px' }} />
                  <Bar dataKey="cantidad" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-emerald-600">No hay notas para graficar</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border border-emerald-100 shadow-sm">
        <CardHeader>
          <CardTitle className="text-emerald-900">Últimas Transacciones</CardTitle>
          <CardDescription className="text-emerald-700">Aplicaciones recientes de notas a facturas</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {transacciones.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-emerald-50 border-b border-emerald-100">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-emerald-800">Nota</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-emerald-800">Factura</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-emerald-800">NIT</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-emerald-800">Valor</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-emerald-800">Cantidad</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-emerald-800">Kilos</th>
                    <th className="text-center py-3 px-4 text-xs font-semibold text-emerald-800">Fecha</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-emerald-50">
                  {transacciones.slice(0, 10).map((item) => (
                    <tr key={item.id} className="hover:bg-emerald-50/40">
                      <td className="py-3 px-4 text-sm text-emerald-900 font-medium">{item.numero_nota}</td>
                      <td className="py-3 px-4 text-sm text-emerald-900 font-medium">{item.numero_factura}</td>
                      <td className="py-3 px-4 text-sm text-emerald-700">{item.nit_cliente || '-'}</td>
                      <td className="py-3 px-4 text-sm text-right font-semibold text-emerald-700">{formatCurrency(item.valor_aplicado || 0)}</td>
                      <td className="py-3 px-4 text-sm text-right text-emerald-900">{Number(item.cantidad_aplicada || 0).toFixed(2)}</td>
                      <td className="py-3 px-4 text-sm text-right text-emerald-900">{Number(item.cantidad_aplicada_kilos || 0).toFixed(2)}</td>
                      <td className="py-3 px-4 text-xs text-center text-emerald-700">
                        {new Date(item.fecha_aplicacion).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-emerald-700">No hay transacciones registradas</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
