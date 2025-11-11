import { useState } from 'react'
import { useTransacciones } from '@/hooks/useFacturas'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { formatCurrency } from '@/lib/utils'
import { Search, Download, RefreshCw, Filter, X, Calendar, DollarSign } from 'lucide-react'

export default function FacturasPage() {
  const [filtros, setFiltros] = useState({
    fecha_desde: '',
    fecha_hasta: '',
    nit_cliente: '',
    codigo_producto: '',
    tipo_inventario: '',
    estado: '',
  })

  const [filtrosAplicados, setFiltrosAplicados] = useState(filtros)
  const [mostrarFiltros, setMostrarFiltros] = useState(false)
  const [paginaActual, setPaginaActual] = useState(0)
  const limite = 20

  const { data: transacciones, isLoading, error, refetch } = useTransacciones({
    ...filtrosAplicados,
    limite,
    offset: paginaActual * limite,
  })

  const handleAplicarFiltros = () => {
    setFiltrosAplicados(filtros)
    setPaginaActual(0)
  }

  const handleLimpiarFiltros = () => {
    const filtrosVacios = {
      fecha_desde: '',
      fecha_hasta: '',
      nit_cliente: '',
      codigo_producto: '',
      tipo_inventario: '',
      estado: '',
    }
    setFiltros(filtrosVacios)
    setFiltrosAplicados(filtrosVacios)
    setPaginaActual(0)
  }

  const handleCambioFiltro = (campo: string, valor: string) => {
    setFiltros(prev => ({ ...prev, [campo]: valor }))
  }

  const totalPaginas = transacciones ? Math.ceil(transacciones.total / limite) : 0

  const handleExportar = () => {
    if (!transacciones?.items) return

    const csv = [
      ['Número Factura', 'Fecha', 'NIT Cliente', 'Cliente', 'Código Producto', 'Producto', 'Tipo Inventario', 'Valor Total', 'Valor Transado', 'Estado'].join(','),
      ...transacciones.items.map(t =>
        [
          t.numero_factura,
          t.fecha_factura,
          t.nit_cliente,
          `"${t.nombre_cliente}"`,
          t.codigo_producto,
          `"${t.nombre_producto}"`,
          t.tipo_inventario || '',
          t.valor_total,
          t.valor_transado,
          t.estado,
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `transacciones_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="text-destructive">Error al cargar las transacciones</div>
        <Button onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Reintentar
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Facturas Transadas</h1>
          <p className="text-muted-foreground">
            Grilla completa de transacciones con filtros avanzados
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setMostrarFiltros(!mostrarFiltros)}>
            <Filter className="mr-2 h-4 w-4" />
            {mostrarFiltros ? 'Ocultar' : 'Mostrar'} Filtros
          </Button>
          <Button variant="outline" onClick={handleExportar} disabled={!transacciones?.items?.length}>
            <Download className="mr-2 h-4 w-4" />
            Exportar CSV
          </Button>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Resumen */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Transacciones</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{transacciones?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              Mostrando {transacciones?.items?.length || 0} de {transacciones?.total || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Valor Total Transado</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(transacciones?.suma_total_transado || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Con filtros aplicados
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Promedio por Transacción</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(
                transacciones?.total
                  ? (transacciones.suma_total_transado || 0) / transacciones.total
                  : 0
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Promedio calculado
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Panel de Filtros */}
      {mostrarFiltros && (
        <Card>
          <CardHeader>
            <CardTitle>Filtros de Búsqueda</CardTitle>
            <CardDescription>Filtra las transacciones por diferentes criterios</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Fecha Desde</label>
                <Input
                  type="date"
                  value={filtros.fecha_desde}
                  onChange={(e) => handleCambioFiltro('fecha_desde', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Fecha Hasta</label>
                <Input
                  type="date"
                  value={filtros.fecha_hasta}
                  onChange={(e) => handleCambioFiltro('fecha_hasta', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">NIT Cliente</label>
                <Input
                  placeholder="Ej: 900123456"
                  value={filtros.nit_cliente}
                  onChange={(e) => handleCambioFiltro('nit_cliente', e.target.value)}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Código Producto</label>
                <Input
                  placeholder="Ej: FERT001"
                  value={filtros.codigo_producto}
                  onChange={(e) => handleCambioFiltro('codigo_producto', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tipo Inventario</label>
                <Input
                  placeholder="Ej: FERTILIZ"
                  value={filtros.tipo_inventario}
                  onChange={(e) => handleCambioFiltro('tipo_inventario', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Estado</label>
                <select
                  className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={filtros.estado}
                  onChange={(e) => handleCambioFiltro('estado', e.target.value)}
                >
                  <option value="">Todos</option>
                  <option value="VALIDA">VALIDA</option>
                  <option value="PROCESADA">PROCESADA</option>
                  <option value="PARCIAL">PARCIAL</option>
                </select>
              </div>
            </div>

            <div className="flex gap-2">
              <Button onClick={handleAplicarFiltros}>
                <Search className="mr-2 h-4 w-4" />
                Aplicar Filtros
              </Button>
              <Button variant="outline" onClick={handleLimpiarFiltros}>
                <X className="mr-2 h-4 w-4" />
                Limpiar Filtros
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Grilla de Transacciones */}
      <Card>
        <CardHeader>
          <CardTitle>Transacciones</CardTitle>
          <CardDescription>
            {transacciones?.total || 0} transacciones encontradas
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground text-center py-8">Cargando transacciones...</div>
          ) : transacciones?.items && transacciones.items.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium">Número</th>
                      <th className="text-left py-3 px-4 font-medium">Fecha</th>
                      <th className="text-left py-3 px-4 font-medium">Cliente</th>
                      <th className="text-left py-3 px-4 font-medium">Producto</th>
                      <th className="text-left py-3 px-4 font-medium">Tipo Inv.</th>
                      <th className="text-right py-3 px-4 font-medium">Cantidad</th>
                      <th className="text-right py-3 px-4 font-medium">Valor Total</th>
                      <th className="text-right py-3 px-4 font-medium">Valor Transado</th>
                      <th className="text-center py-3 px-4 font-medium">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transacciones.items.map((transaccion) => (
                      <tr key={transaccion.id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4 font-mono text-sm">{transaccion.numero_factura}</td>
                        <td className="py-3 px-4">
                          {new Date(transaccion.fecha_factura).toLocaleDateString('es-CO')}
                        </td>
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
                        <td className="py-3 px-4">
                          <span className="text-xs px-2 py-1 rounded bg-muted">
                            {transaccion.tipo_inventario || 'N/A'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div>
                            <p className="font-medium">{transaccion.cantidad_transada.toFixed(2)}</p>
                            <p className="text-xs text-muted-foreground">
                              de {transaccion.cantidad.toFixed(2)}
                            </p>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right">{formatCurrency(transaccion.valor_total)}</td>
                        <td className="py-3 px-4 text-right font-semibold text-green-600">
                          {formatCurrency(transaccion.valor_transado)}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              transaccion.estado === 'PROCESADA'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                : transaccion.estado === 'PARCIAL'
                                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                                : 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                            }`}
                          >
                            {transaccion.estado}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginación */}
              {totalPaginas > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    Página {paginaActual + 1} de {totalPaginas}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPaginaActual(prev => Math.max(0, prev - 1))}
                      disabled={paginaActual === 0}
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPaginaActual(prev => Math.min(totalPaginas - 1, prev + 1))}
                      disabled={paginaActual === totalPaginas - 1}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-muted-foreground text-center py-8">
              No se encontraron transacciones con los filtros aplicados
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
