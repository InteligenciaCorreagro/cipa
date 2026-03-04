"use client"

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Leaf, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [otp, setOtp] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({})
  
  const { login, isLoading, error, requires2fa } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (localStorage.getItem('logout_success')) {
      localStorage.removeItem('logout_success')
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFieldErrors({})

    // Validación de campos
    const errors: { username?: string; password?: string } = {}

    if (!username.trim()) {
      errors.username = "El usuario es requerido"
    } else if (username.length < 3) {
      errors.username = "El usuario debe tener al menos 3 caracteres"
    }

    if (!password) {
      errors.password = "La contraseña es requerida"
    } else if (password.length < 6) {
      errors.password = "La contraseña debe tener al menos 6 caracteres"
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }

    // Login real usando zustand store
    try {
      await login({ username, password, otp: otp || undefined })
      navigate('/')
    } catch (err) {
      console.error('Error al iniciar sesión:', err)
      // El error ya está manejado por el store y se muestra abajo
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 via-white to-white p-4">
      <div className="w-full max-w-md">
        {/* Logo y título */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-600/30 mb-6">
            <Leaf className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-emerald-900">CIPA</h1>
          <p className="text-emerald-700 mt-2 text-sm">Sistema de Gestión de Notas de Crédito</p>
        </div>

        {/* Formulario */}
        <div className="bg-white rounded-2xl shadow-xl border border-emerald-100 p-8">
          {localStorage.getItem('logout_success') && (
            <div className="mb-4 text-sm text-emerald-700 bg-emerald-50 px-4 py-3 rounded-lg border border-emerald-200 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              Sesión cerrada correctamente
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-emerald-800 text-sm font-medium">
                Usuario
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="Ingrese su usuario"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value)
                  if (fieldErrors.username) setFieldErrors((prev) => ({ ...prev, username: undefined }))
                }}
                autoComplete="username"
                className={`h-12 border-emerald-200 bg-emerald-50/40 focus:bg-white focus:border-emerald-600 focus:ring-emerald-500/20 transition-all placeholder:text-emerald-300 ${
                  fieldErrors.username ? "border-emerald-600 focus:border-emerald-700 focus:ring-emerald-600/20" : ""
                }`}
              />
              {fieldErrors.username && (
                <div className="flex items-center gap-1 text-sm text-emerald-700 mt-1">
                  <AlertCircle className="w-4 h-4 text-emerald-600" />
                  {fieldErrors.username}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-emerald-800 text-sm font-medium">
                Contraseña
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Ingrese su contraseña"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }))
                  }}
                  autoComplete="current-password"
                  className={`h-12 pr-12 border-emerald-200 bg-emerald-50/40 focus:bg-white focus:border-emerald-600 focus:ring-emerald-500/20 transition-all placeholder:text-emerald-300 ${
                    fieldErrors.password ? "border-emerald-600 focus:border-emerald-700 focus:ring-emerald-600/20" : ""
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400 hover:text-emerald-600 transition-colors"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {fieldErrors.password && (
                <div className="flex items-center gap-1 text-sm text-emerald-700 mt-1">
                  <AlertCircle className="w-4 h-4 text-emerald-600" />
                  {fieldErrors.password}
                </div>
              )}
            </div>

            {requires2fa && (
              <div className="space-y-2">
                <Label htmlFor="otp" className="text-emerald-800 text-sm font-medium">
                  Código OTP
                </Label>
                <Input
                  id="otp"
                  type="text"
                  placeholder="Ingrese el código de 6 dígitos"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  autoComplete="one-time-code"
                  className="h-12 border-emerald-200 bg-emerald-50/40 focus:bg-white focus:border-emerald-600 focus:ring-emerald-500/20 transition-all placeholder:text-emerald-300"
                />
              </div>
            )}

            {error && (
              <div className="text-sm text-emerald-700 bg-emerald-50 px-4 py-3 rounded-lg border border-emerald-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-emerald-600" />
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-12 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white font-medium transition-all shadow-lg shadow-emerald-600/30 hover:shadow-xl hover:shadow-emerald-600/40"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="animate-spin h-4 w-4" />
                  Iniciando sesión...
                </span>
              ) : (
                "Iniciar Sesión"
              )}
            </Button>
          </form>

          {/* Footer */}
          <p className="text-center text-xs text-emerald-400 mt-6">
            © 2025 CIPA. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </div>
  )
}
