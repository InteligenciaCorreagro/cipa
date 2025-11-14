import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  FileText,
  LogOut,
  Menu,
  X,
  Users,
  FileBarChart
} from 'lucide-react'
import { useState } from 'react'

export default function MainLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'editor', 'viewer'] },
    { path: '/notas', icon: FileText, label: 'Consulta de Notas', roles: ['admin', 'editor', 'viewer'] },
    { path: '/reporte-operativo', icon: FileBarChart, label: 'Reporte Operativo', roles: ['admin', 'editor', 'viewer'] },
    { path: '/usuarios', icon: Users, label: 'Gestión de Usuarios', roles: ['admin'] },
  ]

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-card border-r border-border transition-all duration-300 flex flex-col`}
      >
        {/* Header */}
        <div className="h-16 border-b border-border flex items-center justify-between px-4">
          {sidebarOpen && (
            <h1 className="text-xl font-bold text-primary">Correagro</h1>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems
            .filter((item) => !user?.rol || item.roles.includes(user.rol))
            .map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={isActive ? 'default' : 'ghost'}
                    className={`w-full justify-start ${!sidebarOpen && 'justify-center'}`}
                  >
                    <Icon className="h-5 w-5" />
                    {sidebarOpen && <span className="ml-3">{item.label}</span>}
                  </Button>
                </Link>
              )
            })}
        </nav>

        {/* User section */}
        <div className="border-t border-border p-4">
          <div className={`flex items-center ${!sidebarOpen && 'justify-center'}`}>
            {sidebarOpen ? (
              <>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user?.username}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.rol}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLogout}
                  title="Cerrar sesión"
                >
                  <LogOut className="h-5 w-5" />
                </Button>
              </>
            ) : (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                title="Cerrar sesión"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="container mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
