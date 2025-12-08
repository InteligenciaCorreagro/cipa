import { useState } from 'react'
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
import api from '@/services/api'

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
}

interface ResultadoExportacion {
  exito: boolean
  mensaje: string
  archivo: string
  total_registros: number
}

type TipoExportacion = 'facturas' | 'notas' | 'rechazadas' | 'aplicaciones'

export default function AdminProcesarRangoPage() {
  // Estado para procesar desde API
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState<ResultadoProcesamiento | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Estado para exportar desde BD
  const [fechaExportDesde, setFechaExportDesde] = useState('')
  const [fechaExportHasta, setFechaExportHasta] = useState('')
  const [tipoExport, setTipoExport] = useState<TipoExportacion>('facturas')
  const [loadingExport, setLoadingExport] = useState(false)
  const [resultadoExport, setResultadoExport] = useState<ResultadoExportacion | null>(null)
  const [errorExport, setErrorExport] = useState<string | null>(null)

  // Procesar rango desde API externa
  const handleProcesar = async () => {
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

      const response = await api.post('/api/admin/procesar-rango', {
        fecha_desde: fechaDesde,
        fecha_hasta: fechaHasta,
      })

      setResultado(response.data)
    } catch (err: any) {
      console.error('Error al procesar rango:', err)
      setError(err.response?.data?.error || 'Error al procesar el rango de fechas')
    } finally {
      setLoading(false)
    }
  }

  // Exportar datos desde BD
  const handleExportar = async () => {
    try {
      setLoadingExport(true)
      setErrorExport(null)
      setResultadoExport(null)

      if (!fechaExportDesde || !fechaExportHasta) {
        setErrorExport('Debe seleccionar ambas fechas')
        return
      }

      const response = await api.post('/api/admin/exportar-excel', {
        fecha_desde: fechaExportDesde,
        fecha_hasta: fechaExportHasta,
        tipo: tipoExport
      })

      setResultadoExport(response.data)
    } catch (err: any) {
      console.error('Error al exportar:', err)
      setErrorExport(err.response?.data?.error || 'Error al exportar datos')
    } finally {
      setLoadingExport(false)
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
    } catch (err: any) {
      console.error('Error al descargar archivo:', err)
      setError(err.response?.data?.error || 'Error al descargar el archivo')
    }
  }

  const tiposExportacion = [
    { value: 'facturas', label: 'Facturas', icon: FileText, desc: 'Líneas de facturas válidas' },
    { value: 'notas', label: 'Notas Crédito', icon: CreditCard, desc: 'Notas de crédito registradas' },
    { value: 'rechazadas', label: 'Rechazadas', icon: XCircle, desc: 'Facturas rechazadas' },
    { value: 'aplicaciones', label: 'Aplicaciones', icon: RefreshCw, desc: 'Historial de aplicaciones' },
  ]

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Panel de Administración</h1>
        <p className="text-muted-foreground mt-2">
          Procesar datos desde la API o exportar información de la base de datos
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SECCIÓN: Exportar desde BD */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              Exportar Excel desde BD
            </CardTitle>
            <CardDescription>
              Genera un Excel con datos de la base de datos por rango de fechas
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
                    className={`flex items-center gap-2 p-3 rounded-lg border transition-colors ${
                      tipoExport === tipo.value
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border hover:bg-muted'
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

            <Button
              onClick={handleExportar}
              disabled={loadingExport || !fechaExportDesde || !fechaExportHasta}
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
                  Exportar Excel
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* SECCIÓN: Procesar desde API */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Procesar Rango de Fechas
            </CardTitle>
            <CardDescription>
              Procesa facturas desde la API externa y guarda en la base de datos.
              Máximo 90 días.
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
                    </div>
                    {resultado.archivo_generado && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2"
                        onClick={() => handleDescargar(resultado.archivo_generado)}
                      >
                        <Download className="h-4 w-4 mr-1" />
                        Descargar Excel
                      </Button>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            <Button
              onClick={handleProcesar}
              disabled={loading || !fechaDesde || !fechaHasta}
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
              y se pueden exportar después.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Información adicional */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Información</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
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
            la cantidad Y el valor de la nota son menores o iguales a los de la factura.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
