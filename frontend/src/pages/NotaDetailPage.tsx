import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table } from '@/components/ui/table'
import { formatCurrency } from '@/lib/utils'
import { 
  ArrowLeft, 
  FileText, 
  User, 
  Package, 
  Calendar, 
  DollarSign, 
  Clock, 
  CheckCircle,
  AlertCircle,
  Loader2,
  Receipt,
  TrendingUp
} from 'lucide-react'
import { notasApi } from '@/services/api'
import type { NotaCredito } from '@/types'

// Función para formatear fecha
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('es-CO', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  })
}

// Función para formatear fecha y hora
const formatDateTime = (dateString: string) => {
  return new Date(dateString).toLocaleString('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

type Nota = NotaCredito & {
  aplicaciones?: Aplicacion[]
  motivos_no_aplicacion?: { motivo: string; detalle?: string; fecha_registro: string }[]
}

interface Aplicacion {
  id: number
  numero_factura: string
  fecha_factura: string
  valor_aplicado: number
  cantidad_aplicada: number
  fecha_aplicacion: string
}

export default function NotaDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [nota, setNota] = useState<Nota | null>(null)
  const [aplicaciones, setAplicaciones] = useState<Aplicacion[]>([])
  const [loadingNota, setLoadingNota] = useState(true)
  const [loadingAplicaciones, setLoadingAplicaciones] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchNota = useCallback(async () => {
    try {
      setLoadingNota(true)
      const response = await notasApi.getNota(Number(id))
      setNota(response)
      setAplicaciones(response.aplicaciones || [])
      setLoadingAplicaciones(false)
      setError(null)
    } catch (err) {
      console.error('Error al cargar nota:', err)
      const message = err instanceof Error ? err.message : 'Error al cargar la nota'
      setError(message)
    } finally {
      setLoadingNota(false)
    }
  }, [id])

  useEffect(() => {
    fetchNota()
  }, [fetchNota])

  if (loadingNota) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
          <p className="text-muted-foreground text-sm">Cargando detalles...</p>
        </div>
      </div>
    )
  }

  if (error || !nota) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-12 h-12 bg-destructive/8 rounded-xl flex items-center justify-center">
          <AlertCircle className="w-6 h-6 text-destructive" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-lg font-semibold text-foreground">
            {error || 'Nota no encontrada'}
          </h3>
          <p className="text-muted-foreground text-sm">La nota que buscas no existe o no tienes permisos</p>
        </div>
        <Button 
          onClick={() => navigate('/notas')}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver al listado
        </Button>
      </div>
    )
  }

  const getEstadoBadge = (estado: string) => {
    const estados: Record<string, { icon: typeof Clock }> = {
      'PENDIENTE': { icon: Clock },
      'APLICADA': { icon: CheckCircle },
      'NO_APLICADA': { icon: AlertCircle }
    }
    const config = estados[estado] || { icon: FileText }
    const Icon = config.icon
    
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r border-2"
        style={{
          background: estado === 'APLICADA' 
            ? 'linear-gradient(to right, rgb(236 253 245), rgb(209 250 229))'
            : estado === 'NO_APLICADA'
            ? 'linear-gradient(to right, rgb(254 226 226), rgb(254 202 202))'
            : 'linear-gradient(to right, rgb(255 247 237), rgb(254 243 199))',
          borderColor: estado === 'APLICADA'
            ? '#10b981'
            : estado === 'NO_APLICADA'
            ? '#ef4444'
            : '#f59e0b'
        }}
      >
        <Icon className="w-4 h-4" style={{ 
          color: estado === 'APLICADA' ? '#10b981' : estado === 'NO_APLICADA' ? '#ef4444' : '#f59e0b' 
        }} />
        <span className="font-semibold text-sm" style={{ 
          color: estado === 'APLICADA' ? '#059669' : estado === 'NO_APLICADA' ? '#dc2626' : '#d97706' 
        }}>
          {estado}
        </span>
      </div>
    )
  }

  const porcentajeAplicado = ((Math.abs(nota.valor_total) - Math.abs(nota.saldo_pendiente)) / Math.abs(nota.valor_total)) * 100

  // Columnas para la tabla de aplicaciones
  const columns = [
    {
      key: 'factura',
      label: 'Factura',
      render: (aplicacion: Aplicacion) => (
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary/8 flex items-center justify-center flex-shrink-0">
            <Receipt className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="font-medium text-foreground">{aplicacion.numero_factura}</p>
            <p className="text-xs text-muted-foreground">
              {formatDate(aplicacion.fecha_factura)}
            </p>
          </div>
        </div>
      )
    },
    {
      key: 'valor',
      label: 'Valor Aplicado',
      align: 'right' as const,
      render: (aplicacion: Aplicacion) => (
        <div className="text-right">
          <p className="font-medium text-primary">
            {formatCurrency(Math.abs(aplicacion.valor_aplicado))}
          </p>
          <p className="text-xs text-muted-foreground">
            Cant: {aplicacion.cantidad_aplicada}
          </p>
        </div>
      )
    },
    {
      key: 'fecha',
      label: 'Fecha Aplicacion',
      render: (aplicacion: Aplicacion) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-foreground">
            {formatDateTime(aplicacion.fecha_aplicacion)}
          </span>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/notas')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Nota {nota.numero_nota}
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Detalles y historial de aplicaciones
            </p>
          </div>
        </div>
        {getEstadoBadge(nota.estado)}
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <DollarSign className="h-4 w-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Valor Total</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">
              {formatCurrency(Math.abs(nota.valor_total))}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Cantidad: <span className="font-medium">{nota.cantidad}</span>
            </p>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <AlertCircle className="h-4 w-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Saldo Pendiente</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">
              {formatCurrency(Math.abs(nota.saldo_pendiente))}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Cantidad pendiente: <span className="font-medium">{nota.cantidad_pendiente}</span>
            </p>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <TrendingUp className="h-4 w-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Porcentaje Aplicado</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">
              {porcentajeAplicado.toFixed(1)}%
            </p>
            <div className="w-full bg-muted rounded-full h-2 mt-3 overflow-hidden">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-500"
                style={{ width: `${porcentajeAplicado}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Details */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border border-border">
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Informacion de la Nota</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <FileText className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">Numero de Nota</p>
                <p className="text-sm text-foreground font-medium mt-0.5">{nota.numero_nota}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <Calendar className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">Fecha de Nota</p>
                <p className="text-sm text-foreground font-medium mt-0.5">{formatDate(nota.fecha_nota)}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <Clock className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">Fecha de Registro</p>
                <p className="text-sm text-foreground font-medium mt-0.5">{formatDateTime(nota.fecha_registro)}</p>
              </div>
            </div>
            
            {nota.fecha_aplicacion_completa && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/10">
                <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-xs font-medium text-muted-foreground">Aplicacion Completa</p>
                  <p className="text-sm text-primary font-medium mt-0.5">{formatDateTime(nota.fecha_aplicacion_completa)}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Informacion del Cliente</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <User className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">Cliente</p>
                <p className="text-sm text-foreground font-medium mt-0.5">{nota.nombre_cliente}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <FileText className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">NIT</p>
                <p className="text-sm text-foreground font-mono font-medium mt-0.5">{nota.nit_cliente}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <Package className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-medium text-muted-foreground">Producto</p>
                <p className="text-sm text-foreground font-medium mt-0.5">{nota.nombre_producto}</p>
                <p className="text-xs text-muted-foreground mt-0.5">Codigo: <span className="font-mono">{nota.codigo_producto}</span></p>
              </div>
            </div>
            
          </CardContent>
        </Card>
      </div>

      {/* Aplicaciones History */}
      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Receipt className="w-4 h-4 text-primary" />
                <CardTitle className="text-base font-semibold text-foreground">Historial de Aplicaciones</CardTitle>
              </div>
              <CardDescription className="mt-1">
                {aplicaciones.length} {aplicaciones.length === 1 ? 'aplicacion registrada' : 'aplicaciones registradas'}
              </CardDescription>
            </div>
            {aplicaciones.length > 0 && (
              <Badge variant="info" className="text-xs">
                Total: {aplicaciones.length}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loadingAplicaciones ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center space-y-3">
                <Loader2 className="w-6 h-6 text-primary animate-spin mx-auto" />
                <p className="text-muted-foreground text-sm">Cargando aplicaciones...</p>
              </div>
            </div>
          ) : aplicaciones && aplicaciones.length > 0 ? (
            <Table
              columns={columns}
              data={aplicaciones}
              keyExtractor={(aplicacion) => aplicacion.id.toString()}
              hoverable
              bordered
              compact
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-48 space-y-3">
              <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center">
                <Receipt className="w-6 h-6 text-muted-foreground" />
              </div>
              <div className="text-center">
                <p className="text-foreground font-medium text-sm">Sin aplicaciones</p>
                <p className="text-xs text-muted-foreground mt-1">
                  No hay aplicaciones registradas para esta nota
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
