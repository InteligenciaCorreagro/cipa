import axios, { AxiosError } from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  NotaCredito,
  Aplicacion,
  Estadisticas,
  NotasPorEstado,
  PaginatedResponse,
  ApiError,
  Factura,
  EstadisticasFacturas,
  Transaccion,
  NotaPendiente,
  AplicacionSistema,
  LogEntry,
} from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:2500'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

let onSessionExpiredCallback: ((message?: string) => void) | null = null
export const onAuthSessionExpired = (callback: (message?: string) => void) => {
  onSessionExpiredCallback = callback
}

// Interceptor para agregar el token a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config

    // Solo intentar refresh si es un error 401 Y tenemos tokens
    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = localStorage.getItem('refresh_token')

      // Si no hay refresh token, no intentar refresh
      if (!refreshToken) {
        onSessionExpiredCallback?.(error.response?.data?.message || 'Token expirado')
        return Promise.reject(error)
      }

      // Evitar loops infinitos - no reintentar el endpoint de refresh
      if (originalRequest.url?.includes('/auth/refresh')) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        onSessionExpiredCallback?.('Token expirado')
        return Promise.reject(error)
      }

      // Intentar refrescar el token
      try {
        const response = await axios.post(`${API_URL}/api/auth/refresh`, {}, {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        })

        const { access_token } = response.data
        localStorage.setItem('access_token', access_token)

        // Reintentar la petición original
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        // Si falla el refresh, limpiar tokens y redirigir al login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        onSessionExpiredCallback?.('Token expirado')
        return Promise.reject(refreshError)
      }
    }

    // Para errores de red (ERR_NETWORK), no redirigir
    if (error.code === 'ERR_NETWORK') {
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const { data } = await api.post<LoginResponse>('/api/auth/login', credentials)
    return data
  },

  logout: async (): Promise<void> => {
    await api.post('/api/auth/logout')
  },

  setup2fa: async (): Promise<{ secret: string; otpauth_uri: string }> => {
    const { data } = await api.post<{ secret: string; otpauth_uri: string }>('/api/auth/2fa/setup')
    return data
  },

  enable2fa: async (otp: string): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/auth/2fa/enable', { otp })
    return data
  },

  disable2fa: async (): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/auth/2fa/disable')
    return data
  },

  status2fa: async (): Promise<{ configurado: boolean; habilitado: boolean }> => {
    const { data } = await api.get<{ configurado: boolean; habilitado: boolean }>('/api/auth/2fa/status')
    return data
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },

  refresh: async (): Promise<{ access_token: string }> => {
    const { data } = await api.post<{ access_token: string }>('/api/auth/refresh')
    return data
  },
}

// Notas API
export const notasApi = {
  getNotas: async (params?: {
    estado?: string
    nit_cliente?: string
    fecha_desde?: string
    fecha_hasta?: string
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<NotaCredito>> => {
    const { data } = await api.get<PaginatedResponse<NotaCredito>>('/api/notas', { params })
    return data
  },

  getNota: async (id: number): Promise<NotaCredito> => {
    const { data } = await api.get<NotaCredito>(`/api/notas/${id}`)
    return data
  },
  createNota: async (payload: Partial<NotaCredito>): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/notas', payload)
    return data
  },
  updateNota: async (id: number, payload: Partial<NotaCredito>): Promise<{ mensaje: string }> => {
    const { data } = await api.put<{ mensaje: string }>(`/api/notas/${id}`, payload)
    return data
  },
  deleteNota: async (id: number): Promise<{ mensaje: string }> => {
    const { data } = await api.delete<{ mensaje: string }>(`/api/notas/${id}`)
    return data
  },
  aplicarNota: async (payload: { nota_id: number; numero_factura: string; codigo_producto: string; indice_linea?: number }): Promise<Aplicacion> => {
    const { data } = await api.post<Aplicacion>('/api/notas/aplicar', payload)
    return data
  },
  getNoAplicadas: async (params?: { limite?: number; offset?: number }): Promise<PaginatedResponse<{ id: number; numero_nota: string; numero_factura: string; motivo: string; detalle?: string; fecha_registro: string }>> => {
    const { data } = await api.get<PaginatedResponse<{ id: number; numero_nota: string; numero_factura: string; motivo: string; detalle?: string; fecha_registro: string }>>('/api/notas/no-aplicadas', { params })
    return data
  },
  registrarNoAplicada: async (payload: { nota_id: number; numero_factura?: string; motivo: string; detalle?: string }): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/notas/no-aplicadas', payload)
    return data
  },

  getNotasPorEstado: async (): Promise<NotasPorEstado[]> => {
    const { data } = await api.get<NotasPorEstado[]>('/api/notas/por-estado')
    return data
  },

  getEstadisticas: async (): Promise<Estadisticas> => {
    const { data } = await api.get<Estadisticas>('/api/notas/estadisticas')
    return data
  },
}

// Aplicaciones API
export const aplicacionesApi = {
  getAplicaciones: async (numeroNota: string): Promise<Aplicacion[]> => {
    const { data } = await api.get<Aplicacion[]>(`/api/aplicaciones/${numeroNota}`)
    return data
  },
}

export const notasPendientesApi = {
  getNotas: async (params?: {
    estado?: string
    prioridad?: string
    responsable?: string
    fecha_desde?: string
    fecha_hasta?: string
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<NotaPendiente>> => {
    const { data } = await api.get<PaginatedResponse<NotaPendiente>>('/api/notas/pendientes', { params })
    return data
  },
  createNota: async (payload: Partial<NotaPendiente>): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/notas/pendientes', payload)
    return data
  },
  updateNota: async (id: number, payload: Partial<NotaPendiente>): Promise<{ mensaje: string }> => {
    const { data } = await api.put<{ mensaje: string }>(`/api/notas/pendientes/${id}`, payload)
    return data
  },
  deleteNota: async (id: number): Promise<{ mensaje: string }> => {
    const { data } = await api.delete<{ mensaje: string }>(`/api/notas/pendientes/${id}`)
    return data
  },
  getAlertas: async (): Promise<{ vencidas: NotaPendiente[]; proximas: NotaPendiente[] }> => {
    const { data } = await api.get<{ vencidas: NotaPendiente[]; proximas: NotaPendiente[] }>('/api/notas/pendientes/alertas')
    return data
  },
}

export const aplicacionesSistemaApi = {
  getAplicaciones: async (params?: {
    estado?: string
    search?: string
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<AplicacionSistema>> => {
    const { data } = await api.get<PaginatedResponse<AplicacionSistema>>('/api/aplicaciones-sistema', { params })
    return data
  },
  createAplicacion: async (payload: Partial<AplicacionSistema>): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/aplicaciones-sistema', payload)
    return data
  },
  updateAplicacion: async (id: number, payload: Partial<AplicacionSistema>): Promise<{ mensaje: string }> => {
    const { data } = await api.put<{ mensaje: string }>(`/api/aplicaciones-sistema/${id}`, payload)
    return data
  },
  deleteAplicacion: async (id: number): Promise<{ mensaje: string }> => {
    const { data } = await api.delete<{ mensaje: string }>(`/api/aplicaciones-sistema/${id}`)
    return data
  },
  registrarUso: async (id: number): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>(`/api/aplicaciones-sistema/${id}/uso`)
    return data
  },
}

export const logsApi = {
  getLogs: async (params?: {
    entidad?: string
    accion?: string
    usuario?: string
    fecha_desde?: string
    fecha_hasta?: string
    search?: string
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<LogEntry>> => {
    const { data } = await api.get<PaginatedResponse<LogEntry>>('/api/admin/logs', { params })
    return data
  },
}

export const exportApi = {
  preview: async (payload: { fecha_desde: string; fecha_hasta: string; tipo: string; limite?: number }): Promise<{ columnas: string[]; rows: Record<string, unknown>[]; limite: number }> => {
    const { data } = await api.post<{ columnas: string[]; rows: Record<string, unknown>[]; limite: number }>('/api/admin/export-preview', payload)
    return data
  },
}

// Facturas API
export const facturasApi = {
  getFacturas: async (params?: {
    estado?: string
    nit_cliente?: string
    fecha_desde?: string
    fecha_hasta?: string
    codigo_factura?: string
    numero_factura?: string
    nombre_cliente?: string
    registrable?: boolean
    con_nota?: boolean
    search?: string
    orden?: string
    direccion?: string
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<Factura>> => {
    const { data } = await api.get<PaginatedResponse<Factura>>('/api/facturas', { params })
    return data
  },

  getFactura: async (id: number): Promise<Factura> => {
    const { data } = await api.get<Factura>(`/api/facturas/${id}`)
    return data
  },
  createFactura: async (payload: Partial<Factura>): Promise<{ mensaje: string }> => {
    const { data } = await api.post<{ mensaje: string }>('/api/facturas', payload)
    return data
  },
  updateFactura: async (id: number, payload: Partial<Factura>): Promise<{ mensaje: string }> => {
    const { data } = await api.put<{ mensaje: string }>(`/api/facturas/${id}`, payload)
    return data
  },
  deleteFactura: async (id: number): Promise<{ mensaje: string }> => {
    const { data } = await api.delete<{ mensaje: string }>(`/api/facturas/${id}`)
    return data
  },

  getEstadisticas: async (): Promise<EstadisticasFacturas> => {
    const { data } = await api.get<EstadisticasFacturas>('/api/facturas/estadisticas')
    return data
  },

  getTransacciones: async (params?: {
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<Transaccion>> => {
    const { data } = await api.get<PaginatedResponse<Transaccion>>('/api/facturas/transacciones', { params })
    return data
  },
}

// Health API
export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const { data } = await api.get<{ status: string }>('/api/health')
    return data
  },
}

// Exportar api tanto como default como named export para compatibilidad
export { api }
export default api
