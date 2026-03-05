import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { LayoutDashboard, FileText, LogOut, Receipt, CalendarRange, ClipboardList } from 'lucide-react'

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
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
        <div className="mx-auto flex min-h-14 max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-2 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-3 group">
            <img
              src="/images/logo-correagro.png"
              alt="Correagro Logo"
              className="h-8 w-auto"
            />
            <span className="text-muted-foreground text-xs font-semibold">×</span>
            <img
              src="/images/logo-cipa.png"
              alt="CIPA Logo"
              className="h-8 w-auto"
            />
          </Link>
          <nav className="order-3 w-full overflow-x-auto md:order-2 md:w-auto">
            <div className="flex w-max items-center gap-0.5 p-0.5">
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
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden lg:inline">{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </nav>
          <div className="order-2 ml-auto flex items-center gap-3 md:order-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-foreground">{user?.username}</p>
              <p className="text-xs text-muted-foreground capitalize">{user?.rol}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-muted-foreground hover:text-foreground"
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span className="hidden sm:inline">Salir</span>
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
