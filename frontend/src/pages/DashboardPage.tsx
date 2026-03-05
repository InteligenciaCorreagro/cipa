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
    { label: 'Lineas Registradas', value: estadisticasFacturas?.facturas_validas || 0, icon: Layers }
  ]

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-destructive/10 flex items-center justify-center">
          <ServerCrash className="h-7 w-7 text-destructive" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold text-foreground">Error al cargar el dashboard</h3>
          <p className="text-muted-foreground max-w-md text-sm">{error}</p>
        </div>
        <Button onClick={fetchData} size="sm">
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
          <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
          <p className="text-muted-foreground text-sm">Cargando estadisticas...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1 text-sm">Notas, facturas y transado mensual</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm" className="gap-2">
          <RefreshCw className="h-3.5 w-3.5" />
          Actualizar
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <Card key={card.label} className="border border-border">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{card.label}</p>
                    <p className="text-xl font-semibold text-foreground mt-2">{card.value}</p>
                  </div>
                  <div className="h-9 w-9 rounded-lg bg-primary/8 flex items-center justify-center">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Transado Mes a Mes</CardTitle>
            <CardDescription>Valor aplicado por mes (ultimos 12 meses)</CardDescription>
          </CardHeader>
          <CardContent>
            {transadoPorMes.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={transadoPorMes}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(150 10% 92%)" />
                  <XAxis dataKey="mes" stroke="hsl(160 6% 46%)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(160 6% 46%)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${Math.round(value / 1000000)}M`} />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} contentStyle={{ border: '1px solid hsl(150 10% 90%)', borderRadius: '10px', fontSize: '13px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)' }} />
                  <Bar dataKey="valor" fill="hsl(152 60% 32%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-muted-foreground text-sm">No hay transacciones para graficar</div>
            )}
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-foreground">Notas por Estado</CardTitle>
            <CardDescription>Distribucion de notas en el sistema</CardDescription>
          </CardHeader>
          <CardContent>
            {notasPorEstado.some((item) => item.cantidad > 0) ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={notasPorEstado}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(150 10% 92%)" />
                  <XAxis dataKey="estado" stroke="hsl(160 6% 46%)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(160 6% 46%)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={{ border: '1px solid hsl(150 10% 90%)', borderRadius: '10px', fontSize: '13px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)' }} />
                  <Bar dataKey="cantidad" fill="hsl(140 40% 44%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[280px] flex items-center justify-center text-muted-foreground text-sm">No hay notas para graficar</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Ultimas Transacciones</CardTitle>
          <CardDescription>Aplicaciones recientes de notas a facturas</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {transacciones.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Nota</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Factura</th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">NIT</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Valor</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Cantidad</th>
                    <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Kilos</th>
                    <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">Fecha</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {transacciones.slice(0, 10).map((item) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4 text-sm text-foreground font-medium">{item.numero_nota}</td>
                      <td className="py-3 px-4 text-sm text-foreground font-medium">{item.numero_factura}</td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">{item.nit_cliente || '-'}</td>
                      <td className="py-3 px-4 text-sm text-right font-medium text-foreground">{formatCurrency(item.valor_aplicado || 0)}</td>
                      <td className="py-3 px-4 text-sm text-right text-muted-foreground">{Number(item.cantidad_aplicada || 0).toFixed(2)}</td>
                      <td className="py-3 px-4 text-sm text-right text-muted-foreground">{Number(item.cantidad_aplicada_kilos || 0).toFixed(2)}</td>
                      <td className="py-3 px-4 text-xs text-center text-muted-foreground">
                        {new Date(item.fecha_aplicacion).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground text-sm">No hay transacciones registradas</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
