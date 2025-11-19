import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Calendar, Download, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import api from '@/services/api'

interface ResultadoProcesamiento {
  exito: boolean
  mensaje: string
  fecha_desde: string
  fecha_hasta: string
  total_dias: number
  total_notas_credito: number
  total_facturas_rechazadas: number
  total_aplicaciones: number
  archivo_generado: string
}

export default function AdminProcesarRangoPage() {
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState<ResultadoProcesamiento | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleProcesar = async () => {
    try {
      setLoading(true)
      setError(null)
      setResultado(null)

      // Validar fechas
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

      // Calcular días
      const diffTime = Math.abs(hasta.getTime() - desde.getTime())
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays > 90) {
        setError('El rango máximo permitido es de 90 días')
        return
      }

      // Llamar al endpoint
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

  const handleDescargar = async () => {
    try {
      if (!resultado?.archivo_generado) return

      // Extraer el nombre del archivo de la ruta
      const filename = resultado.archivo_generado.split('/').pop() || ''

      // Descargar el archivo
      const response = await api.get(`/api/admin/descargar-archivo/${filename}`, {
        responseType: 'blob',
      })

      // Crear un enlace de descarga
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

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Procesar Rango de Fechas</h1>
        <p className="text-muted-foreground mt-2">
          Genera un reporte consolidado de facturas para un rango de fechas específico
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Seleccionar Rango de Fechas
          </CardTitle>
          <CardDescription>
            Procesa las facturas de un rango de fechas y genera un Excel consolidado.
            Máximo 90 días.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                    <div>Notas de crédito:</div>
                    <div className="font-medium">{resultado.total_notas_credito}</div>
                    <div>Facturas rechazadas:</div>
                    <div className="font-medium">{resultado.total_facturas_rechazadas}</div>
                    <div>Aplicaciones realizadas:</div>
                    <div className="font-medium">{resultado.total_aplicaciones}</div>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-3">
            <Button
              onClick={handleProcesar}
              disabled={loading || !fechaDesde || !fechaHasta}
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Procesando...
                </>
              ) : (
                <>
                  <Calendar className="mr-2 h-4 w-4" />
                  Procesar Rango
                </>
              )}
            </Button>

            {resultado && (
              <Button onClick={handleDescargar} variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Descargar Excel
              </Button>
            )}
          </div>

          <div className="text-sm text-muted-foreground space-y-1">
            <p>
              Este proceso puede tomar varios minutos dependiendo del rango de fechas
              seleccionado.
            </p>
            <p>El archivo generado estará disponible para descarga una vez completado el procesamiento.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
