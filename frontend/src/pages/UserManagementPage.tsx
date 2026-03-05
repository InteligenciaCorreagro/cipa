import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, Badge } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuthStore } from '@/store/authStore'
import { api, authApi } from '@/services/api'
import { useNavigate } from 'react-router-dom'
import { 
  Users, 
  UserPlus, 
  Shield, 
  Eye, 
  Edit, 
  CheckCircle, 
  XCircle, 
  Calendar,
  Mail,
  Lock,
  ArrowLeft,
  Loader2,
  AlertCircle
} from 'lucide-react'

interface User {
  id: number
  username: string
  email: string | null
  rol: string
  activo: boolean
  ultimo_acceso: string | null
  fecha_creacion: string
}

export default function UserManagementPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [twoFaStatus, setTwoFaStatus] = useState<{ configurado: boolean; habilitado: boolean }>({
    configurado: false,
    habilitado: false
  })
  const [twoFaSecret, setTwoFaSecret] = useState('')
  const [twoFaUri, setTwoFaUri] = useState('')
  const [twoFaOtp, setTwoFaOtp] = useState('')

  // Formulario de nuevo usuario
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    email: '',
    rol: 'viewer'
  })

  // Verificar que el usuario sea admin
  useEffect(() => {
    if (user?.rol !== 'admin') {
      navigate('/')
    }
  }, [user, navigate])

  // Cargar usuarios al montar el componente
  const loadUsers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/auth/users')
      setUsers(response.data.usuarios || response.data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar usuarios'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const status = await authApi.status2fa()
        setTwoFaStatus(status)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al cargar 2FA'
        setError(message)
      }
    }
    loadStatus()
  }, [])

  const handleSetup2fa = async () => {
    setError(null)
    try {
      const res = await authApi.setup2fa()
      setTwoFaSecret(res.secret)
      setTwoFaUri(res.otpauth_uri)
      const status = await authApi.status2fa()
      setTwoFaStatus(status)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al configurar 2FA'
      setError(message)
    }
  }

  const handleEnable2fa = async () => {
    setError(null)
    try {
      await authApi.enable2fa(twoFaOtp)
      setTwoFaOtp('')
      const status = await authApi.status2fa()
      setTwoFaStatus(status)
      setSuccess('2FA habilitado correctamente')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al habilitar 2FA'
      setError(message)
    }
  }

  const handleDisable2fa = async () => {
    setError(null)
    try {
      await authApi.disable2fa()
      setTwoFaSecret('')
      setTwoFaUri('')
      const status = await authApi.status2fa()
      setTwoFaStatus(status)
      setSuccess('2FA deshabilitado correctamente')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al deshabilitar 2FA'
      setError(message)
    }
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    // Validaciones
    if (!newUser.username || !newUser.password) {
      setError('Usuario y contraseña son requeridos')
      return
    }

    if (newUser.password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      return
    }

    try {
      await api.post('/api/auth/register', newUser)
      setSuccess(`Usuario ${newUser.username} creado exitosamente`)

      // Limpiar formulario
      setNewUser({
        username: '',
        password: '',
        email: '',
        rol: 'viewer'
      })

      // Recargar lista de usuarios
      await loadUsers()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al crear usuario'
      setError(message)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Nunca'
    return new Date(dateString).toLocaleString('es-CO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getRolIcon = (rol: string) => {
    switch (rol) {
      case 'admin':
        return Shield
      case 'editor':
        return Edit
      case 'viewer':
        return Eye
      default:
        return Users
    }
  }

  const getRolVariant = (rol: string): 'danger' | 'info' | 'success' | 'default' => {
    switch (rol) {
      case 'admin':
        return 'danger'
      case 'editor':
        return 'info'
      case 'viewer':
        return 'success'
      default:
        return 'default'
    }
  }

  if (user?.rol !== 'admin') {
    return null
  }

  // Columnas para la tabla
  const columns = [
    {
      key: 'usuario',
      label: 'Usuario',
      render: (user: User) => (
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary/8 flex items-center justify-center text-primary font-medium text-sm">
            {user.username.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="font-medium text-foreground">{user.username}</p>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Mail className="w-3 h-3" />
              {user.email || 'Sin email'}
            </div>
          </div>
        </div>
      )
    },
    {
      key: 'rol',
      label: 'Rol',
      align: 'center' as const,
      render: (user: User) => {
        const Icon = getRolIcon(user.rol)
        return (
          <Badge variant={getRolVariant(user.rol)}>
            <Icon className="w-3.5 h-3.5" />
            {user.rol.toUpperCase()}
          </Badge>
        )
      }
    },
    {
      key: 'estado',
      label: 'Estado',
      align: 'center' as const,
      render: (user: User) => (
        <Badge variant={user.activo ? 'success' : 'default'}>
          {user.activo ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
          {user.activo ? 'ACTIVO' : 'INACTIVO'}
        </Badge>
      )
    },
    {
      key: 'ultimo_acceso',
      label: 'Último Acceso',
      render: (user: User) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-foreground">{formatDate(user.ultimo_acceso)}</span>
        </div>
      )
    },
    {
      key: 'fecha_creacion',
      label: 'Creacion',
      render: (user: User) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-foreground">{formatDate(user.fecha_creacion)}</span>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Gestion de Usuarios
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Administra los usuarios del sistema
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => navigate('/')}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Dashboard
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <Users className="w-4 h-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Usuarios</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">{users.length}</p>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <CheckCircle className="w-4 h-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Activos</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">
              {users.filter(u => u.activo).length}
            </p>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <Shield className="w-4 h-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Admins</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">
              {users.filter(u => u.rol === 'admin').length}
            </p>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary/8 flex items-center justify-center">
                <Edit className="w-4 h-4 text-primary" />
              </div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Editores</p>
            </div>
            <p className="text-2xl font-semibold text-foreground">
              {users.filter(u => u.rol === 'editor').length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary" />
            <div>
              <CardTitle className="text-base font-semibold text-foreground">Autenticacion de dos factores</CardTitle>
              <CardDescription className="mt-1">Protege el acceso con OTP</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="flex flex-wrap gap-3">
            <Badge variant={twoFaStatus.habilitado ? 'success' : 'warning'}>
              {twoFaStatus.habilitado ? '2FA activo' : '2FA inactivo'}
            </Badge>
            {twoFaStatus.configurado && !twoFaStatus.habilitado && (
              <Badge variant="info">Configurado</Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-3">
            <Button onClick={handleSetup2fa} variant="outline">
              Generar secreto
            </Button>
            <Button onClick={handleDisable2fa} variant="outline" className="text-red-600">
              Deshabilitar 2FA
            </Button>
          </div>
          {(twoFaSecret || twoFaUri) && (
            <div className="space-y-2 rounded-lg border border-border bg-muted/50 p-4">
              <div className="text-sm text-foreground">Secreto: <span className="font-mono">{twoFaSecret}</span></div>
              <div className="text-sm text-foreground break-all">URI: {twoFaUri}</div>
            </div>
          )}
          <div className="grid gap-3 md:grid-cols-3">
            <div className="md:col-span-2 space-y-2">
              <Label htmlFor="otp" className="text-sm font-medium text-foreground flex items-center gap-2">
                <Lock className="w-4 h-4" />
                OTP
              </Label>
              <Input
                id="otp"
                value={twoFaOtp}
                onChange={(e) => setTwoFaOtp(e.target.value)}
                className="h-11"
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleEnable2fa} className="w-full">
                Habilitar 2FA
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Formulario de Creación de Usuario */}
      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-primary" />
            <div>
              <CardTitle className="text-base font-semibold text-foreground">Crear Nuevo Usuario</CardTitle>
              <CardDescription className="mt-1">
                Complete el formulario para crear un nuevo usuario en el sistema
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <form onSubmit={handleCreateUser} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Usuario *
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="nombre.usuario"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="h-11"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="usuario@ejemplo.com"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Contraseña *
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="h-11"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rol" className="text-sm font-medium text-foreground flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Rol *
                </Label>
                <Select
                  value={newUser.rol}
                  onValueChange={(value) => setNewUser({ ...newUser, rol: value })}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Seleccionar rol" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">
                      <div className="flex items-center gap-2">
                        <Eye className="w-4 h-4" />
                        Viewer (Solo lectura)
                      </div>
                    </SelectItem>
                    <SelectItem value="editor">
                      <div className="flex items-center gap-2">
                        <Edit className="w-4 h-4" />
                        Editor (Lectura y escritura)
                      </div>
                    </SelectItem>
                    <SelectItem value="admin">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Admin (Control total)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-3 text-sm text-destructive bg-destructive/8 p-4 rounded-lg border border-destructive/20">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                {error}
              </div>
            )}

            {success && (
              <div className="flex items-center gap-3 text-sm text-primary bg-primary/8 p-4 rounded-lg border border-primary/20">
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                {success}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full md:w-auto"
            >
              <UserPlus className="mr-2 h-4 w-4" />
              Crear Usuario
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Lista de Usuarios */}
      <Card className="border border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-primary" />
                <CardTitle className="text-base font-semibold text-foreground">Usuarios Registrados</CardTitle>
              </div>
              <CardDescription className="mt-1">
                {users.length} {users.length === 1 ? 'usuario registrado' : 'usuarios registrados'}
              </CardDescription>
            </div>
            <Badge variant="info" className="text-sm">
              Total: {users.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="text-center space-y-3">
                <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
                <p className="text-muted-foreground text-sm">Cargando usuarios...</p>
              </div>
            </div>
          ) : users.length > 0 ? (
            <Table
              columns={columns}
              data={users}
              keyExtractor={(user) => user.id.toString()}
              hoverable
              bordered
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-48 space-y-3">
              <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-muted-foreground" />
              </div>
              <div className="text-center">
                <p className="text-foreground font-medium text-sm">Sin usuarios</p>
                <p className="text-xs text-muted-foreground mt-1">
                  No hay usuarios registrados en el sistema
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
