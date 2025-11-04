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
} from '@/types'

// ============================================================================
// CONFIGURACIÓN: URL de la API en puerto 2500
// ============================================================================
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:2500'

console.log('🔧 API Configuration:', {
  url: API_URL,
  env: import.meta.env.MODE
})

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// ============================================================================
// INTERCEPTOR DE REQUEST - Agregar token
// ============================================================================
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('🔑 Token agregado a request:', {
        url: config.url,
        method: config.method,
        tokenPreview: token.substring(0, 20) + '...'
      })
    } else {
      console.warn('⚠️  No hay token disponible para:', config.url)
    }
    
    return config
  },
  (error) => {
    console.error('❌ Error en request interceptor:', error)
    return Promise.reject(error)
  }
)

// ============================================================================
// INTERCEPTOR DE RESPONSE - Manejo de errores y refresh
// ============================================================================
let isRefreshing = false
let failedQueue: any[] = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  
  failedQueue = []
}

api.interceptors.response.use(
  (response) => {
    console.log('✅ Response exitoso:', {
      url: response.config.url,
      status: response.status
    })
    return response
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest: any = error.config

    console.error('❌ Error en response:', {
      url: originalRequest?.url,
      status: error.response?.status,
      message: error.message,
      code: error.code
    })

    // ========================================================================
    // Manejo de errores de red
    // ========================================================================
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
      console.error('🔌 Error de conexión con el servidor')
      return Promise.reject({
        ...error,
        message: 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo en ' + API_URL
      })
    }

    // ========================================================================
    // Manejo de error 401 (no autorizado)
    // ========================================================================
    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        console.warn('🔒 No hay refresh token, redirigiendo a login')
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (originalRequest.url?.includes('/auth/refresh')) {
        console.error('❌ Refresh token inválido o expirado')
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (originalRequest.url?.includes('/auth/login')) {
        console.error('❌ Credenciales inválidas')
        return Promise.reject(error)
      }

      // ======================================================================
      // Sistema de cola para refresh token
      // ======================================================================
      if (isRefreshing) {
        console.log('⏳ Esperando refresh en progreso...')
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      console.log('🔄 Intentando refrescar token...')

      return new Promise((resolve, reject) => {
        axios.post(`${API_URL}/api/auth/refresh`, {}, {
          headers: {
            'Authorization': `Bearer ${refreshToken}`,
          },
        })
        .then(response => {
          const { access_token } = response.data
          
          console.log('✅ Token refrescado exitosamente')
          
          localStorage.setItem('access_token', access_token)
          originalRequest.headers['Authorization'] = 'Bearer ' + access_token
          
          processQueue(null, access_token)
          resolve(api(originalRequest))
        })
        .catch(err => {
          console.error('❌ Error al refrescar token:', err)
          processQueue(err, null)
          localStorage.clear()
          window.location.href = '/login'
          reject(err)
        })
        .finally(() => {
          isRefreshing = false
        })
      })
    }

    return Promise.reject(error)
  }
)

// ============================================================================
// AUTH API
// ============================================================================
export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    console.log('🔐 Intentando login con:', credentials.username)
    
    try {
      const { data } = await api.post<LoginResponse>('/api/auth/login', credentials)
      
      console.log('✅ Login exitoso:', {
        username: data.user.username,
        rol: data.user.rol
      })
      
      return data
    } catch (error: any) {
      console.error('❌ Login fallido:', error.response?.data || error.message)
      throw error
    }
  },

  logout: async (): Promise<void> => {
    console.log('👋 Cerrando sesión...')
    
    try {
      await api.post('/api/auth/logout')
      console.log('✅ Logout exitoso')
    } catch (error) {
      console.error('⚠️  Error en logout:', error)
    }
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

// ============================================================================
// NOTAS API
// ============================================================================
export const notasApi = {
  getNotas: async (params?: {
    estado?: string
    nit_cliente?: string
    fecha_desde?: string
    fecha_hasta?: string
    limite?: number
    offset?: number
  }): Promise<PaginatedResponse<NotaCredito>> => {
    console.log('📄 Obteniendo notas con params:', params)
    
    try {
      const { data } = await api.get<PaginatedResponse<NotaCredito>>('/api/notas', { params })
      
      console.log('✅ Notas obtenidas:', {
        total: data.total,
        items: data.items.length
      })
      
      return data
    } catch (error) {
      console.error('❌ Error obteniendo notas:', error)
      throw error
    }
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

// ============================================================================
// APLICACIONES API
// ============================================================================
export const aplicacionesApi = {
  getAplicaciones: async (numeroNota: string): Promise<Aplicacion[]> => {
    const { data } = await api.get<Aplicacion[]>(`/api/aplicaciones/${numeroNota}`)
    return data
  },
}

// ============================================================================
// HEALTH API
// ============================================================================
export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const { data } = await api.get<{ status: string }>('/api/health')
    return data
  },
}

export default api