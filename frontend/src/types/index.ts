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
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  user: User
}

export interface NotaCredito {
  id: number
  numero_nota: string
  fecha_nota: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  tipo_inventario: string
  valor_total: number
  cantidad: number
  saldo_pendiente: number
  cantidad_pendiente: number
  estado: 'PENDIENTE' | 'PARCIAL' | 'APLICADA'
  fecha_registro: string
  fecha_aplicacion_completa: string | null
}

export interface Aplicacion {
  id: number
  id_nota: number
  numero_nota: string
  numero_factura: string
  fecha_factura: string
  nit_cliente: string
  codigo_producto: string
  valor_aplicado: number
  cantidad_aplicada: number
  fecha_aplicacion: string
}

export interface Estadisticas {
  total_notas: number
  total_valor: number
  saldo_pendiente_total: number
  notas_pendientes: number
  notas_parciales: number
  notas_aplicadas: number
  promedio_valor: number
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
  details?: string
}

export interface Factura {
  id: number
  numero_factura: string
  fecha_factura: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  tipo_inventario: string | null
  valor_total: number
  cantidad: number
  valor_transado: number
  cantidad_transada: number
  estado: 'VALIDA' | 'PROCESADA' | 'ANULADA'
  tiene_nota_credito: boolean
  es_valida: boolean
  razon_invalidez: string | null
  fecha_registro: string
  aplicaciones?: Aplicacion[]
}

export interface EstadisticasFacturas {
  total_facturas: number
  facturas_validas: number
  facturas_invalidas: number
  valor_total_facturado: number
  valor_total_transado: number
  facturas_con_notas: number
  por_estado: {
    estado: string
    cantidad: number
    valor_total: number
  }[]
  facturas_ultimos_30_dias: number
}

export interface Transaccion {
  id: number
  numero_factura: string
  fecha_factura: string
  nit_cliente: string
  nombre_cliente: string
  codigo_producto: string
  nombre_producto: string
  valor_total: number
  valor_transado: number
  cantidad: number
  cantidad_transada: number
  estado: string
  tiene_nota_credito: boolean
}
