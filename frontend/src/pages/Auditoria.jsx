import { useState } from 'react'
import { Cargando, Encabezado, ErrorAlerta, Kpi, Vacio, useCarga } from '../components/comunes'
import { api } from '../services/api'
import { fecha } from '../utils/formato'

const SERVICIOS = ['ms-usuarios', 'ms-clientes', 'ms-ordenes', 'ms-reparaciones', 'ms-inventario', 'ms-facturacion']
const POR_PAGINA = 25

export default function Auditoria() {
  const [f, setF] = useState({ servicio: '', metodo: '', solo_fallidos: false, desde: '', hasta: '', id_usuario: '' })
  const [pagina, setPagina] = useState(0)
  const resumen = useCarga(() => api('reportes', '/auditoria/resumen'))
  const { datos, cargando, error, recargar } = useCarga(() => api('reportes', '/auditoria', {
    query: { ...f, solo_fallidos: f.solo_fallidos || '', limite: POR_PAGINA, desplazamiento: pagina * POR_PAGINA },
  }), [JSON.stringify(f), pagina])
  const cambiar = (campo) => (e) => { setPagina(0); setF({ ...f, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }) }
  const r = resumen.datos
  const paginas = datos ? Math.max(1, Math.ceil(datos.total / POR_PAGINA)) : 1

  return (
    <>
      <Encabezado titulo="Auditoría" icono="journal-text" subtitulo="Bitácora de solo lectura: un trigger de PostgreSQL impide modificarla o borrarla">
        <button className="btn btn-light" onClick={() => { recargar(); resumen.recargar() }}><i className="bi bi-arrow-clockwise" /></button>
      </Encabezado>
      {r && (
        <div className="row g-3 mb-3">
          <div className="col-sm-6 col-xl-3"><Kpi titulo="Operaciones (24 h)" valor={r.total_operaciones} icono="activity" /></div>
          <div className="col-sm-6 col-xl-3"><Kpi titulo="Accesos denegados" valor={r.accesos_denegados} icono="shield-exclamation" color="danger" /></div>
          <div className="col-sm-6 col-xl-3"><Kpi titulo="Inicios de sesión fallidos" valor={r.inicios_sesion_fallidos} icono="person-lock" color="warning" /></div>
          <div className="col-sm-6 col-xl-3"><Kpi titulo="Servicios activos" valor={Object.keys(r.por_servicio).length} icono="hdd-network" color="success" /></div>
        </div>
      )}
      <div className="card shadow-sm border-0">
        <div className="card-body">
          <div className="row g-2 mb-3 align-items-end">
            <div className="col-md-3"><label className="form-label small">Servicio</label>
              <select className="form-select form-select-sm" value={f.servicio} onChange={cambiar('servicio')}><option value="">Todos</option>{SERVICIOS.map((s) => <option key={s}>{s}</option>)}</select></div>
            <div className="col-md-2"><label className="form-label small">Método</label>
              <select className="form-select form-select-sm" value={f.metodo} onChange={cambiar('metodo')}><option value="">Todos</option>{['POST', 'PUT', 'PATCH', 'DELETE'].map((m) => <option key={m}>{m}</option>)}</select></div>
            <div className="col-md-2"><label className="form-label small">Id usuario</label><input type="number" className="form-control form-control-sm" value={f.id_usuario} onChange={cambiar('id_usuario')} /></div>
            <div className="col-md-2"><label className="form-label small">Desde</label><input type="date" className="form-control form-control-sm" value={f.desde} onChange={cambiar('desde')} /></div>
            <div className="col-md-2"><label className="form-label small">Hasta</label><input type="date" className="form-control form-control-sm" value={f.hasta} onChange={cambiar('hasta')} /></div>
            <div className="col-md-1"><div className="form-check"><input id="ff" type="checkbox" className="form-check-input" checked={f.solo_fallidos} onChange={cambiar('solo_fallidos')} /><label htmlFor="ff" className="form-check-label small">Fallidas</label></div></div>
          </div>
          <ErrorAlerta error={error} onReintentar={recargar} />
          {cargando && !datos ? <Cargando /> : datos?.registros.length === 0 ? <Vacio texto="Sin registros con estos filtros" /> : (
            <>
              <div className="table-responsive">
                <table className="table table-sm table-hover mb-2">
                  <thead><tr><th>Fecha</th><th>Servicio</th><th>Acción</th><th>Recurso</th><th>Usuario</th><th>Código</th><th className="text-end">ms</th></tr></thead>
                  <tbody>
                    {datos?.registros.map((x) => (
                      <tr key={x.id_registro} className={x.exito ? '' : 'table-danger'}>
                        <td className="small text-nowrap">{fecha(x.fecha)}</td>
                        <td className="small"><code>{x.servicio}</code></td>
                        <td><div>{x.accion}</div><div className="small text-muted">{x.metodo} {x.ruta}</div></td>
                        <td>{x.recurso_id || '—'}</td>
                        <td className="small">{x.id_usuario ?? '—'} {x.roles && <span className="text-muted">({x.roles})</span>}</td>
                        <td><span className={`badge text-bg-${x.exito ? 'success' : 'danger'}`}>{x.codigo_estado}</span></td>
                        <td className="text-end small">{x.duracion_ms}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="d-flex justify-content-between align-items-center small">
                <span className="text-muted">{datos?.total} registros</span>
                <div className="btn-group btn-group-sm">
                  <button className="btn btn-outline-secondary" disabled={pagina === 0} onClick={() => setPagina(pagina - 1)}>Anterior</button>
                  <span className="btn btn-outline-secondary disabled">{pagina + 1} / {paginas}</span>
                  <button className="btn btn-outline-secondary" disabled={pagina + 1 >= paginas} onClick={() => setPagina(pagina + 1)}>Siguiente</button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}
