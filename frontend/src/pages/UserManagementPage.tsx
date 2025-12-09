import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, Badge } from '@/components/ui/Table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/services/api'
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
  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/auth/users')
      setUsers(response.data.usuarios || response.data)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al cargar usuarios')
    } finally {
      setLoading(false)
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
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al crear usuario')
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

  const getRolVariant = (rol: string): any => {
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
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
            {user.username.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-gray-900">{user.username}</p>
            <div className="flex items-center gap-1 text-xs text-gray-500">
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
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-700">{formatDate(user.ultimo_acceso)}</span>
        </div>
      )
    },
    {
      key: 'fecha_creacion',
      label: 'Creación',
      render: (user: User) => (
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-700">{formatDate(user.fecha_creacion)}</span>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header con gradiente */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg">
              <Users className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                Gestión de Usuarios
              </h1>
              <p className="text-gray-600 mt-1">
                Administra los usuarios del sistema
              </p>
            </div>
          </div>
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

      {/* Stats rápidas */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card className="border-2 border-blue-200 shadow-md hover:shadow-lg transition-all">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <p className="text-sm font-medium text-gray-600">Total Usuarios</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{users.length}</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-emerald-200 shadow-md hover:shadow-lg transition-all">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <p className="text-sm font-medium text-gray-600">Activos</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {users.filter(u => u.activo).length}
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-red-200 shadow-md hover:shadow-lg transition-all">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center">
                <Shield className="w-6 h-6 text-red-600" />
              </div>
            </div>
            <p className="text-sm font-medium text-gray-600">Admins</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {users.filter(u => u.rol === 'admin').length}
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-purple-200 shadow-md hover:shadow-lg transition-all">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center">
                <Edit className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <p className="text-sm font-medium text-gray-600">Editores</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {users.filter(u => u.rol === 'editor').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Formulario de Creación de Usuario */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-emerald-600" />
            <div>
              <CardTitle className="text-lg">Crear Nuevo Usuario</CardTitle>
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
                <Label htmlFor="username" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Usuario *
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="nombre.usuario"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="h-11 border-2 focus:border-emerald-500"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="usuario@ejemplo.com"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="h-11 border-2 focus:border-emerald-500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Contraseña *
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="h-11 border-2 focus:border-emerald-500"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rol" className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Rol *
                </Label>
                <Select
                  value={newUser.rol}
                  onValueChange={(value) => setNewUser({ ...newUser, rol: value })}
                >
                  <SelectTrigger className="h-11 border-2 focus:border-emerald-500">
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
              <div className="flex items-center gap-3 text-sm text-red-700 bg-red-50 p-4 rounded-lg border-2 border-red-200">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                {error}
              </div>
            )}

            {success && (
              <div className="flex items-center gap-3 text-sm text-emerald-700 bg-emerald-50 p-4 rounded-lg border-2 border-emerald-200">
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                {success}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full md:w-auto bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 shadow-lg"
            >
              <UserPlus className="mr-2 h-4 w-4" />
              Crear Usuario
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Lista de Usuarios */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="border-b bg-gradient-to-br from-gray-50 to-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-600" />
                <CardTitle className="text-lg">Usuarios Registrados</CardTitle>
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
                <Loader2 className="w-12 h-12 text-emerald-600 animate-spin mx-auto" />
                <p className="text-gray-500">Cargando usuarios...</p>
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
              <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
                <Users className="w-8 h-8 text-gray-400" />
              </div>
              <div className="text-center">
                <p className="text-gray-900 font-medium">Sin usuarios</p>
                <p className="text-sm text-gray-500 mt-1">
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