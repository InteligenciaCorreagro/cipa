import { useCallback, useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, Badge } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { facturasApi } from '@/services/api'
import { FileText, RefreshCw, AlertCircle } from 'lucide-react'
import DetailModal from '@/components/DetailModal'

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

interface FacturaRow {
  id: number
  numero_factura: string
  codigo_factura: string
  fecha_factura: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  cantidad_original: number
  cantidad_restante: number
  valor_total: number
  valor_restante: number
  registrable: number
  total_repeticiones: number
  suma_total_repeticiones: number
}

interface FacturasStats {
  facturas_validas: number
  facturas_registrables: number
  facturas_no_registrables: number
  facturas_rechazadas: number
  total_aplicado: number
  valor_total_facturado: number
}

export default function FacturasPage() {
  const [facturas, setFacturas] = useState<FacturaRow[]>([])
  const [stats, setStats] = useState<FacturasStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<FacturaRow | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    fecha_desde: '',
    fecha_hasta: '',
    estado: '',
    registrable: '',
    con_nota: '',
    numero_factura: '',
    nombre_cliente: '',
    orden: 'fecha_factura',
    direccion: 'DESC'
  })
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const pageSize = 25

  const fetchFacturas = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [facturasRes, statsRes] = await Promise.allSettled([
        facturasApi.getFacturas({
          search: searchTerm || undefined,
          fecha_desde: filters.fecha_desde || undefined,
          fecha_hasta: filters.fecha_hasta || undefined,
          estado: filters.estado || undefined,
          registrable: filters.registrable ? filters.registrable === 'true' : undefined,
          con_nota: filters.con_nota ? filters.con_nota === 'true' : undefined,
          numero_factura: filters.numero_factura || undefined,
          nombre_cliente: filters.nombre_cliente || undefined,
          orden: filters.orden,
          direccion: filters.direccion,
          limite: pageSize,
          offset: page * pageSize
        }),
        facturasApi.getEstadisticas()
      ])
      if (facturasRes.status === 'fulfilled') {
        const response = facturasRes.value
        setFacturas(response.items || [])
        setTotal(response.total || 0)
      } else {
        setFacturas([])
        setTotal(0)
        throw facturasRes.reason
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'No se pudo cargar facturas'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [searchTerm, filters, page, pageSize])

  useEffect(() => {
    fetchFacturas()
    const interval = setInterval(fetchFacturas, 30000)
    return () => clearInterval(interval)
  }, [fetchFacturas])

  const totalPages = useMemo(() => Math.ceil(total / pageSize), [total, pageSize])
  const pageNumbers = useMemo(() => {
    const pages: number[] = []
    const start = Math.max(1, page + 1 - 2)
    const end = Math.min(totalPages || 1, page + 1 + 2)
    for (let i = start; i <= end; i += 1) {
      pages.push(i)
    }
    return pages
  }, [page, totalPages])

  const resumen = useMemo(() => {
    return [
      { label: 'Facturas válidas', value: stats?.facturas_validas ?? total },
      { label: 'Registrables', value: stats?.facturas_registrables ?? facturas.filter((f) => f.registrable).length },
      { label: 'Rechazadas', value: stats?.facturas_rechazadas ?? 0 },
      { label: 'Total facturado', value: formatCurrency(stats?.valor_total_facturado ?? 0) }
    ]
  }, [stats, total, facturas])

  const formatDate = (value: string) => {
    if (!value) return '-'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '-'
    return date.toLocaleDateString('es-CO')
  }

  const columns = [
    {
      key: 'factura',
      label: 'Factura',
      render: (f: FacturaRow) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-emerald-700" />
          </div>
          <div>
            <p className="font-semibold text-emerald-900">{f.numero_factura}</p>
            <p className="text-xs text-emerald-600">{formatDate(f.fecha_factura)}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'cliente',
      label: 'Cliente',
      render: (f: FacturaRow) => (
        <div>
          <p className="font-medium text-emerald-900">{f.nombre_cliente}</p>
          <p className="text-xs text-emerald-600 font-mono">{f.nit_cliente}</p>
        </div>
      ),
    },
    {
      key: 'producto',
      label: 'Producto',
      render: (f: FacturaRow) => (
        <div>
          <p className="font-medium text-emerald-900">{f.nombre_producto}</p>
          <p className="text-xs text-emerald-600 font-mono">{f.codigo_producto}</p>
        </div>
      ),
    },
    {
      key: 'valor',
      label: 'Valor',
      align: 'right' as const,
      render: (f: FacturaRow) => (
        <span className="font-semibold text-emerald-900">{formatCurrency(f.valor_total)}</span>
      ),
    },
    {
      key: 'registrable',
      label: 'Registrable',
      align: 'center' as const,
      render: (f: FacturaRow) => (
        <Badge variant={f.registrable ? 'success' : 'danger'}>
          {f.registrable ? 'Sí' : 'No'}
        </Badge>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-emerald-900">Facturas</h1>
          <p className="text-emerald-700 mt-1">Vista operativa de facturas y estado de aplicación</p>
        </div>
        <Button onClick={fetchFacturas} variant="outline" size="sm" className="gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {resumen.map((item) => (
          <Card key={item.label} className="border border-emerald-100 shadow-sm">
            <CardContent className="p-5">
              <p className="text-sm text-emerald-700">{item.label}</p>
              <p className="text-2xl font-bold text-emerald-900 mt-1">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {error && (
        <Card className="border border-emerald-200 bg-emerald-50/50">
          <CardContent className="flex items-center gap-3 p-4 text-emerald-800">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </CardContent>
        </Card>
      )}

      <Card className="border border-emerald-100 shadow-sm">
        <CardHeader>
          <CardTitle className="text-emerald-900">Filtros</CardTitle>
          <CardDescription className="text-emerald-700">Fecha, estado, cliente y orden</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Input className="border-emerald-200" placeholder="Número factura" value={filters.numero_factura} onChange={(e) => setFilters({ ...filters, numero_factura: e.target.value })} />
          <Input className="border-emerald-200" placeholder="Nombre cliente" value={filters.nombre_cliente} onChange={(e) => setFilters({ ...filters, nombre_cliente: e.target.value })} />
          <Input className="border-emerald-200" type="date" value={filters.fecha_desde} onChange={(e) => setFilters({ ...filters, fecha_desde: e.target.value })} />
          <Input className="border-emerald-200" type="date" value={filters.fecha_hasta} onChange={(e) => setFilters({ ...filters, fecha_hasta: e.target.value })} />
          <Select value={filters.estado || 'ALL'} onValueChange={(value) => setFilters({ ...filters, estado: value === 'ALL' ? '' : value })}>
            <SelectTrigger className="border-emerald-200">
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos</SelectItem>
              <SelectItem value="ACTIVA">Activa</SelectItem>
              <SelectItem value="ANULADA">Anulada</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.registrable || 'ALL'} onValueChange={(value) => setFilters({ ...filters, registrable: value === 'ALL' ? '' : value })}>
            <SelectTrigger className="border-emerald-200">
              <SelectValue placeholder="Registrable" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos</SelectItem>
              <SelectItem value="true">Sí</SelectItem>
              <SelectItem value="false">No</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.con_nota || 'ALL'} onValueChange={(value) => setFilters({ ...filters, con_nota: value === 'ALL' ? '' : value })}>
            <SelectTrigger className="border-emerald-200">
              <SelectValue placeholder="Con nota" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos</SelectItem>
              <SelectItem value="true">Con nota</SelectItem>
              <SelectItem value="false">Sin nota</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.orden} onValueChange={(value) => setFilters({ ...filters, orden: value })}>
            <SelectTrigger className="border-emerald-200">
              <SelectValue placeholder="Orden" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fecha_factura">Fecha</SelectItem>
              <SelectItem value="numero_factura">Número</SelectItem>
              <SelectItem value="valor_total">Valor</SelectItem>
              <SelectItem value="nombre_cliente">Cliente</SelectItem>
              <SelectItem value="nit_cliente">NIT</SelectItem>
              <SelectItem value="codigo_factura">Código</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filters.direccion} onValueChange={(value) => setFilters({ ...filters, direccion: value })}>
            <SelectTrigger className="border-emerald-200">
              <SelectValue placeholder="Dirección" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DESC">Descendente</SelectItem>
              <SelectItem value="ASC">Ascendente</SelectItem>
            </SelectContent>
          </Select>
          <Input
            className="border-emerald-200"
            placeholder="Búsqueda global"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Button onClick={fetchFacturas} variant="outline" className="md:col-span-4 border-emerald-200 text-emerald-700 hover:bg-emerald-50">
            Aplicar filtros
          </Button>
        </CardContent>
      </Card>

      <Card className="border border-emerald-100 shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-emerald-900">Listado de Facturas</CardTitle>
              <CardDescription className="text-emerald-700">{total} registros</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table
            columns={columns}
            data={facturas}
            keyExtractor={(f) => f.id.toString()}
            loading={loading}
            emptyMessage="No hay facturas registradas"
            hoverable
            bordered
            enablePagination={false}
            onRowClick={(row) => setSelected(row)}
          />
          <div className="flex items-center justify-between p-4">
            <div className="text-sm text-emerald-700">
              Página {page + 1} de {totalPages || 1}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50" onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
                Anterior
              </Button>
              {pageNumbers.map((pageNumber) => (
                <Button
                  key={pageNumber}
                  variant={pageNumber === page + 1 ? 'default' : 'outline'}
                  size="sm"
                  className={pageNumber === page + 1 ? '' : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'}
                  onClick={() => setPage(pageNumber - 1)}
                >
                  {pageNumber}
                </Button>
              ))}
              <Button variant="outline" size="sm" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50" onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page + 1 >= totalPages}>
                Siguiente
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      <DetailModal
        open={!!selected}
        title={`Detalle factura ${selected?.numero_factura ?? ''}`}
        description="Información operativa de la línea seleccionada"
        onClose={() => setSelected(null)}
      >
        {selected ? (
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs text-emerald-600">Número factura</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.numero_factura}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Fecha</p>
              <p className="text-sm font-semibold text-emerald-900">{formatDate(selected.fecha_factura)}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Cliente</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.nombre_cliente}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">NIT</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.nit_cliente}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Producto</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.nombre_producto}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Código producto</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.codigo_producto}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Cantidad original</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.cantidad_original.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Cantidad restante</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.cantidad_restante.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Valor total</p>
              <p className="text-sm font-semibold text-emerald-900">{formatCurrency(selected.valor_total)}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Valor restante</p>
              <p className="text-sm font-semibold text-emerald-900">{formatCurrency(selected.valor_restante)}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Código factura</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.codigo_factura}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Registrable</p>
              <p className="text-sm font-semibold text-emerald-900">{selected.registrable ? 'Sí' : 'No'}</p>
            </div>
          </div>
        ) : null}
      </DetailModal>
    </div>
  )
}
