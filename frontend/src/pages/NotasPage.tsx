import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotas } from '@/hooks/useNotas'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
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
import { formatCurrency, formatDate } from '@/lib/utils'
import { Search, Eye, ChevronLeft, ChevronRight } from 'lucide-react'

const LIMITE = 50

export default function NotasPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [estado, setEstado] = useState<string>('')
  const [offset, setOffset] = useState(0)

  const { data, isLoading } = useNotas({
    estado: estado || undefined,
    nit_cliente: search || undefined,
    limite: LIMITE,
    offset,
  })

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

  const handleNext = () => {
    if (data && offset + LIMITE < data.total) {
      setOffset(offset + LIMITE)
    }
  }

  const handlePrevious = () => {
    if (offset >= LIMITE) {
      setOffset(offset - LIMITE)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Notas de Crédito</h1>
        <p className="text-muted-foreground">
          Gestión y seguimiento de notas de crédito
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Buscar y filtrar notas de crédito
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por NIT cliente..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setOffset(0)
                }}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={estado === '' ? 'default' : 'outline'}
                onClick={() => {
                  setEstado('')
                  setOffset(0)
                }}
                size="sm"
              >
                Todos
              </Button>
              <Button
                variant={estado === 'PENDIENTE' ? 'default' : 'outline'}
                onClick={() => {
                  setEstado('PENDIENTE')
                  setOffset(0)
                }}
                size="sm"
              >
                Pendientes
              </Button>
              <Button
                variant={estado === 'PARCIAL' ? 'default' : 'outline'}
                onClick={() => {
                  setEstado('PARCIAL')
                  setOffset(0)
                }}
                size="sm"
              >
                Parciales
              </Button>
              <Button
                variant={estado === 'APLICADA' ? 'default' : 'outline'}
                onClick={() => {
                  setEstado('APLICADA')
                  setOffset(0)
                }}
                size="sm"
              >
                Aplicadas
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Listado de Notas</CardTitle>
          <CardDescription>
            {data ? `Mostrando ${offset + 1} - ${Math.min(offset + LIMITE, data.total)} de ${data.total} notas` : 'Cargando...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">Cargando notas...</div>
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Número</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Producto</TableHead>
                    <TableHead className="text-right">Valor Total</TableHead>
                    <TableHead className="text-right">Saldo Pendiente</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((nota) => (
                    <TableRow key={nota.id}>
                      <TableCell className="font-medium">{nota.numero_nota}</TableCell>
                      <TableCell>{formatDate(nota.fecha_nota)}</TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{nota.nombre_cliente}</div>
                          <div className="text-xs text-muted-foreground">{nota.nit_cliente}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{nota.nombre_producto}</div>
                          <div className="text-xs text-muted-foreground">{nota.codigo_producto}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(Math.abs(nota.valor_total))}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(Math.abs(nota.saldo_pendiente))}
                      </TableCell>
                      <TableCell>{getEstadoBadge(nota.estado)}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/notas/${nota.id}`)}
                          title="Ver detalles"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrevious}
                  disabled={offset === 0}
                >
                  <ChevronLeft className="h-4 w-4 mr-2" />
                  Anterior
                </Button>
                <span className="text-sm text-muted-foreground">
                  Página {Math.floor(offset / LIMITE) + 1} de {Math.ceil(data.total / LIMITE)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNext}
                  disabled={offset + LIMITE >= data.total}
                >
                  Siguiente
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">No se encontraron notas</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
