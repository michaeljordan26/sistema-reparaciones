import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Cargando, Encabezado, ErrorAlerta, Insignia, Kpi, Vacio, useCarga } from '../components/comunes'
import { api } from '../services/api'
import { dinero, fecha } from '../utils/formato'

const COLOR = { PENDIENTE: 'warning', PARCIAL: 'info', PAGADA: 'success', ANULADA: 'secondary' }

function Facturas() {
  const [estado, setEstado] = useState('')
  const { datos, cargando, error, recargar } = useCarga(() => api('facturacion', '/facturas', { query: { estado } }), [estado])
  return (
    <>
      <div className="mb-3" style={{ maxWidth: 260 }}>
        <select className="form-select" value={estado} onChange={(e) => setEstado(e.target.value)}>
          <option value="">Todas las facturas</option>
          {Object.keys(COLOR).map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
      </div>
      <ErrorAlerta error={error} onReintentar={recargar} />
      {cargando ? <Cargando /> : datos.length === 0 ? <Vacio texto="No hay facturas" icono="receipt" /> : (
        <div className="table-responsive">
          <table className="table table-hover mb-0">
            <thead><tr><th>Factura</th><th>Orden</th><th>Fecha</th><th className="text-end">Total</th><th className="text-end">Pagado</th><th className="text-end">Saldo</th><th>Estado</th></tr></thead>
            <tbody>
              {datos.map((f) => (
                <tr key={f.id_factura}>
                  <td className="fw-semibold">{f.numero}</td>
                  <td><Link to={`/ordenes/${f.id_orden}`}>Orden #{f.id_orden}</Link></td>
                  <td className="small">{fecha(f.fecha)}</td>
                  <td className="text-end">{dinero(f.total)}</td>
                  <td className="text-end text-success">{dinero(f.total_pagado)}</td>
                  <td className={`text-end fw-semibold ${f.saldo > 0 ? 'text-danger' : ''}`}>{dinero(f.saldo)}</td>
                  <td><Insignia texto={f.estado} color={COLOR[f.estado]} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

function Cartera() {
  const { datos, cargando, error } = useCarga(() => api('facturacion', '/reportes/cartera'))
  if (cargando) return <Cargando />
  if (error) return <ErrorAlerta error={error} />
  return (
    <>
      <div className="row g-3 mb-3"><div className="col-md-4"><Kpi titulo="Total por cobrar" valor={dinero(datos.total_por_cobrar)} icono="wallet2" color="danger" detalle={`${datos.facturas.length} facturas`} /></div></div>
      {datos.facturas.length === 0 ? <Vacio texto="No hay pagos pendientes" icono="emoji-smile" /> : (
        <table className="table">
          <thead><tr><th>Factura</th><th>Orden</th><th className="text-end">Total</th><th className="text-end">Pagado</th><th className="text-end">Saldo</th><th>Estado</th></tr></thead>
          <tbody>
            {datos.facturas.map((f) => (
              <tr key={f.id_factura}>
                <td>{f.numero}</td><td><Link to={`/ordenes/${f.id_orden}`}>Orden #{f.id_orden}</Link></td>
                <td className="text-end">{dinero(f.total)}</td><td className="text-end">{dinero(f.total_pagado)}</td>
                <td className="text-end fw-semibold text-danger">{dinero(f.saldo)}</td><td><Insignia texto={f.estado} color={COLOR[f.estado]} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}

function Ingresos() {
  const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Bogota' })
  const hace30 = new Date(Date.now() - 30 * 864e5).toLocaleDateString('en-CA', { timeZone: 'America/Bogota' })
  const [rango, setRango] = useState({ desde: hace30, hasta: hoy })
  const { datos, cargando, error } = useCarga(() => api('facturacion', '/reportes/ingresos', { query: rango }), [rango.desde, rango.hasta])
  return (
    <>
      <div className="row g-2 mb-3" style={{ maxWidth: 520 }}>
        <div className="col"><label className="form-label small">Desde</label><input type="date" className="form-control" value={rango.desde} onChange={(e) => setRango({ ...rango, desde: e.target.value })} /></div>
        <div className="col"><label className="form-label small">Hasta</label><input type="date" className="form-control" value={rango.hasta} onChange={(e) => setRango({ ...rango, hasta: e.target.value })} /></div>
      </div>
      <ErrorAlerta error={error} />
      {cargando ? <Cargando /> : datos && (
        <div className="row g-3">
          <div className="col-md-4"><Kpi titulo="Total recaudado" valor={dinero(datos.total)} icono="cash-stack" color="success" detalle={`${datos.cantidad_pagos} pagos`} /></div>
          <div className="col-md-8">
            <table className="table">
              <thead><tr><th>Método</th><th className="text-end">Recaudado</th></tr></thead>
              <tbody>
                {Object.keys(datos.por_metodo).length === 0 && <tr><td colSpan={2} className="text-muted">Sin pagos en el rango</td></tr>}
                {Object.entries(datos.por_metodo).map(([m, v]) => <tr key={m}><td>{m}</td><td className="text-end">{dinero(v)}</td></tr>)}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}

export default function Facturacion() {
  const [pestaña, setPestaña] = useState('facturas')
  return (
    <>
      <Encabezado titulo="Facturación y pagos" icono="cash-coin" subtitulo="Para cobrar, abra la orden desde la factura" />
      <div className="card shadow-sm border-0">
        <div className="card-header pb-0 border-0">
          <ul className="nav nav-tabs card-header-tabs">
            {[['facturas', 'Facturas'], ['cartera', 'Pagos pendientes'], ['ingresos', 'Ingresos']].map(([k, t]) => (
              <li className="nav-item" key={k}><button className={`nav-link ${pestaña === k ? 'active' : ''}`} onClick={() => setPestaña(k)}>{t}</button></li>
            ))}
          </ul>
        </div>
        <div className="card-body">
          {pestaña === 'facturas' && <Facturas />}
          {pestaña === 'cartera' && <Cartera />}
          {pestaña === 'ingresos' && <Ingresos />}
        </div>
      </div>
    </>
  )
}

