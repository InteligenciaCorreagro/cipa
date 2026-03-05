import { Loader2 } from 'lucide-react'

interface SessionLoadingOverlayProps {
  visible: boolean
  message?: string | null
}

export default function SessionLoadingOverlay({ visible, message }: SessionLoadingOverlayProps) {
  if (!visible) return null

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/90 backdrop-blur-sm">
      <div className="flex w-[92%] max-w-sm flex-col items-center rounded-2xl border border-border bg-card p-8 shadow-lg">
        <img
          src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-jwwFqToCBnvzQxjVAgBLw7p8FyUsD3.png"
          alt="Correagro Logo"
          className="h-8 w-auto mb-6"
        />
        <Loader2 className="mb-4 h-6 w-6 animate-spin text-primary" />
        <p className="text-center text-sm font-medium text-foreground">
          {message || 'Procesando sesion...'}
        </p>
      </div>
    </div>
  )
}
