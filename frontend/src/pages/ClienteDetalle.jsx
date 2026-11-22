import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { BotonConfirmar, Cargando, Encabezado, ErrorAlerta, EstadoOrden, Vacio, useCarga } from '../components/comunes'
import { ModalCliente, ModalEquipo } from '../components/formularios'
import Modal from '../components/Modal'
import { useAuth } from '../context/AuthContext'
import { useAvisos } from '../context/AvisosContext'
import { api } from '../services/api'
import { fecha, nombreCliente, TIPOS_EQUIPO } from '../utils/formato'

function HistorialEquipo({ equipo, onCerrar }) {
  const { datos, cargando, error } = useCarga(() => api('ordenes', `/equipos/${equipo.id_equipo}/historial`), [equipo.id_equipo])
  return (
    <Modal titulo={`Historial de servicios · ${equipo.marca} ${equipo.modelo}`} abierto onCerrar={onCerrar} tamano="lg">
      <ErrorAlerta error={error} />
      {cargando ? <Cargando /> : datos?.length === 0 ? <Vacio texto="Este equipo no tiene órdenes" /> : (
        <table className="table table-sm">
          <thead><tr><th>Orden</th><th>Recibido</th><th>Problema</th><th>Estado</th></tr></thead>
          <tbody>
            {datos?.map((o) => (
              <tr key={o.id_orden}>
                <td><Link to={`/ordenes/${o.id_orden}`}>{o.codigo}</Link></td>
                <td className="small">{fecha(o.fecha_recepcion)}</td>
                <td className="small">{o.descripcion_problema}</td>
                <td><EstadoOrden estado={o.estado_actual} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Modal>
  )
}

export default function ClienteDetalle() {
  const { id } = useParams()
  const { tieneRol } = useAuth()
  const aviso = useAvisos()
  const [editar, setEditar] = useState(false)
  const [nuevoEquipo, setNuevoEquipo] = useState(false)
  const [historial, setHistorial] = useState(null)
  const { datos: c, cargando, error, recargar } = useCarga(() => api('clientes', `/clientes/${id}`), [id])

  if (cargando && !c) return <Cargando />
  if (error) return <ErrorAlerta error={error} onReintentar={recargar} />

  const cambiarEstado = async (accion) => {
    try {
      await api('clientes', `/clientes/${id}/${accion}`, { method: 'PATCH' })
      aviso.ok(accion === 'activar' ? 'Cliente reactivado' : 'Cliente desactivado')
      recargar()
    } catch (e) { aviso.error(e.message) }
  }

  return (
    <>
      <Encabezado titulo={nombreCliente(c)} icono="person-vcard" subtitulo={`${c.tipo_documento} ${c.numero_documento} · Cliente desde ${fecha(c.fecha_registro)}`}>
        <Link to="/clientes" className="btn btn-light"><i className="bi bi-arrow-left me-1" />Volver</Link>
        <button className="btn btn-outline-primary" onClick={() => setEditar(true)}><i className="bi bi-pencil me-1" />Editar</button>
        {tieneRol('ADMINISTRADOR') && (c.estado === 'ACTIVO'
          ? <BotonConfirmar className="btn btn-outline-danger" onConfirmar={() => cambiarEstado('desactivar')}>Desactivar</BotonConfirmar>
          : <button className="btn btn-outline-success" onClick={() => cambiarEstado('activar')}>Reactivar</button>)}
      </Encabezado>

      <div className="row g-3">
        <div className="col-lg-4">
          <div className="card shadow-sm border-0">
            <div className="card-header">Datos de contacto</div>
            <div className="card-body">
              <dl className="mb-0">
                <dt className="small text-muted">Teléfono</dt><dd>{c.telefono}</dd>
                <dt className="small text-muted">Correo</dt><dd>{c.correo || '—'}</dd>
                <dt className="small text-muted">Dirección</dt><dd>{c.direccion || '—'}</dd>
                <dt className="small text-muted">Estado</dt>
                <dd className="mb-0"><span className={`badge text-bg-${c.estado === 'ACTIVO' ? 'success' : 'secondary'}`}>{c.estado}</span></dd>
              </dl>
            </div>
          </div>
        </div>
        <div className="col-lg-8">
          <div className="card shadow-sm border-0">
            <div className="card-header d-flex justify-content-between align-items-center">
              <span>Equipos ({c.equipos.length})</span>
              {c.estado === 'ACTIVO' && <button className="btn btn-sm btn-primary" onClick={() => setNuevoEquipo(true)}><i className="bi bi-plus-lg me-1" />Registrar equipo</button>}
            </div>
            <div className="card-body">
              {c.equipos.length === 0 ? <Vacio texto="El cliente no tiene equipos registrados" icono="laptop" /> : (
                <div className="table-responsive">
                  <table className="table mb-0">
                    <thead><tr><th>Equipo</th><th>Serie</th><th>Descripción</th><th /></tr></thead>
                    <tbody>
                      {c.equipos.map((e) => (
                        <tr key={e.id_equipo}>
                          <td><div className="fw-semibold">{e.marca} {e.modelo}</div><div className="small text-muted">{TIPOS_EQUIPO[e.tipo_equipo]}</div></td>
                          <td><code>{e.numero_serie}</code></td>
                          <td className="small">{e.descripcion || '—'}</td>
                          <td className="text-end text-nowrap">
                            <button className="btn btn-sm btn-outline-secondary me-1" onClick={() => setHistorial(e)} title="Historial">
                              <i className="bi bi-clock-history" />
                            </button>
                            <Link className="btn btn-sm btn-primary" to={`/ordenes/nueva?equipo=${e.id_equipo}`}>
                              <i className="bi bi-clipboard-plus me-1" />Nueva orden
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      {editar && <ModalCliente abierto cliente={c} onCerrar={() => setEditar(false)} onGuardado={recargar} />}
      {nuevoEquipo && <ModalEquipo abierto idCliente={id} onCerrar={() => setNuevoEquipo(false)} onGuardado={recargar} />}
      {historial && <HistorialEquipo equipo={historial} onCerrar={() => setHistorial(null)} />}
    </>
  )
}
