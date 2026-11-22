import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Cargando, Encabezado, ErrorAlerta, Insignia, Vacio, useCarga } from '../components/comunes'
import Modal from '../components/Modal'
import { useAuth } from '../context/AuthContext'
import { useAvisos } from '../context/AvisosContext'
import { useCatalogos } from '../hooks'
import { api } from '../services/api'
import { dia, fecha, nombreCliente } from '../utils/formato'

const COLOR = { VIGENTE: 'success', VENCIDA: 'secondary', ANULADA: 'danger' }
const COLOR_REC = { ABIERTA: 'warning', APROBADA: 'success', RECHAZADA: 'danger' }

function DetalleGarantia({ g, onCerrar, onCambio }) {
  const { tieneRol } = useAuth()
  const aviso = useAvisos()
  const [descripcion, setDescripcion] = useState('')
  const [respuesta, setRespuesta] = useState('')
  const [motivo, setMotivo] = useState('')
  const abierta = g.reclamaciones.find((r) => r.estado === 'ABIERTA')

  const hacer = async (fn, ok) => {
    try { await fn(); aviso.ok(ok); onCambio() } catch (e) { aviso.error(e.message) }
  }
  return (
    <Modal titulo={`Garantía #${g.id_garantia}`} abierto onCerrar={onCerrar} tamano="lg">
      <div className="row g-2 mb-3">
        <div className="col-md-4"><div className="seccion-titulo">Estado</div><Insignia texto={g.estado} color={COLOR[g.estado]} /></div>
        <div className="col-md-4"><div className="seccion-titulo">Vigencia</div>{dia(g.fecha_inicio)} → {dia(g.fecha_fin)}</div>
        <div className="col-md-4"><div className="seccion-titulo">Orden</div><Link to={`/ordenes/${g.id_orden}`} onClick={onCerrar}>Orden #{g.id_orden}</Link></div>
        <div className="col-12"><div className="seccion-titulo">Cobertura</div>{g.cobertura}</div>
        <div className="col-12 small text-muted">{g.condiciones}</div>
        {g.motivo_anulacion && <div className="col-12 text-danger small">Anulada: {g.motivo_anulacion}</div>}
      </div>
      <div className="seccion-titulo mb-2">Reclamaciones</div>
      {g.reclamaciones.length === 0 && <div className="text-muted small mb-3">Sin reclamaciones</div>}
      {g.reclamaciones.map((r) => (
        <div key={r.id_reclamacion} className="border rounded p-2 mb-2">
          <div className="d-flex justify-content-between"><span className="small text-muted">{fecha(r.fecha)}</span><Insignia texto={r.estado} color={COLOR_REC[r.estado]} /></div>
          <div>{r.descripcion}</div>
          {r.respuesta && <div className="small mt-1"><i className="bi bi-reply me-1" />{r.respuesta}</div>}
          {r.estado === 'ABIERTA' && tieneRol('ADMINISTRADOR') && (
            <div className="input-group input-group-sm mt-2">
              <input className="form-control" placeholder="Respuesta al cliente" value={respuesta} onChange={(e) => setRespuesta(e.target.value)} />
              <button className="btn btn-success" disabled={respuesta.length < 5} onClick={() => hacer(() => api('reparaciones', `/reclamaciones/${r.id_reclamacion}`, { method: 'PATCH', body: { estado: 'APROBADA', respuesta } }), 'Reclamación aprobada')}>Aprobar</button>
              <button className="btn btn-outline-danger" disabled={respuesta.length < 5} onClick={() => hacer(() => api('reparaciones', `/reclamaciones/${r.id_reclamacion}`, { method: 'PATCH', body: { estado: 'RECHAZADA', respuesta } }), 'Reclamación rechazada')}>Rechazar</button>
            </div>
          )}
        </div>
      ))}
      {g.estado === 'VIGENTE' && !abierta && (
        <div className="input-group mt-3">
          <input className="form-control" placeholder="¿Qué reporta el cliente?" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
          <button className="btn btn-primary" disabled={descripcion.length < 10}
            onClick={() => hacer(() => api('reparaciones', `/garantias/${g.id_garantia}/reclamaciones`, { method: 'POST', body: { descripcion } }), 'Reclamación registrada')}>Registrar reclamación</button>
        </div>
      )}
      {g.estado === 'VIGENTE' && tieneRol('ADMINISTRADOR') && (
        <div className="input-group input-group-sm mt-3">
          <input className="form-control" placeholder="Motivo de anulación" value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          <button className="btn btn-outline-danger" disabled={motivo.length < 5}
            onClick={() => hacer(() => api('reparaciones', `/garantias/${g.id_garantia}/anular`, { method: 'PATCH', body: { motivo } }), 'Garantía anulada')}>Anular garantía</button>
        </div>
      )}
    </Modal>
  )
}

export default function Garantias() {
  const [estado, setEstado] = useState('VIGENTE')
  const [abierta, setAbierta] = useState(null)
  const cat = useCatalogos()
  const { datos, cargando, error, recargar } = useCarga(() => api('reparaciones', '/garantias', { query: { estado } }), [estado])
  const seleccionada = datos?.find((g) => g.id_garantia === abierta)

  return (
    <>
      <Encabezado titulo="Garantías" icono="shield-check" subtitulo="Se crean solas al finalizar una reparación" />
      <div className="card shadow-sm border-0">
        <div className="card-body">
          <div className="btn-group mb-3">
            {[['VIGENTE', 'Vigentes'], ['VENCIDA', 'Vencidas'], ['ANULADA', 'Anuladas'], ['', 'Todas']].map(([k, t]) => (
              <button key={k} className={`btn btn-sm ${estado === k ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setEstado(k)}>{t}</button>
            ))}
          </div>
          <ErrorAlerta error={error} onReintentar={recargar} />
          {cargando && !datos ? <Cargando /> : datos?.length === 0 ? <Vacio texto="No hay garantías en esta vista" icono="shield" /> : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead><tr><th>#</th><th>Cliente</th><th>Orden</th><th>Vence</th><th>Estado</th><th>Reclamaciones</th></tr></thead>
                <tbody>
                  {datos?.map((g) => (
                    <tr key={g.id_garantia} className="clicable" onClick={() => setAbierta(g.id_garantia)}>
                      <td>{g.id_garantia}</td>
                      <td>{cat.clientes[g.id_cliente] ? nombreCliente(cat.clientes[g.id_cliente]) : `Cliente #${g.id_cliente}`}</td>
                      <td>Orden #{g.id_orden}</td>
                      <td>{dia(g.fecha_fin)}</td>
                      <td><Insignia texto={g.estado} color={COLOR[g.estado]} /></td>
                      <td>{g.reclamaciones.length > 0 ? g.reclamaciones.map((r) => <Insignia key={r.id_reclamacion} texto={r.estado} color={COLOR_REC[r.estado]} />) : <span className="text-muted">—</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      {seleccionada && <DetalleGarantia g={seleccionada} onCerrar={() => setAbierta(null)} onCambio={recargar} />}
    </>
  )
}
