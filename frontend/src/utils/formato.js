const moneda = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
const fechaHora = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Bogota' })
const fechaCorta = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeZone: 'UTC' })

export const dinero = (v) => (v === null || v === undefined ? '—' : moneda.format(v))
export const fecha = (v) => (v ? fechaHora.format(new Date(v)) : '—')
// Para campos tipo date ('2026-11-07'), sin desfase de zona horaria
export const dia = (v) => (v ? fechaCorta.format(new Date(`${v}T00:00:00Z`)) : '—')

export const ESTADOS_ORDEN = {
  RECIBIDO: { texto: 'Recibido', color: 'secondary', icono: 'box-arrow-in-down' },
  EN_DIAGNOSTICO: { texto: 'En diagnóstico', color: 'info', icono: 'search' },
  ESPERANDO_APROBACION: { texto: 'Esperando aprobación', color: 'warning', icono: 'hourglass-split' },
  EN_REPARACION: { texto: 'En reparación', color: 'primary', icono: 'tools' },
  LISTO_ENTREGA: { texto: 'Listo para entregar', color: 'success', icono: 'check2-circle' },
  ENTREGADO: { texto: 'Entregado', color: 'dark', icono: 'bag-check' },
  CANCELADO: { texto: 'Cancelado', color: 'danger', icono: 'x-circle' },
}

export const FLUJO = ['RECIBIDO', 'EN_DIAGNOSTICO', 'ESPERANDO_APROBACION', 'EN_REPARACION', 'LISTO_ENTREGA', 'ENTREGADO']

export const PRIORIDADES = {
  URGENTE: 'danger', ALTA: 'warning', MEDIA: 'info', BAJA: 'secondary',
}

export const TIPOS_EQUIPO = {
  PORTATIL: 'Portátil', ESCRITORIO: 'Escritorio', TODO_EN_UNO: 'Todo en uno', IMPRESORA: 'Impresora',
  TABLET: 'Tablet', SERVIDOR: 'Servidor', OTRO: 'Otro',
}

export const nombreCliente = (c) => (c ? `${c.nombres} ${c.apellidos}` : '—')
export const nombreEquipo = (e) => (e ? `${TIPOS_EQUIPO[e.tipo_equipo] || e.tipo_equipo} ${e.marca} ${e.modelo}` : '—')
