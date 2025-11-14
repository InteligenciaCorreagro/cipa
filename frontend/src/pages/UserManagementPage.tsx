import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/services/api'
import { useNavigate } from 'react-router-dom'

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
      navigate('/dashboard')
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
      setUsers(response.data.usuarios)
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
    return new Date(dateString).toLocaleString('es-CO')
  }

  const getRolBadgeColor = (rol: string) => {
    switch (rol) {
      case 'admin':
        return 'bg-red-100 text-red-800'
      case 'editor':
        return 'bg-blue-100 text-blue-800'
      case 'viewer':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (user?.rol !== 'admin') {
    return null
  }

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Gestión de Usuarios</h1>
        <Button variant="outline" onClick={() => navigate('/')}>
          Volver al Dashboard
        </Button>
      </div>

      {/* Formulario de Creación de Usuario */}
      <Card>
        <CardHeader>
          <CardTitle>Crear Nuevo Usuario</CardTitle>
          <CardDescription>
            Complete el formulario para crear un nuevo usuario en el sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">Usuario *</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="nombre.usuario"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="usuario@ejemplo.com"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Contraseña *</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rol">Rol *</Label>
                <Select
                  value={newUser.rol}
                  onValueChange={(value) => setNewUser({ ...newUser, rol: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar rol" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">Viewer (Solo lectura)</SelectItem>
                    <SelectItem value="editor">Editor (Lectura y escritura)</SelectItem>
                    <SelectItem value="admin">Admin (Control total)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
                {error}
              </div>
            )}

            {success && (
              <div className="text-sm text-green-600 bg-green-50 p-3 rounded">
                {success}
              </div>
            )}

            <Button type="submit" className="w-full md:w-auto">
              Crear Usuario
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Lista de Usuarios */}
      <Card>
        <CardHeader>
          <CardTitle>Usuarios Registrados</CardTitle>
          <CardDescription>
            Total: {users.length} usuarios
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">Cargando usuarios...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Último Acceso</TableHead>
                    <TableHead>Fecha Creación</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.username}</TableCell>
                      <TableCell>{user.email || '-'}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${getRolBadgeColor(user.rol)}`}>
                          {user.rol.toUpperCase()}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          user.activo ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {user.activo ? 'ACTIVO' : 'INACTIVO'}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(user.ultimo_acceso)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(user.fecha_creacion)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
