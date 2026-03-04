import { create } from 'zustand'
import type { User, LoginRequest } from '@/types'
import { authApi, onAuthSessionExpired } from '@/services/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  requires2fa: boolean
  sessionTransitioning: boolean
  sessionMessage: string | null
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  handleSessionExpired: (reason?: string) => Promise<void>
  setUser: (user: User | null) => void
  initialize: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  requires2fa: false,
  sessionTransitioning: false,
  sessionMessage: null,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null, sessionTransitioning: true, sessionMessage: 'Validando credenciales...' })
    try {
      const response = await authApi.login(credentials)
      if (response.requires_2fa || !response.access_token) {
        set({ requires2fa: true, isLoading: false, error: 'OTP requerido', sessionTransitioning: false, sessionMessage: null })
        return
      }
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      set({ user: response.user, isAuthenticated: true, isLoading: false, requires2fa: false, sessionTransitioning: false, sessionMessage: null })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Error al iniciar sesión'
      set({
        error: message,
        isLoading: false,
        sessionTransitioning: false,
        sessionMessage: null
      })
      throw error
    }
  },

  logout: async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    } finally {
      if ('caches' in window) {
        try {
          const keys = await caches.keys()
          await Promise.all(keys.map((k) => caches.delete(k)))
        } catch (err) {
          console.error('Error al limpiar caché:', err)
        }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      localStorage.setItem('logout_success', 'true')
      set({ user: null, isAuthenticated: false, requires2fa: false, sessionTransitioning: false, sessionMessage: null })
    }
  },

  handleSessionExpired: async (reason?: string) => {
    set({ sessionTransitioning: true, sessionMessage: reason || 'La sesión expiró, cerrando de forma segura...' })
    try {
      await authApi.logout()
    } catch {
      // Ignorar: token ya expiró
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      localStorage.setItem('logout_success', 'true')
      set({
        user: null,
        isAuthenticated: false,
        requires2fa: false,
        error: 'Sesión finalizada por expiración del token',
        sessionTransitioning: false,
        sessionMessage: null
      })
      window.location.href = '/login'
    }
  },

  setUser: (user: User | null) => {
    set({ user, isAuthenticated: !!user })
  },

  initialize: () => {
    const token = localStorage.getItem('access_token')
    const userStr = localStorage.getItem('user')

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as User
        set({ user, isAuthenticated: true })
      } catch (error) {
        console.error('Error al parsear usuario:', error)
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }
    }
  },
}))

onAuthSessionExpired((message) => {
  const state = useAuthStore.getState()
  state.handleSessionExpired(message)
})
