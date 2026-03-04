import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'

interface DetailModalProps {
  open: boolean
  title: string
  description?: string
  onClose: () => void
  children: ReactNode
}

export default function DetailModal({ open, title, description, onClose, children }: DetailModalProps) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-[1px] p-4" onClick={onClose}>
      <div
        className="mx-auto mt-8 w-full max-w-3xl rounded-2xl border border-emerald-200 bg-white shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-emerald-100 p-5">
          <div>
            <h3 className="text-xl font-semibold text-emerald-900">{title}</h3>
            {description ? <p className="mt-1 text-sm text-emerald-700">{description}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-2 text-emerald-700 hover:bg-emerald-50"
            aria-label="Cerrar modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="max-h-[75vh] overflow-y-auto p-5">{children}</div>
      </div>
    </div>
  )
}
