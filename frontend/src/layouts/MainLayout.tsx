import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { LayoutDashboard, FileText, LogOut, Leaf, Receipt, CalendarRange, ClipboardList } from 'lucide-react'

export default function MainLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'editor', 'viewer'] },
    { path: '/facturas', icon: Receipt, label: 'Facturas', roles: ['admin', 'editor', 'viewer'] },
    { path: '/notas', icon: FileText, label: 'Notas', roles: ['admin', 'editor', 'viewer'] },
    { path: '/procesamiento-facturas', icon: CalendarRange, label: 'Procesamiento', roles: ['admin', 'editor'] },
    { path: '/reporte-operativo', icon: ClipboardList, label: 'Reporte', roles: ['admin', 'editor', 'viewer'] },
  ]

  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-30 border-b border-emerald-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
        <div className="mx-auto flex min-h-16 max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-2 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600">
              <Leaf className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-emerald-900">CIPA</p>
              <p className="text-xs text-emerald-600">Dashboard operativo</p>
            </div>
          </div>
          <nav className="order-3 w-full overflow-x-auto md:order-2 md:w-auto">
            <div className="flex w-max items-center gap-1 rounded-xl border border-emerald-100 bg-emerald-50/50 p-1">
            {menuItems
              .filter((item) => !user?.rol || item.roles.includes(user.rol))
              .map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'text-emerald-700 hover:bg-emerald-100/80'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </nav>
          <div className="order-2 ml-auto flex items-center gap-3 md:order-3">
            <div className="text-right">
              <p className="text-sm font-medium text-emerald-900">{user?.username}</p>
              <p className="text-xs text-emerald-600 capitalize">{user?.rol}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="border-emerald-200 text-emerald-700 hover:bg-emerald-50"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Salir
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
