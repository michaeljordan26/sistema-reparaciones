// Recepción de un equipo: 1) buscar cliente, 2) elegir equipo, 3) describir el problema.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { BotonEnviar, Encabezado, useFormulario } from '../components/comunes'
import { ModalCliente, ModalEquipo } from '../components/formularios'
import { useAvisos } from '../context/AvisosContext'
import { api } from '../services/api'
import { nombreCliente, TIPOS_EQUIPO } from '../utils/formato'

export default function NuevaOrden() {
  const navegar = useNavigate()
  const aviso = useAvisos()
  const [params] = useSearchParams()
  const [buscar, setBuscar] = useState('')
  const [resultados, setResultados] = useState(null)
  const [cliente, setCliente] = useState(null)
  const [idEquipo, setIdEquipo] = useState(null)
  const [modalCliente, setModalCliente] = useState(false)
  const [modalEquipo, setModalEquipo] = useState(false)
  const [v, cambiar] = useFormulario({ descripcion_problema: '', accesorios_recibidos: '', prioridad: 'MEDIA' })
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)

  const cargarCliente = async (id, equipo = null) => {
    const c = await api('clientes', `/clientes/${id}`)
    setCliente(c)
    setIdEquipo(equipo ?? (c.equipos.length === 1 ? c.equipos[0].id_equipo : null))
  }

  // Si se llega desde "Nueva orden" de un equipo, se precarga
  useEffect(() => {
    const e = params.get('equipo')
    if (e) api('clientes', `/equipos/${e}`).then((eq) => cargarCliente(eq.id_cliente, eq.id_equipo)).catch((err) => setError(err.message))
  }, [params])

  const buscarClientes = async (e) => {
    e.preventDefault()
    try {
      setResultados(await api('clientes', '/clientes', { query: { buscar } }))
    } catch (err) { setError(err.message) }
  }

  const crear = async (e) => {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      const o = await api('ordenes', '/ordenes', {
        method: 'POST', body: { ...v, id_equipo: idEquipo, accesorios_recibidos: v.accesorios_recibidos || null },
      })
      aviso.ok(`Orden ${o.codigo} creada`)
      navegar(`/ordenes/${o.id_orden}`)
    } catch (err) {
      setError(err.message)
      setEnviando(false)
    }
  }

  return (
    <>
      <Encabezado titulo="Nueva orden de trabajo" icono="clipboard-plus" subtitulo="Recepción de un equipo en el taller">
        <Link to="/ordenes" className="btn btn-light"><i className="bi bi-arrow-left me-1" />Volver</Link>
      </Encabezado>
      {error && <div className="alert alert-danger">{error}</div>}
      <div className="row g-3">
        <div className="col-lg-5">
          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header"><span className="badge text-bg-primary me-2">1</span>Cliente</div>
            <div className="card-body">
              {cliente ? (
                <div className="d-flex justify-content-between align-items-start">
                  <div>
                    <div className="fw-semibold">{nombreCliente(cliente)}</div>
                    <div className="small text-muted">{cliente.tipo_documento} {cliente.numero_documento} · {cliente.telefono}</div>
                  </div>
                  <button className="btn btn-sm btn-light" onClick={() => { setCliente(null); setIdEquipo(null) }}>Cambiar</button>
                </div>
              ) : (
                <>
                  <form className="input-group mb-2" onSubmit={buscarClientes}>
                    <input className="form-control" placeholder="Documento, nombre o teléfono" value={buscar} onChange={(e) => setBuscar(e.target.value)} required />
                    <button className="btn btn-outline-primary"><i className="bi bi-search" /></button>
                  </form>
                  {resultados && (
                    <div className="list-group mb-2">
                      {resultados.length === 0 && <div className="list-group-item text-muted small">Sin resultados</div>}
                      {resultados.map((c) => (
                        <button key={c.id_cliente} className="list-group-item list-group-item-action" onClick={() => cargarCliente(c.id_cliente)}>
                          <div className="fw-semibold">{nombreCliente(c)}</div>
                          <div className="small text-muted">{c.tipo_documento} {c.numero_documento}</div>
                        </button>
                      ))}
                    </div>
                  )}
                  <button className="btn btn-sm btn-link px-0" onClick={() => setModalCliente(true)}><i className="bi bi-person-plus me-1" />Registrar cliente nuevo</button>
                </>
              )}
            </div>
          </div>
          {cliente && (
            <div className="card shadow-sm border-0">
              <div className="card-header d-flex justify-content-between align-items-center">
                <span><span className="badge text-bg-primary me-2">2</span>Equipo</span>
                <button className="btn btn-sm btn-outline-primary" onClick={() => setModalEquipo(true)}><i className="bi bi-plus-lg" /> Equipo</button>
              </div>
              <div className="list-group list-group-flush">
                {cliente.equipos.length === 0 && <div className="list-group-item text-muted small">El cliente no tiene equipos. Regístrelo primero.</div>}
                {cliente.equipos.map((e) => (
                  <label key={e.id_equipo} className={`list-group-item d-flex gap-2 ${idEquipo === e.id_equipo ? 'active' : ''}`}>
                    <input type="radio" className="form-check-input mt-1" checked={idEquipo === e.id_equipo} onChange={() => setIdEquipo(e.id_equipo)} />
                    <div>
                      <div className="fw-semibold">{e.marca} {e.modelo}</div>
                      <div className="small opacity-75">{TIPOS_EQUIPO[e.tipo_equipo]} · Serie {e.numero_serie}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="col-lg-7">
          <div className="card shadow-sm border-0">
            <div className="card-header"><span className="badge text-bg-primary me-2">3</span>Problema reportado</div>
            <div className="card-body">
              <form onSubmit={crear}>
                <div className="mb-3">
                  <label className="form-label">¿Qué le pasa al equipo?</label>
                  <textarea className="form-control" rows="4" value={v.descripcion_problema} onChange={cambiar('descripcion_problema')}
                    placeholder="Ej.: no enciende, pantalla con líneas, se apaga solo..." required minLength={5} />
                </div>
                <div className="row g-2 mb-3">
                  <div className="col-md-8">
                    <label className="form-label">Accesorios recibidos</label>
                    <input className="form-control" value={v.accesorios_recibidos} onChange={cambiar('accesorios_recibidos')} placeholder="Cargador, estuche..." />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Prioridad</label>
                    <select className="form-select" value={v.prioridad} onChange={cambiar('prioridad')}>
                      {['BAJA', 'MEDIA', 'ALTA', 'URGENTE'].map((p) => <option key={p}>{p}</option>)}
                    </select>
                  </div>
                </div>
                <BotonEnviar enviando={enviando} disabled={!idEquipo || enviando}>
                  <i className="bi bi-check2 me-1" />Crear orden
                </BotonEnviar>
                {!idEquipo && <span className="small text-muted ms-2">Seleccione el cliente y el equipo</span>}
              </form>
            </div>
          </div>
        </div>
      </div>
      {modalCliente && <ModalCliente abierto onCerrar={() => setModalCliente(false)} onGuardado={(c) => cargarCliente(c.id_cliente)} />}
      {modalEquipo && <ModalEquipo abierto idCliente={cliente.id_cliente} onCerrar={() => setModalEquipo(false)}
        onGuardado={(e) => cargarCliente(cliente.id_cliente, e.id_equipo)} />}
    </>
  )
}
