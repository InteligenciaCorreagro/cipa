"use client"

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react'

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

    try {
      await login({ username, password, otp: otp || undefined })
      navigate('/')
    } catch (err) {
      console.error('Error al iniciar sesion:', err)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-10">
          <img
            src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jwwFqToCBnvzQxjVAgBLw7p8FyUsD3.png"
            alt="Correagro Logo"
            className="h-10 w-auto mx-auto mb-4"
          />
          <div className="h-px w-12 bg-primary mx-auto mb-4" />
          <p className="text-muted-foreground text-sm tracking-wide">
            Sistema de Gestion de Notas de Credito
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-card rounded-2xl border border-border p-8 shadow-sm">
          {localStorage.getItem('logout_success') && (
            <div className="mb-4 text-sm text-primary bg-secondary px-4 py-3 rounded-lg border border-border flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              Sesion cerrada correctamente
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-foreground text-sm font-medium">
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
                className={`h-11 bg-background border-border focus:border-primary focus:ring-ring/20 transition-all placeholder:text-muted-foreground/50 ${
                  fieldErrors.username ? "border-destructive focus:border-destructive focus:ring-destructive/20" : ""
                }`}
              />
              {fieldErrors.username && (
                <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                  <AlertCircle className="w-4 h-4" />
                  {fieldErrors.username}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-foreground text-sm font-medium">
                Contrasena
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Ingrese su contrasena"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }))
                  }}
                  autoComplete="current-password"
                  className={`h-11 pr-12 bg-background border-border focus:border-primary focus:ring-ring/20 transition-all placeholder:text-muted-foreground/50 ${
                    fieldErrors.password ? "border-destructive focus:border-destructive focus:ring-destructive/20" : ""
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  aria-label={showPassword ? "Ocultar contrasena" : "Mostrar contrasena"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {fieldErrors.password && (
                <div className="flex items-center gap-1 text-sm text-destructive mt-1">
                  <AlertCircle className="w-4 h-4" />
                  {fieldErrors.password}
                </div>
              )}
            </div>

            {requires2fa && (
              <div className="space-y-2">
                <Label htmlFor="otp" className="text-foreground text-sm font-medium">
                  Codigo OTP
                </Label>
                <Input
                  id="otp"
                  type="text"
                  placeholder="Ingrese el codigo de 6 digitos"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  autoComplete="one-time-code"
                  className="h-11 bg-background border-border focus:border-primary focus:ring-ring/20 transition-all placeholder:text-muted-foreground/50"
                />
              </div>
            )}

            {error && (
              <div className="text-sm text-destructive bg-destructive/5 px-4 py-3 rounded-lg border border-destructive/20 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-11 bg-primary hover:bg-primary/90 text-primary-foreground font-medium transition-all"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="animate-spin h-4 w-4" />
                  Iniciando sesion...
                </span>
              ) : (
                "Iniciar Sesion"
              )}
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground mt-6">
            CIPA - Todos los derechos reservados.
          </p>
        </div>
      </div>
    </div>
  )
}
