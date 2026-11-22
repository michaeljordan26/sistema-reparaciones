// Tablero de inicio: cada rol ve los indicadores que le sirven (datos de ms-reportes).
import { Link } from 'react-router-dom'
import { Cargando, ErrorAlerta, EstadoOrden, Kpi, Prioridad, Vacio, useCarga } from '../components/comunes'
import { useAuth } from '../context/AuthContext'
import { api } from '../services/api'
import { dinero, ESTADOS_ORDEN, fecha } from '../utils/formato'

function TablaPendientes({ lista, limite = 8 }) {
  if (!lista?.length) return <Vacio texto="No hay órdenes pendientes" icono="emoji-smile" />
  return (
    <div className="table-responsive">
      <table className="table table-sm table-hover mb-0">
        <thead><tr><th>Orden</th><th>Estado</th><th>Prioridad</th><th>Técnico</th><th>Recibida</th></tr></thead>
        <tbody>
          {lista.slice(0, limite).map((o) => (
            <tr key={o.id_orden}>
              <td><Link to={`/ordenes/${o.id_orden}`} className="fw-semibold">{o.codigo}</Link></td>
              <td><EstadoOrden estado={o.estado} /></td>
              <td><Prioridad valor={o.prioridad} /></td>
              <td className="small">{o.tecnico || <span className="text-warning">Sin asignar</span>}</td>
              <td className="small text-nowrap">{fecha(o.fecha_recepcion)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Barras({ datos }) {
  const total = Object.values(datos).reduce((a, b) => a + b, 0) || 1
  return Object.entries(datos).map(([k, v]) => (
    <div key={k} className="mb-2">
      <div className="d-flex justify-content-between small"><span>{ESTADOS_ORDEN[k]?.texto || k}</span><span className="fw-semibold">{v}</span></div>
      <div className="progress" style={{ height: 6 }}>
        <div className={`progress-bar bg-${ESTADOS_ORDEN[k]?.color || 'primary'}`} style={{ width: `${(v / total) * 100}%` }} />
      </div>
    </div>
  ))
}

function PanelAdmin() {
  const { datos: p, cargando, error, recargar } = useCarga(() => api('reportes', '/reportes/panel'))
  if (cargando && !p) return <Cargando />
  if (error) return <ErrorAlerta error={error} onReintentar={recargar} />
  const o = p.ordenes.datos, f = p.finanzas.datos, inv = p.inventario.datos, g = p.garantias.datos, a = p.auditoria.datos
  const caido = Object.entries(p).filter(([, s]) => s && s.disponible === false)
  return (
    <>
      {caido.map(([k, s]) => <div key={k} className="alert alert-warning py-2 small"><i className="bi bi-plug me-1" />Sección {k}: {s.error}</div>)}
      <div className="row g-3 mb-3">
        <div className="col-sm-6 col-xl-3"><Kpi titulo="Órdenes pendientes" valor={o?.pendientes ?? '—'} icono="hourglass-split" color="warning" detalle={o && `${o.sin_tecnico} sin técnico`} /></div>
        <div className="col-sm-6 col-xl-3"><Kpi titulo="Ingresos (30 días)" valor={f ? dinero(f.ingresos.total) : '—'} icono="cash-stack" color="success" detalle={f && `${f.ingresos.cantidad_pagos} pagos`} /></div>
        <div className="col-sm-6 col-xl-3"><Kpi titulo="Por cobrar" valor={f ? dinero(f.cartera.total_por_cobrar) : '—'} icono="wallet2" color="danger" detalle={f && `${f.cartera.facturas.length} facturas`} /></div>
        <div className="col-sm-6 col-xl-3"><Kpi titulo="Repuestos con stock bajo" valor={inv?.stock_bajo.length ?? '—'} icono="box-seam" color="info" detalle={inv && `Inventario: ${dinero(inv.valor_inventario_costo)}`} /></div>
      </div>
      <div className="row g-3">
        <div className="col-xl-8">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header d-flex justify-content-between"><span>Órdenes pendientes por prioridad</span><Link to="/ordenes" className="small">Ver todas</Link></div>
            <div className="card-body"><TablaPendientes lista={o?.lista_pendientes} /></div>
          </div>
        </div>
        <div className="col-xl-4">
          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header">Órdenes por estado</div>
            <div className="card-body">
              {o ? <Barras datos={o.por_estado} /> : '—'}
              {o?.dias_promedio_hasta_entrega != null && <div className="small text-muted mt-2">Tiempo promedio hasta la entrega: <strong>{o.dias_promedio_hasta_entrega < 1 ? 'menos de 1 día' : `${o.dias_promedio_hasta_entrega} días`}</strong></div>}
            </div>
          </div>
          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header">Carga por técnico</div>
            <ul className="list-group list-group-flush">
              {o && Object.keys(o.carga_por_tecnico).length === 0 && <li className="list-group-item small text-muted">Sin órdenes asignadas</li>}
              {o && Object.entries(o.carga_por_tecnico).map(([t, n]) => (
                <li key={t} className="list-group-item d-flex justify-content-between small">{t}<span className="badge text-bg-primary">{n}</span></li>))}
            </ul>
          </div>
        </div>
        <div className="col-md-6 col-xl-4">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header d-flex justify-content-between"><span>Stock bajo</span><Link to="/inventario" className="small">Inventario</Link></div>
            <ul className="list-group list-group-flush">
              {inv?.stock_bajo.length === 0 && <li className="list-group-item small text-muted">Todo en orden</li>}
              {inv?.stock_bajo.map((r) => (
                <li key={r.id_repuesto} className="list-group-item d-flex justify-content-between small">
                  <span><code>{r.codigo}</code> {r.nombre}</span><span className="text-danger fw-semibold">{r.stock_actual}/{r.stock_minimo}</span>
                </li>))}
            </ul>
          </div>
        </div>
        <div className="col-md-6 col-xl-4">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header">Ingresos por método (30 días)</div>
            <ul className="list-group list-group-flush">
              {f && Object.keys(f.ingresos.por_metodo).length === 0 && <li className="list-group-item small text-muted">Sin pagos</li>}
              {f && Object.entries(f.ingresos.por_metodo).map(([m, v]) => (
                <li key={m} className="list-group-item d-flex justify-content-between small">{m}<strong>{dinero(v)}</strong></li>))}
            </ul>
          </div>
        </div>
        <div className="col-md-12 col-xl-4">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header d-flex justify-content-between"><span>Actividad y garantías (24 h)</span><Link to="/auditoria" className="small">Auditoría</Link></div>
            <ul className="list-group list-group-flush small">
              <li className="list-group-item d-flex justify-content-between">Operaciones registradas<strong>{a?.total_operaciones ?? '—'}</strong></li>
              <li className="list-group-item d-flex justify-content-between">Accesos denegados<strong className="text-danger">{a?.accesos_denegados ?? '—'}</strong></li>
              <li className="list-group-item d-flex justify-content-between">Inicios de sesión fallidos<strong>{a?.inicios_sesion_fallidos ?? '—'}</strong></li>
              <li className="list-group-item d-flex justify-content-between">Garantías vigentes<strong>{g?.vigentes ?? '—'}</strong></li>
              <li className="list-group-item d-flex justify-content-between">Reclamaciones abiertas<strong>{g?.reclamaciones_abiertas ?? '—'}</strong></li>
            </ul>
          </div>
        </div>
      </div>
    </>
  )
}

function SeccionRecepcion() {
  const { datos: o, cargando, error } = useCarga(() => api('reportes', '/reportes/ordenes'))
  if (cargando) return <Cargando />
  if (error) return <ErrorAlerta error={error} />
  return (
    <>
      <div className="row g-3 mb-3">
        <div className="col-sm-4"><Kpi titulo="Pendientes" valor={o.pendientes} icono="hourglass-split" color="warning" /></div>
        <div className="col-sm-4"><Kpi titulo="Listas para entregar" valor={o.por_estado.LISTO_ENTREGA || 0} icono="check2-circle" color="success" /></div>
        <div className="col-sm-4"><Kpi titulo="Sin técnico" valor={o.sin_tecnico} icono="person-exclamation" color="danger" /></div>
      </div>
      <div className="card shadow-sm border-0 mb-3">
        <div className="card-header d-flex justify-content-between"><span>Órdenes pendientes</span><Link to="/ordenes/nueva" className="btn btn-sm btn-primary">Nueva orden</Link></div>
        <div className="card-body"><TablaPendientes lista={o.lista_pendientes} limite={12} /></div>
      </div>
    </>
  )
}

function SeccionTecnico() {
  const { datos, cargando, error } = useCarga(() => api('ordenes', '/ordenes/mis-ordenes'))
  if (cargando) return <Cargando />
  if (error) return <ErrorAlerta error={error} />
  const lista = datos.map((o) => ({ id_orden: o.id_orden, codigo: o.codigo, estado: o.estado_actual, prioridad: o.prioridad,
    tecnico: o.asignacion_activa?.nombre_tecnico, fecha_recepcion: o.fecha_recepcion }))
  return (
    <div className="card shadow-sm border-0 mb-3">
      <div className="card-header">Mis órdenes asignadas ({lista.length})</div>
      <div className="card-body"><TablaPendientes lista={lista} limite={20} /></div>
    </div>
  )
}

function SeccionCaja() {
  const { datos: f, cargando, error } = useCarga(() => api('reportes', '/reportes/finanzas'))
  if (cargando) return <Cargando />
  if (error) return <ErrorAlerta error={error} />
  return (
    <div className="row g-3 mb-3">
      <div className="col-sm-4"><Kpi titulo="Ingresos (30 días)" valor={dinero(f.ingresos.total)} icono="cash-stack" color="success" /></div>
      <div className="col-sm-4"><Kpi titulo="Por cobrar" valor={dinero(f.cartera.total_por_cobrar)} icono="wallet2" color="danger" /></div>
      <div className="col-sm-4"><Kpi titulo="Facturas con saldo" valor={f.cartera.facturas.length} icono="receipt" color="warning" detalle={<Link to="/facturacion">Ver facturación</Link>} /></div>
    </div>
  )
}

function SeccionInventario() {
  const { datos: inv, cargando, error } = useCarga(() => api('reportes', '/reportes/inventario'))
  if (cargando) return <Cargando />
  if (error) return <ErrorAlerta error={error} />
  return (
    <>
      <div className="row g-3 mb-3">
        <div className="col-sm-4"><Kpi titulo="Repuestos" valor={inv.total_repuestos} icono="box-seam" /></div>
        <div className="col-sm-4"><Kpi titulo="Valor del inventario" valor={dinero(inv.valor_inventario_costo)} icono="currency-dollar" color="success" /></div>
        <div className="col-sm-4"><Kpi titulo="Stock bajo" valor={inv.stock_bajo.length} icono="exclamation-triangle" color="danger" detalle={<Link to="/inventario">Ver inventario</Link>} /></div>
      </div>
    </>
  )
}

export default function Inicio() {
  const { usuario, tieneRol } = useAuth()
  const hora = new Date().getHours()
  const saludo = hora < 12 ? 'Buenos días' : hora < 19 ? 'Buenas tardes' : 'Buenas noches'
  return (
    <>
      <div className="mb-4">
        <h1 className="h3 mb-0">{saludo}, {usuario.nombres}</h1>
        <div className="text-muted small">Resumen del taller</div>
      </div>
      {tieneRol('ADMINISTRADOR') ? <PanelAdmin /> : (
        <>
          {tieneRol('RECEPCIONISTA') && <SeccionRecepcion />}
          {tieneRol('CAJA') && <SeccionCaja />}
          {tieneRol('TECNICO') && <SeccionTecnico />}
          {tieneRol('INVENTARIO') && <SeccionInventario />}
        </>
      )}
    </>
  )
}
