import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Calendar,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  RefreshCw,
  FileText,
  CreditCard,
  XCircle
} from 'lucide-react'
import api, { exportApi } from '@/services/api'
import { useAuthStore } from '@/store/authStore'

interface ResultadoProcesamiento {
  exito: boolean
  mensaje: string
  fecha_desde: string
  fecha_hasta: string
  total_dias: number
  total_facturas_procesadas?: number
  total_notas_credito: number
  total_facturas_rechazadas: number
  total_aplicaciones: number
  archivo_generado: string
  dias_con_error?: Array<{ fecha: string; error: string }>
}

interface ResultadoExportacion {
  exito: boolean
  mensaje: string
  archivo: string
  total_registros: number
}

type TipoExportacion = 'facturas' | 'notas' | 'rechazadas' | 'aplicaciones'

export default function AdminProcesarRangoPage() {
  const user = useAuthStore((state) => state.user)
  const canProcess = user?.rol === 'admin' || user?.rol === 'editor'
  // Estado para procesar desde API
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState<ResultadoProcesamiento | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [inicioProceso, setInicioProceso] = useState<number | null>(null)
  const [estimadoSegundos, setEstimadoSegundos] = useState<number | null>(null)
  const [segundosTranscurridos, setSegundosTranscurridos] = useState(0)

  // Estado para exportar desde BD
  const [fechaExportDesde, setFechaExportDesde] = useState('')
  const [fechaExportHasta, setFechaExportHasta] = useState('')
  const [tipoExport, setTipoExport] = useState<TipoExportacion>('facturas')
  const [formatoExport, setFormatoExport] = useState<'excel' | 'pdf'>('excel')
  const [loadingExport, setLoadingExport] = useState(false)
  const [resultadoExport, setResultadoExport] = useState<ResultadoExportacion | null>(null)
  const [errorExport, setErrorExport] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<{ columnas: string[]; rows: Record<string, unknown>[] } | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)

  // Procesar rango desde API externa
  const handleProcesar = async () => {
    if (!canProcess) {
      setError('No tiene permisos para procesar información')
      return
    }
    try {
      setLoading(true)
      setError(null)
      setResultado(null)

      if (!fechaDesde || !fechaHasta) {
        setError('Debe seleccionar ambas fechas')
        return
      }

      const desde = new Date(fechaDesde)
      const hasta = new Date(fechaHasta)

      if (desde > hasta) {
        setError('La fecha desde debe ser anterior a la fecha hasta')
        return
      }

      const diffTime = Math.abs(hasta.getTime() - desde.getTime())
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays > 90) {
        setError('El rango máximo permitido es de 90 días')
        return
      }
      const estimado = Math.min(Math.max(diffDays * 95, 90), 3600)
      setEstimadoSegundos(estimado)
      setInicioProceso(Date.now())
      setSegundosTranscurridos(0)

      const response = await api.post('/api/admin/procesar-rango', {
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta,
      }, { timeout: 0 })
      setResultado(response.data)
    } catch (err) {
      console.error('Error al procesar rango:', err)
      const message = err instanceof Error ? err.message : 'Error al procesar el rango de fechas'
      setError(message)
    } finally {
      setLoading(false)
      setInicioProceso(null)
      setSegundosTranscurridos(0)
    }
  }

  useEffect(() => {
    if (!loading || !inicioProceso) return
    const timer = window.setInterval(() => {
      const seconds = Math.max(0, Math.floor((Date.now() - inicioProceso) / 1000))
      setSegundosTranscurridos(seconds)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [loading, inicioProceso])

  // Exportar datos desde BD
  const handleExportar = async () => {
    if (!canProcess) {
      setErrorExport('No tiene permisos para exportar información')
      return
    }
    try {
      setLoadingExport(true)
      setErrorExport(null)
      setResultadoExport(null)

      if (!fechaExportDesde || !fechaExportHasta) {
        setErrorExport('Debe seleccionar ambas fechas')
        return
      }

      const endpoint = formatoExport === 'pdf' ? '/api/admin/exportar-pdf' : '/api/admin/exportar-excel'
      const response = await api.post(endpoint, {
        fecha_desde: fechaExportDesde,
        fecha_hasta: fechaExportHasta,
        tipo: tipoExport
      })

      setResultadoExport(response.data)
    } catch (err) {
      console.error('Error al exportar:', err)
      const message = err instanceof Error ? err.message : 'Error al exportar datos'
      setErrorExport(message)
    } finally {
      setLoadingExport(false)
    }
  }

  const handlePreview = async () => {
    if (!canProcess) {
      setErrorExport('No tiene permisos para consultar previsualización')
      return
    }
    setLoadingPreview(true)
    try {
      const data = await exportApi.preview({
        fecha_desde: fechaExportDesde,
        fecha_hasta: fechaExportHasta,
        tipo: tipoExport,
        limite: 20
      })
      setPreviewData({ columnas: data.columnas, rows: data.rows })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al generar preview'
      setErrorExport(message)
    } finally {
      setLoadingPreview(false)
    }
  }

  // Descargar archivo
  const handleDescargar = async (filename: string) => {
    try {
      const response = await api.get(`/api/admin/descargar/${filename}`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Error al descargar archivo:', err)
      const message = err instanceof Error ? err.message : 'Error al descargar el archivo'
      setError(message)
    }
  }

  const tiposExportacion = [
    { value: 'facturas', label: 'Facturas', icon: FileText, desc: 'Líneas de facturas válidas' },
    { value: 'notas', label: 'Notas Crédito', icon: CreditCard, desc: 'Notas de crédito registradas' },
    { value: 'rechazadas', label: 'Rechazadas', icon: XCircle, desc: 'Facturas rechazadas' },
    { value: 'aplicaciones', label: 'Aplicaciones', icon: RefreshCw, desc: 'Historial de aplicaciones' },
  ]

  const formatDuracion = (seconds: number) => {
    const s = Math.max(0, Math.floor(seconds))
    const min = Math.floor(s / 60)
    const seg = s % 60
    return `${min}m ${seg}s`
  }

  const segundosRestantes = estimadoSegundos ? Math.max(estimadoSegundos - segundosTranscurridos, 0) : null

  return (
    <div className="mx-auto max-w-7xl space-y-6 py-2">
      {!canProcess && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Su perfil es de consulta. Puede visualizar información, pero no procesar ni exportar archivos.
          </AlertDescription>
        </Alert>
      )}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Procesamiento de Facturas</h1>
        <p className="mt-1 text-muted-foreground text-sm">
          Procesa facturas por rango y guarda automaticamente los resultados en base de datos
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SECCIÓN: Exportar desde BD */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
              <FileSpreadsheet className="h-4 w-4 text-primary" />
              Exportar Excel o PDF desde BD
            </CardTitle>
            <CardDescription>
              Genera un archivo con datos de la base de datos por rango de fechas
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="export-desde">Fecha Desde</Label>
                <Input
                  id="export-desde"
                  type="date"
                  value={fechaExportDesde}
                  onChange={(e) => setFechaExportDesde(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="export-hasta">Fecha Hasta</Label>
                <Input
                  id="export-hasta"
                  type="date"
                  value={fechaExportHasta}
                  onChange={(e) => setFechaExportHasta(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Tipo de datos a exportar</Label>
              <div className="grid grid-cols-2 gap-2">
                {tiposExportacion.map((tipo) => (
                  <button
                    key={tipo.value}
                    onClick={() => setTipoExport(tipo.value as TipoExportacion)}
                    className={`flex items-center gap-2 rounded-lg border p-3 text-left transition-colors ${
                      tipoExport === tipo.value
                        ? 'border-primary/30 bg-primary/5 text-foreground'
                        : 'border-border hover:bg-accent'
                    }`}
                  >
                    <tipo.icon className="h-4 w-4" />
                      <div className="text-left">
                      <div className="text-sm font-medium">{tipo.label}</div>
                      <div className="text-xs text-muted-foreground">{tipo.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Formato</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={formatoExport === 'excel' ? 'default' : 'outline'}
                  onClick={() => setFormatoExport('excel')}
                >
                  Excel
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={formatoExport === 'pdf' ? 'default' : 'outline'}
                  onClick={() => setFormatoExport('pdf')}
                >
                  PDF
                </Button>
              </div>
            </div>

            {errorExport && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errorExport}</AlertDescription>
              </Alert>
            )}

            {resultadoExport && (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{resultadoExport.mensaje}</p>
                      <p className="text-sm text-muted-foreground">
                        Archivo: {resultadoExport.archivo}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleDescargar(resultadoExport.archivo)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Descargar
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {previewData && (
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="min-w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      {previewData.columnas.map((col) => (
                        <th key={col} className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.map((row, idx) => (
                      <tr key={idx} className="border-t border-border">
                        {previewData.columnas.map((col) => (
                          <td key={col} className="px-3 py-2 text-foreground">{String(row[col] ?? '')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={handlePreview}
              disabled={!canProcess || loadingPreview || !fechaExportDesde || !fechaExportHasta}
                variant="outline"
                className="w-full"
              >
                {loadingPreview ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generando preview...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Previsualizar
                  </>
                )}
              </Button>
              <Button
                onClick={handleExportar}
              disabled={!canProcess || loadingExport || !fechaExportDesde || !fechaExportHasta}
                className="w-full"
              >
                {loadingExport ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Exportando...
                  </>
                ) : (
                  <>
                    <FileSpreadsheet className="mr-2 h-4 w-4" />
                    Exportar
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* SECCIÓN: Procesar desde API */}
        <Card className="border border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
              <Calendar className="h-4 w-4 text-primary" />
              Procesar Rango de Fechas
            </CardTitle>
            <CardDescription>
              Procesa facturas desde la API externa y guarda en la base de datos.
              Maximo 90 dias.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fecha-desde">Fecha Desde</Label>
                <Input
                  id="fecha-desde"
                  type="date"
                  value={fechaDesde}
                  onChange={(e) => setFechaDesde(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fecha-hasta">Fecha Hasta</Label>
                <Input
                  id="fecha-hasta"
                  type="date"
                  value={fechaHasta}
                  onChange={(e) => setFechaHasta(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                />
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {loading && (
              <Alert>
                <Loader2 className="h-4 w-4 animate-spin" />
                <AlertDescription>
                  <div className="space-y-1">
                    <div>Proceso en ejecución.</div>
                    <div className="text-xs">
                      Tiempo transcurrido: {formatDuracion(segundosTranscurridos)}
                      {segundosRestantes !== null ? ` · Estimado restante: ${formatDuracion(segundosRestantes)}` : ''}
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {resultado && (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-semibold">{resultado.mensaje}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm mt-2">
                      <div>Total de días procesados:</div>
                      <div className="font-medium">{resultado.total_dias}</div>
                      <div>Facturas procesadas:</div>
                      <div className="font-medium">{resultado.total_facturas_procesadas || 0}</div>
                      <div>Notas de crédito:</div>
                      <div className="font-medium">{resultado.total_notas_credito}</div>
                      <div>Facturas rechazadas:</div>
                      <div className="font-medium">{resultado.total_facturas_rechazadas}</div>
                      <div>Aplicaciones realizadas:</div>
                      <div className="font-medium">{resultado.total_aplicaciones}</div>
                      <div>Días con error:</div>
                      <div className="font-medium">{resultado.dias_con_error?.length || 0}</div>
                    </div>
                    {resultado.archivo_generado && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2"
                        onClick={() => handleDescargar(resultado.archivo_generado)}
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Descargar Archivo
                      </Button>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            <Button
              onClick={handleProcesar}
              disabled={!canProcess || loading || !fechaDesde || !fechaHasta}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Procesando...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Procesar Rango
                </>
              )}
            </Button>

            <p className="text-xs text-muted-foreground">
              Este proceso puede tomar varios minutos. Los datos se guardan en la BD
              y se pueden exportar despues.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Información adicional */}
      <Card className="border border-border">
        <CardHeader>
          <CardTitle className="text-base font-semibold text-foreground">Informacion</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            <strong>Exportar Excel:</strong> Genera un archivo Excel con los datos
            ya almacenados en la base de datos. Es rápido porque no consulta la API externa.
          </p>
          <p>
            <strong>Procesar Rango:</strong> Consulta la API externa para obtener
            facturas y notas crédito, aplica las reglas de negocio y guarda todo en la BD.
            Este proceso es más lento pero actualiza la información.
          </p>
          <p>
            <strong>Regla de aplicación de notas:</strong> Una nota solo se aplica si
            cumple con la verificación de agente. Las notas marcadas como agente se aplican
            a su factura correspondiente. El monto mínimo registrable por factura es $524.000
            y el código abc123 permite hasta 5 repeticiones si la suma total supera $524.000.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
