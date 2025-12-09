import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface Column<T> {
  key: string
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
  bordered = true
}: TableProps<T>) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-gray-500 text-sm">Cargando datos...</p>
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-gray-400"
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
        <p className="text-gray-500 font-medium">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className={cn(
            'bg-gradient-to-r from-gray-50 to-gray-100',
            bordered && 'border-b-2 border-gray-200'
          )}>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  'font-semibold text-sm text-gray-700',
                  compact ? 'py-3 px-4' : 'py-4 px-6',
                  column.align === 'center' && 'text-center',
                  column.align === 'right' && 'text-right',
                  column.align !== 'center' && column.align !== 'right' && 'text-left',
                  column.sortable && 'cursor-pointer hover:text-emerald-600 transition-colors select-none'
                )}
                style={{ width: column.width }}
              >
                <div className="flex items-center gap-2 justify-between">
                  <span>{column.label}</span>
                  {column.sortable && (
                    <svg
                      className="w-4 h-4 text-gray-400"
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
          bordered && 'divide-y divide-gray-100'
        )}>
          {data.map((row, index) => (
            <tr
              key={keyExtractor(row)}
              className={cn(
                'transition-all duration-200',
                hoverable && 'hover:bg-gray-50/80 hover:shadow-sm cursor-pointer',
                striped && index % 2 === 0 && 'bg-gray-50/30',
                onRowClick && 'cursor-pointer'
              )}
              onClick={() => onRowClick?.(row)}
              style={{ animationDelay: `${index * 30}ms` }}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    'text-gray-900',
                    compact ? 'py-3 px-4' : 'py-4 px-6',
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right'
                  )}
                >
                  {column.render 
                    ? column.render(row)
                    : (row as any)[column.key]
                  }
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
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
    default: 'bg-gray-100 text-gray-700 border-gray-200',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-orange-50 text-orange-700 border-orange-200',
    danger: 'bg-red-50 text-red-700 border-red-200',
    info: 'bg-blue-50 text-blue-700 border-blue-200'
  }

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border',
      variants[variant],
      className
    )}>
      {children}
    </span>
  )
}