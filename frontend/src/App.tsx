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
import UserManagementPage from '@/pages/UserManagementPage'
import OperativeReportPage from '@/pages/OperativeReportPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
})

// Obtener el base path desde el import.meta.env o usar '/' por defecto
const BASE_PATH = import.meta.env.VITE_USE_SUBPATH === 'true' ? '/intranet/cipa' : '/'

function App() {
  const initialize = useAuthStore((state) => state.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <QueryClientProvider client={queryClient}>
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
            <Route path="notas" element={<NotasPage />} />
            <Route path="notas/:id" element={<NotaDetailPage />} />
            <Route path="usuarios" element={<UserManagementPage />} />
            <Route path="reporte-operativo" element={<OperativeReportPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
