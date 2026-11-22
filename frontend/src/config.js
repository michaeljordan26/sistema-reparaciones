// Rutas base de cada microservicio (pasan por el proxy de Vite o de nginx).
export const SERVICIOS = {
  usuarios: '/api/usuarios',
  clientes: '/api/clientes',
  ordenes: '/api/ordenes',
  reparaciones: '/api/reparaciones',
  inventario: '/api/inventario',
  facturacion: '/api/facturacion',
  reportes: '/api/reportes',
}

export const NOMBRE_SERVICIO = {
  usuarios: 'usuarios', clientes: 'clientes', ordenes: 'órdenes', reparaciones: 'reparaciones',
  inventario: 'inventario', facturacion: 'facturación', reportes: 'reportes',
}

export const ROLES = ['ADMINISTRADOR', 'RECEPCIONISTA', 'TECNICO', 'CAJA', 'INVENTARIO']
