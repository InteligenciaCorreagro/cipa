export interface User {
  id: number
  username: string
  email: string
  rol: 'admin' | 'editor' | 'viewer'
  activo: boolean
  ultimo_acceso: string | null
  fecha_creacion: string
}

export interface LoginRequest {
  username: string
  password: string
  otp?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: User
  requires_2fa?: boolean
}

export interface MotivoNoAplicacion {
  id: number
  numero_nota: string
  numero_factura: string
  motivo: string
  detalle?: string
  fecha_registro: string
}

export interface NotaCredito {
  id: number
  numero_nota: string
  fecha_nota: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  valor_total: number
  cantidad: number
  saldo_pendiente: number
  cantidad_pendiente: number
  estado: 'PENDIENTE' | 'APLICADA' | 'NO_APLICADA'
  es_agente: number
  fecha_registro: string
  fecha_aplicacion_completa: string | null
  aplicaciones?: Aplicacion[]
  motivos_no_aplicacion?: MotivoNoAplicacion[]
}

export interface Aplicacion {
  id: number
  id_nota: number
  id_factura: number
  numero_nota: string
  numero_factura: string
  fecha_factura: string
  nit_cliente: string
  codigo_producto: string
  valor_aplicado: number
  cantidad_aplicada: number
  fecha_aplicacion: string
  valor_factura_antes?: number
  valor_factura_despues?: number
}

export interface Estadisticas {
  total_notas: number
  valor_total: number
  saldo_pendiente_total: number
  notas_pendientes: number
  notas_aplicadas: number
  notas_no_aplicadas: number
  total_aplicaciones: number
  monto_total_aplicado: number
}

export interface NotasPorEstado {
  estado: string
  cantidad: number
  valor_total: number
  saldo_pendiente: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limite: number
  offset: number
}

export interface ApiError {
  error: string
  message?: string
  details?: string
}

export interface Factura {
  id: number
  numero_factura: string
  codigo_factura: string
  fecha_factura: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  valor_total: number
  cantidad_original: number
  cantidad_restante: number
  valor_restante: number
  estado: 'ACTIVA' | 'ANULADA'
  registrable: number
  repeticion_index: number
  indice_linea?: number
  total_repeticiones: number
  suma_total_repeticiones: number
  fecha_registro: string
  aplicaciones?: Aplicacion[]
}

export interface EstadisticasFacturas {
  facturas_validas: number
  valor_total_facturado: number
  facturas_registrables: number
  facturas_no_registrables: number
  facturas_rechazadas: number
  aplicaciones_total: number
  total_aplicado: number
}

export interface Transaccion {
  id: number
  numero_nota: string
  numero_factura: string
  cantidad_aplicada: number
  valor_aplicado: number
  fecha_aplicacion: string
}

export interface NotaPendiente {
  id: number
  numero_nota: string
  prioridad: 'alta' | 'media' | 'baja'
  fecha_vencimiento: string | null
  responsable: string | null
  estado: 'PENDIENTE' | 'EN_PROGRESO' | 'COMPLETADA'
  descripcion: string | null
  fecha_creacion: string
  fecha_actualizacion: string
}

export interface AplicacionSistema {
  id: number
  nombre: string
  version: string
  fecha_instalacion: string | null
  estado: 'ACTIVA' | 'INACTIVA'
  uso_total: number
  ultimo_uso: string | null
  fecha_creacion: string
  fecha_actualizacion: string
}

export interface LogEntry {
  id: number
  entidad: string
  accion: string
  entidad_id: string | null
  usuario: string | null
  payload: string | null
  fecha_registro: string
}
