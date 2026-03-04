import { Loader2, Leaf } from 'lucide-react'

interface SessionLoadingOverlayProps {
  visible: boolean
  message?: string | null
}

export default function SessionLoadingOverlay({ visible, message }: SessionLoadingOverlayProps) {
  if (!visible) return null

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-white/90 backdrop-blur-sm">
      <div className="flex w-[92%] max-w-md flex-col items-center rounded-2xl border border-emerald-200 bg-white p-8 shadow-xl">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-emerald-600">
          <Leaf className="h-7 w-7 text-white" />
        </div>
        <Loader2 className="mb-4 h-7 w-7 animate-spin text-emerald-600" />
        <p className="text-center text-sm font-medium text-emerald-900">
          {message || 'Procesando sesión...'}
        </p>
      </div>
    </div>
  )
}
