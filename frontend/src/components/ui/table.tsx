import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface Column<T> {
  key: keyof T | string
  label: string
  render?: (row: T) => ReactNode
  align?: 'left' | 'center' | 'right'
  width?: string
  sortable?: boolean
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (row: T) => string | number
  onRowClick?: (row: T) => void
  emptyMessage?: string
  loading?: boolean
  hoverable?: boolean
  striped?: boolean
  compact?: boolean
  bordered?: boolean
  enablePagination?: boolean
  pageSize?: number
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyMessage = 'No hay datos disponibles',
  loading = false,
  hoverable = true,
  striped = false,
  compact = false,
  bordered = true,
  enablePagination = true,
  pageSize = 25
}: TableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1)

  const totalPages = useMemo(() => {
    if (!enablePagination) return 1
    return Math.max(1, Math.ceil(data.length / pageSize))
  }, [data.length, enablePagination, pageSize])

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages)
    }
  }, [currentPage, totalPages])

  const paginatedData = useMemo(() => {
    if (!enablePagination || data.length <= pageSize) return data
    const start = (currentPage - 1) * pageSize
    return data.slice(start, start + pageSize)
  }, [data, enablePagination, pageSize, currentPage])

  const pageNumbers = useMemo(() => {
    if (totalPages <= 1) return []
    const pages: number[] = []
    const start = Math.max(1, currentPage - 2)
    const end = Math.min(totalPages, currentPage + 2)
    for (let i = start; i <= end; i += 1) {
      pages.push(i)
    }
    return pages
  }, [currentPage, totalPages])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-muted-foreground text-sm">Cargando datos...</p>
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-12 h-12 bg-muted rounded-xl flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-6 h-6 text-muted-foreground"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p className="text-muted-foreground text-sm font-medium">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className={cn(
            'bg-muted/50',
            bordered && 'border-b border-border'
          )}>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={cn(
                  'text-xs font-medium text-muted-foreground uppercase tracking-wider',
                  compact ? 'py-3 px-4' : 'py-3 px-6',
                  column.align === 'center' && 'text-center',
                  column.align === 'right' && 'text-right',
                  column.align !== 'center' && column.align !== 'right' && 'text-left',
                  column.sortable && 'cursor-pointer hover:text-foreground transition-colors select-none'
                )}
                style={{ width: column.width }}
              >
                <div className="flex items-center gap-2 justify-between">
                  <span>{column.label}</span>
                  {column.sortable && (
                    <svg
                      className="w-4 h-4 text-muted-foreground/50"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                    </svg>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={cn(
          bordered && 'divide-y divide-border'
        )}>
          {paginatedData.map((row, index) => (
            <tr
              key={keyExtractor(row)}
              className={cn(
                'transition-colors',
                hoverable && 'hover:bg-muted/30 cursor-pointer',
                striped && index % 2 === 0 && 'bg-muted/20',
                onRowClick && 'cursor-pointer'
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((column) => (
                <td
                  key={String(column.key)}
                  className={cn(
                    'text-foreground',
                    compact ? 'py-3 px-4' : 'py-3.5 px-6',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right'
                  )}
                >
                  {column.render 
                    ? column.render(row)
                    : (() => {
                        const value = (row as Record<string, unknown>)[column.key as string]
                        if (typeof value === 'string' || typeof value === 'number') {
                          return value
                        }
                        if (value === null || value === undefined) {
                          return ''
                        }
                        return String(value)
                      })()
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {enablePagination && totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3">
          <p className="text-sm text-muted-foreground">
            Pagina {currentPage} de {totalPages}
          </p>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="rounded-lg border border-border px-3 py-1.5 text-sm text-foreground hover:bg-accent disabled:opacity-50 transition-colors"
            >
              Anterior
            </button>
            {pageNumbers.map((page) => (
              <button
                key={page}
                type="button"
                onClick={() => setCurrentPage(page)}
                className={cn(
                  'rounded-lg border px-3 py-1.5 text-sm transition-colors',
                  currentPage === page
                    ? 'border-primary bg-primary text-primary-foreground'
                    : 'border-border text-foreground hover:bg-accent'
                )}
              >
                {page}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="rounded-lg border border-border px-3 py-1.5 text-sm text-foreground hover:bg-accent disabled:opacity-50 transition-colors"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Badge component para usar en la tabla
export function Badge({ 
  children, 
  variant = 'default',
  className = ''
}: { 
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  className?: string
}) {
  const variants = {
    default: 'bg-muted text-muted-foreground border-border',
    success: 'bg-primary/8 text-primary border-primary/20',
    warning: 'bg-accent text-foreground border-border',
    danger: 'bg-destructive/8 text-destructive border-destructive/20',
    info: 'bg-secondary text-secondary-foreground border-border'
  }

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border',
      variants[variant],
      className
    )}>
      {children}
    </span>
  )
}
