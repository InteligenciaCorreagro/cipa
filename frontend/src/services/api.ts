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
} from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:2500'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
        return Promise.reject(error)
      }

      // Evitar loops infinitos - no reintentar el endpoint de refresh
      if (originalRequest.url?.includes('/auth/refresh')) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
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
        window.location.href = '/login'
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

// Facturas API
export const facturasApi = {
  getFacturas: async (params?: {
    estado?: string
    nit_cliente?: string
    fecha_desde?: string
    fecha_hasta?: string
    es_valida?: boolean
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

export default api
