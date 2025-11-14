import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotas } from '@/hooks/useNotas'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SortableTable, Column } from '@/components/ui/sortable-table'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Search, Eye, ChevronLeft, ChevronRight, ServerCrash, RefreshCw } from 'lucide-react'
import type { NotaCredito } from '@/types'

const LIMITE = 50

export default function NotasPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [estado, setEstado] = useState<string>('')
  const [offset, setOffset] = useState(0)

  const { data, isLoading, error, refetch } = useNotas({
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
          <div className="font-medium">{nota.nombre_cliente}</div>
          <div className="text-xs text-muted-foreground">{nota.nit_cliente}</div>
        </div>
      ),
    },
    {
      key: 'nombre_producto',
      label: 'Producto',
      render: (nota) => (
        <div>
          <div className="font-medium">{nota.nombre_producto}</div>
          <div className="text-xs text-muted-foreground">{nota.codigo_producto}</div>
        </div>
      ),
    },
    {
      key: 'valor_total',
      label: 'Valor Total',
      className: 'text-right',
      render: (nota) => <span className="font-medium">{formatCurrency(Math.abs(nota.valor_total))}</span>,
    },
    {
      key: 'saldo_pendiente',
      label: 'Saldo Pendiente',
      className: 'text-right',
      render: (nota) => <span className="font-medium">{formatCurrency(Math.abs(nota.saldo_pendiente))}</span>,
    },
    {
      key: 'estado',
      label: 'Estado',
      render: (nota) => getEstadoBadge(nota.estado),
    },
    {
      key: 'acciones',
      label: '',
      sortable: false,
      render: (nota) => (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/dashboard/notas/${nota.id}`)}
          title="Ver detalles"
        >
          <Eye className="h-4 w-4" />
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Consulta de Notas</h1>
        <p className="text-muted-foreground">
          Visualización y consulta de información de notas
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Buscar y filtrar notas
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
          {error ? (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
              <ServerCrash className="h-12 w-12 text-muted-foreground" />
              <div className="text-center space-y-2">
                <h3 className="text-lg font-semibold">Error al cargar las notas</h3>
                <p className="text-muted-foreground max-w-md">
                  No se pudo conectar con la API. Por favor, verifica que el servidor esté funcionando.
                </p>
                <p className="text-sm text-muted-foreground">
                  Error: {(error as any)?.message || 'Error de conexión'}
                </p>
              </div>
              <Button onClick={() => refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Reintentar
              </Button>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">Cargando notas...</div>
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <SortableTable
                data={data.items}
                columns={notasColumns}
                emptyMessage="No se encontraron notas"
              />

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
