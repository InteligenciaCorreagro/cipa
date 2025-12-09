"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

// Calendario simple sin Popover
interface CalendarProps {
  selected?: Date
  onSelect?: (date: Date) => void
  disabled?: (date: Date) => boolean
  className?: string
}

function Calendar({ selected, onSelect, disabled, className }: CalendarProps) {
  const [currentMonth, setCurrentMonth] = React.useState(selected || new Date())

  const daysInMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth() + 1,
    0
  ).getDate()

  const firstDayOfMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth(),
    1
  ).getDay()

  const monthNames = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
  ]

  const dayNames = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const selectDate = (day: number) => {
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day)
    if (!disabled || !disabled(date)) {
      onSelect?.(date)
    }
  }

  const isSelected = (day: number) => {
    if (!selected) return false
    return (
      selected.getDate() === day &&
      selected.getMonth() === currentMonth.getMonth() &&
      selected.getFullYear() === currentMonth.getFullYear()
    )
  }

  const isToday = (day: number) => {
    const today = new Date()
    return (
      today.getDate() === day &&
      today.getMonth() === currentMonth.getMonth() &&
      today.getFullYear() === currentMonth.getFullYear()
    )
  }

  const isDisabled = (day: number) => {
    if (!disabled) return false
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day)
    return disabled(date)
  }

  return (
    <div className={cn("p-4 bg-white rounded-xl shadow-xl border border-gray-200", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <Button
          variant="ghost"
          size="icon"
          onClick={previousMonth}
          className="h-8 w-8 hover:bg-emerald-50 hover:text-emerald-600"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-col items-center">
          <h3 className="font-bold text-gray-900">
            {monthNames[currentMonth.getMonth()]}
          </h3>
          <p className="text-xs text-gray-500">{currentMonth.getFullYear()}</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={nextMonth}
          className="h-8 w-8 hover:bg-emerald-50 hover:text-emerald-600"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Day names */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {dayNames.map((day) => (
          <div
            key={day}
            className="text-center text-xs font-semibold text-gray-500 py-2"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Days */}
      <div className="grid grid-cols-7 gap-1">
        {/* Empty cells for days before month starts */}
        {Array.from({ length: firstDayOfMonth }).map((_, index) => (
          <div key={`empty-${index}`} />
        ))}

        {/* Days of the month */}
        {Array.from({ length: daysInMonth }).map((_, index) => {
          const day = index + 1
          const selected = isSelected(day)
          const today = isToday(day)
          const disabled = isDisabled(day)

          return (
            <button
              key={day}
              onClick={() => selectDate(day)}
              disabled={disabled}
              className={cn(
                "h-10 w-10 rounded-lg text-sm font-medium transition-all duration-200",
                "hover:bg-emerald-50 hover:text-emerald-600 hover:scale-105",
                "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2",
                selected && "bg-gradient-to-br from-emerald-500 to-emerald-600 text-white hover:from-emerald-600 hover:to-emerald-700 shadow-lg shadow-emerald-600/30",
                today && !selected && "border-2 border-emerald-500 text-emerald-600 font-bold",
                disabled && "opacity-40 cursor-not-allowed hover:bg-transparent hover:scale-100"
              )}
            >
              {day}
            </button>
          )
        })}
      </div>
    </div>
  )
}

// DatePicker component sin Popover (usa modal simple)
interface DatePickerProps {
  date?: Date
  onDateChange?: (date: Date | undefined) => void
  placeholder?: string
  disabled?: (date: Date) => boolean
  className?: string
}

export function DatePicker({
  date,
  onDateChange,
  placeholder = "Seleccionar fecha",
  disabled,
  className
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false)

  const handleSelect = (selectedDate: Date) => {
    onDateChange?.(selectedDate)
    setOpen(false)
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('es-CO', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    })
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setOpen(!open)}
        className={cn(
          "w-full justify-start text-left font-normal h-12 border-2 hover:border-emerald-500 hover:bg-emerald-50/50 transition-all",
          !date && "text-gray-500",
          className
        )}
      >
        <CalendarIcon className="mr-2 h-4 w-4 text-gray-500" />
        {date ? (
          <span className="text-gray-900 font-medium">{formatDate(date)}</span>
        ) : (
          <span>{placeholder}</span>
        )}
      </Button>

      {/* Modal simple en lugar de Popover */}
      {open && (
        <>
          {/* Overlay oscuro */}
          <div 
            className="fixed inset-0 bg-black/20 z-40 animate-in fade-in duration-200"
            onClick={() => setOpen(false)}
          />
          
          {/* Calendario flotante */}
          <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 animate-in zoom-in-95 duration-200">
            <div className="relative">
              <button
                onClick={() => setOpen(false)}
                className="absolute -top-2 -right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg z-10"
              >
                <X className="w-4 h-4" />
              </button>
              <Calendar
                selected={date}
                onSelect={handleSelect}
                disabled={disabled}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// DateRangePicker component sin Popover
interface DateRange {
  from?: Date
  to?: Date
}

interface DateRangePickerProps {
  dateRange?: DateRange
  onDateRangeChange?: (range: DateRange) => void
  placeholder?: string
  disabled?: (date: Date) => boolean
  className?: string
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  placeholder = "Seleccionar rango de fechas",
  disabled,
  className
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)
  const [tempRange, setTempRange] = React.useState<DateRange>(dateRange || {})

  const handleSelect = (date: Date) => {
    if (!tempRange.from || (tempRange.from && tempRange.to)) {
      // Start new range
      setTempRange({ from: date, to: undefined })
    } else if (date < tempRange.from) {
      // Selected date is before start, make it the new start
      setTempRange({ from: date, to: tempRange.from })
      onDateRangeChange?.({ from: date, to: tempRange.from })
      setOpen(false)
    } else {
      // Complete the range
      setTempRange({ from: tempRange.from, to: date })
      onDateRangeChange?.({ from: tempRange.from, to: date })
      setOpen(false)
    }
  }

  const formatDateRange = (range: DateRange) => {
    if (!range.from) return placeholder
    if (!range.to) return `Desde ${range.from.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })}`
    return `${range.from.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })} - ${range.to.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}`
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setOpen(!open)}
        className={cn(
          "w-full justify-start text-left font-normal h-12 border-2 hover:border-emerald-500 hover:bg-emerald-50/50 transition-all",
          !dateRange?.from && "text-gray-500",
          className
        )}
      >
        <CalendarIcon className="mr-2 h-4 w-4 text-gray-500" />
        <span className={dateRange?.from ? "text-gray-900 font-medium" : ""}>
          {formatDateRange(tempRange)}
        </span>
      </Button>

      {/* Modal simple */}
      {open && (
        <>
          <div 
            className="fixed inset-0 bg-black/20 z-40 animate-in fade-in duration-200"
            onClick={() => setOpen(false)}
          />
          
          <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 animate-in zoom-in-95 duration-200">
            <div className="relative">
              <button
                onClick={() => setOpen(false)}
                className="absolute -top-2 -right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg z-10"
              >
                <X className="w-4 h-4" />
              </button>
              <Calendar
                selected={tempRange.from}
                onSelect={handleSelect}
                disabled={disabled}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}