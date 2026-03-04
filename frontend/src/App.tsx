import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'

import ProtectedRoute from '@/components/ProtectedRoute'
import MainLayout from '@/layouts/MainLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import NotasPage from '@/pages/NotasPage'
import NotaDetailPage from '@/pages/NotaDetailPage'
import FacturasPage from '@/pages/FacturasPage'
import UserManagementPage from '@/pages/UserManagementPage'
import OperativeReportPage from '@/pages/OperativeReportPage'
import AdminProcesarRangoPage from '@/pages/AdminProcesarRangoPage'
import NotasPendientesPage from '@/pages/NotasPendientesPage'
import AplicacionesSistemaPage from '@/pages/AplicacionesSistemaPage'
import LogsPage from '@/pages/LogsPage'
import SessionLoadingOverlay from '@/components/SessionLoadingOverlay'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
})

const BASE_SUBPATH = '/intranet/cipa'
const BASE_PATH = (() => {
  if (import.meta.env.VITE_USE_SUBPATH === 'true') {
    return window.location.pathname.startsWith(BASE_SUBPATH) ? BASE_SUBPATH : '/'
  }
  return '/'
})()

function App() {
  const initialize = useAuthStore((state) => state.initialize)
  const sessionTransitioning = useAuthStore((state) => state.sessionTransitioning)
  const sessionMessage = useAuthStore((state) => state.sessionMessage)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <QueryClientProvider client={queryClient}>
      <SessionLoadingOverlay visible={sessionTransitioning} message={sessionMessage} />
      <BrowserRouter basename={BASE_PATH}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="facturas" element={<FacturasPage />} />
            <Route path="notas" element={<NotasPage />} />
            <Route path="notas/:id" element={<NotaDetailPage />} />
            <Route path="notas-pendientes" element={<NotasPendientesPage />} />
            <Route path="aplicaciones" element={<AplicacionesSistemaPage />} />
            <Route path="usuarios" element={<UserManagementPage />} />
            <Route path="reporte-operativo" element={<OperativeReportPage />} />
            <Route path="procesamiento-facturas" element={<AdminProcesarRangoPage />} />
            <Route path="admin/procesar-rango" element={<AdminProcesarRangoPage />} />
            <Route path="admin/logs" element={<LogsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
