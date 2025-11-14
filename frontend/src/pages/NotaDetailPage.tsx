import { useParams, useNavigate } from 'react-router-dom'
import { useNota, useAplicaciones } from '@/hooks/useNotas'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatCurrency, formatDate, formatDateTime } from '@/lib/utils'
import { ArrowLeft, FileText, User, Package, Calendar, DollarSign } from 'lucide-react'

export default function NotaDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: nota, isLoading: loadingNota } = useNota(Number(id))
  const { data: aplicaciones, isLoading: loadingAplicaciones } = useAplicaciones(nota?.numero_nota || '')

  if (loadingNota) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Cargando detalles...</div>
      </div>
    )
  }

  if (!nota) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="text-muted-foreground">Nota no encontrada</div>
        <Button onClick={() => navigate('/dashboard/notas')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver al listado
        </Button>
      </div>
    )
  }

  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'PENDIENTE':
        return <Badge variant="warning">{estado}</Badge>
      case 'PARCIAL':
        return <Badge variant="secondary">{estado}</Badge>
      case 'APLICADA':
        return <Badge variant="success">{estado}</Badge>
      default:
        return <Badge>{estado}</Badge>
    }
  }

  const porcentajeAplicado = ((Math.abs(nota.valor_total) - Math.abs(nota.saldo_pendiente)) / Math.abs(nota.valor_total)) * 100

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/dashboard/notas')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Nota {nota.numero_nota}
            </h1>
            <p className="text-muted-foreground">
              Detalles y historial de aplicaciones
            </p>
          </div>
        </div>
        {getEstadoBadge(nota.estado)}
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Valor Total
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(Math.abs(nota.valor_total))}
            </div>
            <p className="text-xs text-muted-foreground">
              Cantidad: {nota.cantidad}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Saldo Pendiente
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(Math.abs(nota.saldo_pendiente))}
            </div>
            <p className="text-xs text-muted-foreground">
              Cantidad pendiente: {nota.cantidad_pendiente}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Porcentaje Aplicado
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {porcentajeAplicado.toFixed(1)}%
            </div>
            <div className="w-full bg-secondary rounded-full h-2 mt-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${porcentajeAplicado}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Details */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Información de la Nota</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Número de Nota</p>
                <p className="text-sm text-muted-foreground">{nota.numero_nota}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Fecha de Nota</p>
                <p className="text-sm text-muted-foreground">{formatDate(nota.fecha_nota)}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Fecha de Registro</p>
                <p className="text-sm text-muted-foreground">{formatDateTime(nota.fecha_registro)}</p>
              </div>
            </div>
            {nota.fecha_aplicacion_completa && (
              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">Fecha de Aplicación Completa</p>
                  <p className="text-sm text-muted-foreground">{formatDateTime(nota.fecha_aplicacion_completa)}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Información del Cliente</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              <User className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Cliente</p>
                <p className="text-sm text-muted-foreground">{nota.nombre_cliente}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">NIT</p>
                <p className="text-sm text-muted-foreground">{nota.nit_cliente}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Package className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Producto</p>
                <p className="text-sm text-muted-foreground">{nota.nombre_producto}</p>
                <p className="text-xs text-muted-foreground">Código: {nota.codigo_producto}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Tipo de Inventario</p>
                <p className="text-sm text-muted-foreground">{nota.tipo_inventario}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Aplicaciones History */}
      <Card>
        <CardHeader>
          <CardTitle>Historial de Aplicaciones</CardTitle>
          <CardDescription>
            {aplicaciones?.length || 0} aplicaciones registradas
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingAplicaciones ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-muted-foreground">Cargando aplicaciones...</div>
            </div>
          ) : aplicaciones && aplicaciones.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Factura</TableHead>
                  <TableHead>Fecha Factura</TableHead>
                  <TableHead className="text-right">Valor Aplicado</TableHead>
                  <TableHead className="text-right">Cantidad Aplicada</TableHead>
                  <TableHead>Fecha Aplicación</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {aplicaciones.map((aplicacion) => (
                  <TableRow key={aplicacion.id}>
                    <TableCell className="font-medium">{aplicacion.numero_factura}</TableCell>
                    <TableCell>{formatDate(aplicacion.fecha_factura)}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(Math.abs(aplicacion.valor_aplicado))}
                    </TableCell>
                    <TableCell className="text-right">
                      {aplicacion.cantidad_aplicada}
                    </TableCell>
                    <TableCell>{formatDateTime(aplicacion.fecha_aplicacion)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="text-muted-foreground">
                No hay aplicaciones registradas para esta nota
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
