import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import {
  LayoutDashboard,
  FileText,
  LogOut,
  Users,
  FileBarChart,
  Calendar,
  ChevronRight,
  Leaf
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
    { path: '/notas', icon: FileText, label: 'Notas de Crédito', roles: ['admin', 'editor', 'viewer'] },
    { path: '/reporte-operativo', icon: FileBarChart, label: 'Reporte Operativo', roles: ['admin', 'editor', 'viewer'] },
    { path: '/admin/procesar-rango', icon: Calendar, label: 'Procesar Rango', roles: ['admin'] },
    { path: '/usuarios', icon: Users, label: 'Usuarios', roles: ['admin'] },
  ]

  const getInitials = (name: string) => {
    return name.substring(0, 2).toUpperCase()
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-72' : 'w-20'
        } bg-white border-r border-gray-200 transition-all duration-300 flex flex-col shadow-sm`}
      >
        {/* Header con logo */}
        <div className="h-20 border-b border-gray-200 flex items-center px-6 bg-gradient-to-r from-emerald-600 to-emerald-700">
          {sidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
                <Leaf className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">CIPA</h1>
                <p className="text-xs text-emerald-100">Correagro S.A.</p>
              </div>
            </div>
          ) : (
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center mx-auto">
              <Leaf className="w-6 h-6 text-white" />
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {menuItems
            .filter((item) => !user?.rol || item.roles.includes(user.rol))
            .map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link key={item.path} to={item.path}>
                  <div
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all group ${
                      isActive
                        ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-lg shadow-emerald-600/30'
                        : 'text-gray-600 hover:bg-gray-100'
                    } ${!sidebarOpen && 'justify-center'}`}
                    title={!sidebarOpen ? item.label : undefined}
                  >
                    <Icon className={`h-5 w-5 ${isActive ? 'text-white' : 'text-gray-500 group-hover:text-emerald-600'}`} />
                    {sidebarOpen && (
                      <>
                        <span className="flex-1 font-medium text-sm">{item.label}</span>
                        {isActive && <ChevronRight className="h-4 w-4" />}
                      </>
                    )}
                  </div>
                </Link>
              )
            })}
        </nav>

        {/* User section */}
        <div className="border-t border-gray-200 p-4">
          {sidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
                {getInitials(user?.username || 'U')}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">{user?.username}</p>
                <p className="text-xs text-gray-500 truncate capitalize">{user?.rol}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                title="Cerrar sesión"
                className="text-gray-400 hover:text-red-600 hover:bg-red-50"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
                {getInitials(user?.username || 'U')}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                title="Cerrar sesión"
                className="text-gray-400 hover:text-red-600 hover:bg-red-50"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Toggle button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute -right-3 top-24 w-6 h-6 bg-white border border-gray-200 rounded-full shadow-md flex items-center justify-center text-gray-400 hover:text-emerald-600 hover:border-emerald-600 transition-colors"
        >
          <ChevronRight className={`h-4 w-4 transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} />
        </button>
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