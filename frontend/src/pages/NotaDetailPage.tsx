import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table } from '@/components/ui/Table'
import { formatCurrency } from '@/lib/utils'
import { 
  ArrowLeft, 
  FileText, 
  User, 
  Package, 
  Calendar, 
  DollarSign, 
  Clock, 
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Loader2,
  Receipt
} from 'lucide-react'
import { api } from '@/services/api'

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

interface Nota {
  id: number
  numero_nota: string
  fecha_nota: string
  fecha_registro: string
  fecha_aplicacion_completa?: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  tipo_inventario: string
  cantidad: number
  cantidad_pendiente: number
  valor_total: number
  saldo_pendiente: number
  estado: string
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

  useEffect(() => {
    fetchNota()
  }, [id])

  useEffect(() => {
    if (nota?.numero_nota) {
      fetchAplicaciones()
    }
  }, [nota])

  const fetchNota = async () => {
    try {
      setLoadingNota(true)
      const response = await api.get(`/api/notas/${id}`)
      setNota(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error al cargar nota:', err)
      setError(err.message || 'Error al cargar la nota')
    } finally {
      setLoadingNota(false)
    }
  }

  const fetchAplicaciones = async () => {
    try {
      setLoadingAplicaciones(true)
      const response = await api.get(`/api/notas/${nota?.numero_nota}/aplicaciones`)
      setAplicaciones(response.data || [])
    } catch (err) {
      console.error('Error al cargar aplicaciones:', err)
    } finally {
      setLoadingAplicaciones(false)
    }
  }

  if (loadingNota) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-3">
          <Loader2 className="w-12 h-12 text-emerald-600 animate-spin mx-auto" />
          <p className="text-gray-500">Cargando detalles...</p>
        </div>
      </div>
    )
  }

  if (error || !nota) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-red-600" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-gray-900">
            {error || 'Nota no encontrada'}
          </h3>
          <p className="text-gray-500">La nota que buscas no existe o no tienes permisos</p>
        </div>
        <Button 
          onClick={() => navigate('/notas')}
          className="bg-emerald-600 hover:bg-emerald-700"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver al listado
        </Button>
      </div>
    )
  }

  const getEstadoBadge = (estado: string) => {
    const estados: Record<string, { variant: any; icon: any }> = {
      'PENDIENTE': { variant: 'warning', icon: Clock },
      'PARCIAL': { variant: 'info', icon: TrendingUp },
      'APLICADA': { variant: 'success', icon: CheckCircle }
    }
    const config = estados[estado] || { variant: 'default', icon: FileText }
    const Icon = config.icon
    
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r border-2"
        style={{
          background: estado === 'APLICADA' 
            ? 'linear-gradient(to right, rgb(236 253 245), rgb(209 250 229))'
            : estado === 'PARCIAL'
            ? 'linear-gradient(to right, rgb(239 246 255), rgb(219 234 254))'
            : 'linear-gradient(to right, rgb(255 247 237), rgb(254 243 199))',
          borderColor: estado === 'APLICADA'
            ? '#10b981'
            : estado === 'PARCIAL'
            ? '#3b82f6'
            : '#f59e0b'
        }}
      >
        <Icon className="w-4 h-4" style={{ 
          color: estado === 'APLICADA' ? '#10b981' : estado === 'PARCIAL' ? '#3b82f6' : '#f59e0b' 
        }} />
        <span className="font-semibold text-sm" style={{ 
          color: estado === 'APLICADA' ? '#059669' : estado === 'PARCIAL' ? '#2563eb' : '#d97706' 
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
          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
            <Receipt className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{aplicacion.numero_factura}</p>
            <p className="text-xs text-gray-500">
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
          <p className="font-bold text-emerald-600">
            {formatCurrency(Math.abs(aplicacion.valor_aplicado))}
          </p>
          <p className="text-xs text-gray-500">
            Cant: {aplicacion.cantidad_aplicada}
          </p>
        </div>
      )
    },
    {
      key: 'fecha',
      label: 'Fecha Aplicación',
      render: (aplicacion: Aplicacion) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-700">
            {formatDateTime(aplicacion.fecha_aplicacion)}
          </span>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header con gradiente */}
      <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-2xl p-6 border-2 border-emerald-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/notas')}
              className="hover:bg-white/80"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                Nota {nota.numero_nota}
              </h1>
              <p className="text-gray-600 mt-1">
                Detalles y historial de aplicaciones
              </p>
            </div>
          </div>
          {getEstadoBadge(nota.estado)}
        </div>
      </div>

      {/* Info Cards con diseño mejorado */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="border-2 border-emerald-200 shadow-lg hover:shadow-xl transition-all">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center ring-4 ring-white shadow-sm">
                <DollarSign className="h-7 w-7 text-emerald-600" />
              </div>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Valor Total</h3>
            <p className="text-3xl font-bold text-gray-900 tracking-tight">
              {formatCurrency(Math.abs(nota.valor_total))}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Cantidad: <span className="font-semibold">{nota.cantidad}</span>
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-orange-200 shadow-lg hover:shadow-xl transition-all">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="w-14 h-14 rounded-2xl bg-orange-50 flex items-center justify-center ring-4 ring-white shadow-sm">
                <AlertCircle className="h-7 w-7 text-orange-600" />
              </div>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Saldo Pendiente</h3>
            <p className="text-3xl font-bold text-gray-900 tracking-tight">
              {formatCurrency(Math.abs(nota.saldo_pendiente))}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Cantidad pendiente: <span className="font-semibold">{nota.cantidad_pendiente}</span>
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-blue-200 shadow-lg hover:shadow-xl transition-all">
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center ring-4 ring-white shadow-sm">
                <TrendingUp className="h-7 w-7 text-blue-600" />
              </div>
            </div>
            <h3 className="text-sm font-medium text-gray-600 mb-2">Porcentaje Aplicado</h3>
            <p className="text-3xl font-bold text-gray-900 tracking-tight">
              {porcentajeAplicado.toFixed(1)}%
            </p>
            <div className="w-full bg-gray-200 rounded-full h-3 mt-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-3 rounded-full transition-all duration-500 shadow-sm"
                style={{ width: `${porcentajeAplicado}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Details con diseño mejorado */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-0 shadow-lg">
          <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-600" />
              <CardTitle className="text-lg">Información de la Nota</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pt-6">
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <FileText className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">Número de Nota</p>
                <p className="text-sm text-gray-900 font-medium mt-1">{nota.numero_nota}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <Calendar className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">Fecha de Nota</p>
                <p className="text-sm text-gray-900 font-medium mt-1">{formatDate(nota.fecha_nota)}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <Clock className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">Fecha de Registro</p>
                <p className="text-sm text-gray-900 font-medium mt-1">{formatDateTime(nota.fecha_registro)}</p>
              </div>
            </div>
            
            {nota.fecha_aplicacion_completa && (
              <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-emerald-50 transition-colors border-2 border-emerald-200">
                <CheckCircle className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-700">Aplicación Completa</p>
                  <p className="text-sm text-emerald-700 font-medium mt-1">{formatDateTime(nota.fecha_aplicacion_completa)}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
            <div className="flex items-center gap-2">
              <User className="w-5 h-5 text-blue-600" />
              <CardTitle className="text-lg">Información del Cliente</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pt-6">
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <User className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">Cliente</p>
                <p className="text-sm text-gray-900 font-medium mt-1">{nota.nombre_cliente}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <FileText className="h-5 w-5 text-gray-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">NIT</p>
                <p className="text-sm text-gray-900 font-mono font-medium mt-1">{nota.nit_cliente}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <Package className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">Producto</p>
                <p className="text-sm text-gray-900 font-medium mt-1">{nota.nombre_producto}</p>
                <p className="text-xs text-gray-500 mt-1">Código: <span className="font-mono">{nota.codigo_producto}</span></p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
              <Package className="h-5 w-5 text-orange-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-700">Tipo de Inventario</p>
                <p className="text-sm text-gray-900 font-medium mt-1">{nota.tipo_inventario}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Aplicaciones History con tabla mejorada */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-emerald-600" />
                <CardTitle className="text-lg">Historial de Aplicaciones</CardTitle>
              </div>
              <CardDescription className="mt-1">
                {aplicaciones.length} {aplicaciones.length === 1 ? 'aplicación registrada' : 'aplicaciones registradas'}
              </CardDescription>
            </div>
            {aplicaciones.length > 0 && (
              <Badge variant="info" className="text-sm">
                Total: {aplicaciones.length}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loadingAplicaciones ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center space-y-3">
                <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
                <p className="text-gray-500 text-sm">Cargando aplicaciones...</p>
              </div>
            </div>
          ) : aplicaciones && aplicaciones.length > 0 ? (
            <Table
              columns={columns}
              data={aplicaciones}
              keyExtractor={(aplicacion) => aplicacion.id.toString()}
              hoverable
              bordered
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-48 space-y-3">
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
                <Receipt className="w-8 h-8 text-gray-400" />
              </div>
              <div className="text-center">
                <p className="text-gray-900 font-medium">Sin aplicaciones</p>
                <p className="text-sm text-gray-500 mt-1">
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