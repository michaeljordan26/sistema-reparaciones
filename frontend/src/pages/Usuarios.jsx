import { useState } from 'react'
import { BotonConfirmar, BotonEnviar, Cargando, Encabezado, ErrorAlerta, useCarga, useFormulario } from '../components/comunes'
import Modal from '../components/Modal'
import { ROLES } from '../config'
import { useAuth } from '../context/AuthContext'
import { useAvisos } from '../context/AvisosContext'
import { api } from '../services/api'

function Roles({ seleccion, onCambio }) {
  return (
    <div className="d-flex flex-wrap gap-3">
      {ROLES.map((r) => (
        <div className="form-check" key={r}>
          <input id={`rol-${r}`} type="checkbox" className="form-check-input" checked={seleccion.includes(r)}
            onChange={(e) => onCambio(e.target.checked ? [...seleccion, r] : seleccion.filter((x) => x !== r))} />
          <label htmlFor={`rol-${r}`} className="form-check-label small">{r}</label>
        </div>
      ))}
    </div>
  )
}

function ModalUsuario({ onCerrar, onGuardado }) {
  const aviso = useAvisos()
  const [v, cambiar] = useFormulario({ nombres: '', apellidos: '', correo: '', nombre_usuario: '', contrasena: '' })
  const [roles, setRoles] = useState(['RECEPCIONISTA'])
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const guardar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    try {
      await api('usuarios', '/usuarios', { method: 'POST', body: { ...v, roles } })
      aviso.ok('Usuario creado')
      onGuardado()
      onCerrar()
    } catch (err) { setError(err.message); setEnviando(false) }
  }
  return (
    <Modal titulo="Nuevo usuario" abierto onCerrar={onCerrar}>
      <form onSubmit={guardar}>
        {error && <div className="alert alert-danger py-2 small">{error}</div>}
        <div className="row g-2">
          <div className="col-6"><label className="form-label small">Nombres</label><input className="form-control" value={v.nombres} onChange={cambiar('nombres')} required /></div>
          <div className="col-6"><label className="form-label small">Apellidos</label><input className="form-control" value={v.apellidos} onChange={cambiar('apellidos')} required /></div>
          <div className="col-12"><label className="form-label small">Correo</label><input type="email" className="form-control" value={v.correo} onChange={cambiar('correo')} required /></div>
          <div className="col-6"><label className="form-label small">Usuario</label><input className="form-control" value={v.nombre_usuario} onChange={cambiar('nombre_usuario')} required pattern="[a-zA-Z0-9_.]{3,}" /></div>
          <div className="col-6"><label className="form-label small">Contraseña (mín. 8)</label><input type="password" className="form-control" value={v.contrasena} onChange={cambiar('contrasena')} required minLength={8} /></div>
          <div className="col-12"><label className="form-label small">Roles</label><Roles seleccion={roles} onCambio={setRoles} /></div>
        </div>
        <div className="text-end mt-3"><BotonEnviar enviando={enviando} disabled={roles.length === 0 || enviando}>Crear usuario</BotonEnviar></div>
      </form>
    </Modal>
  )
}

function ModalRoles({ usuario, onCerrar, onGuardado }) {
  const aviso = useAvisos()
  const [roles, setRoles] = useState(usuario.roles.map((r) => r.nombre))
  const guardar = async () => {
    try {
      await api('usuarios', `/usuarios/${usuario.id_usuario}/roles`, { method: 'PUT', body: { roles } })
      aviso.ok('Roles actualizados')
      onGuardado()
      onCerrar()
    } catch (e) { aviso.error(e.message) }
  }
  return (
    <Modal titulo={`Roles de ${usuario.nombre_usuario}`} abierto onCerrar={onCerrar}
      pie={<button className="btn btn-primary" disabled={roles.length === 0} onClick={guardar}>Guardar</button>}>
      <Roles seleccion={roles} onCambio={setRoles} />
    </Modal>
  )
}

export default function Usuarios() {
  const { usuario: yo } = useAuth()
  const aviso = useAvisos()
  const [modal, setModal] = useState(null)
  const [especialidad, setEspecialidad] = useState({})
  const u = useCarga(() => api('usuarios', '/usuarios'))
  const t = useCarga(() => api('usuarios', '/tecnicos'))
  const recargar = () => { u.recargar(); t.recargar() }
  const hacer = async (fn, ok) => { try { await fn(); aviso.ok(ok); recargar() } catch (e) { aviso.error(e.message) } }

  const conPerfil = new Set((t.datos || []).map((x) => x.id_usuario))
  const sinPerfil = (u.datos || []).filter((x) => x.roles.some((r) => r.nombre === 'TECNICO') && !conPerfil.has(x.id_usuario))

  return (
    <>
      <Encabezado titulo="Usuarios y técnicos" icono="person-gear">
        <button className="btn btn-primary" onClick={() => setModal({ tipo: 'nuevo' })}><i className="bi bi-person-plus me-1" />Nuevo usuario</button>
      </Encabezado>
      <div className="card shadow-sm border-0 mb-3">
        <div className="card-header">Usuarios</div>
        <div className="card-body">
          <ErrorAlerta error={u.error} />
          {u.cargando && !u.datos ? <Cargando /> : (
            <div className="table-responsive">
              <table className="table mb-0">
                <thead><tr><th>Usuario</th><th>Nombre</th><th>Correo</th><th>Roles</th><th>Estado</th><th /></tr></thead>
                <tbody>
                  {u.datos?.map((x) => (
                    <tr key={x.id_usuario} className={x.activo ? '' : 'text-muted'}>
                      <td><code>{x.nombre_usuario}</code></td>
                      <td>{x.nombres} {x.apellidos}</td>
                      <td className="small">{x.correo}</td>
                      <td>{x.roles.map((r) => <span key={r.id_rol} className="badge text-bg-light border me-1">{r.nombre}</span>)}</td>
                      <td><span className={`badge text-bg-${x.activo ? 'success' : 'secondary'}`}>{x.activo ? 'Activo' : 'Inactivo'}</span></td>
                      <td className="text-end text-nowrap">
                        <button className="btn btn-sm btn-outline-primary me-1" onClick={() => setModal({ tipo: 'roles', usuario: x })}>Roles</button>
                        {x.id_usuario !== yo.id_usuario && (x.activo
                          ? <BotonConfirmar onConfirmar={() => hacer(() => api('usuarios', `/usuarios/${x.id_usuario}/desactivar`, { method: 'PATCH' }), 'Usuario desactivado')}>Desactivar</BotonConfirmar>
                          : <button className="btn btn-sm btn-outline-success" onClick={() => hacer(() => api('usuarios', `/usuarios/${x.id_usuario}`, { method: 'PUT', body: { activo: true } }), 'Usuario reactivado')}>Reactivar</button>)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card shadow-sm border-0">
        <div className="card-header">Perfiles de técnico</div>
        <div className="card-body">
          {sinPerfil.length > 0 && (
            <div className="alert alert-info py-2">
              <div className="small fw-semibold mb-1">Usuarios con rol TÉCNICO sin perfil:</div>
              {sinPerfil.map((x) => (
                <div key={x.id_usuario} className="input-group input-group-sm mb-1" style={{ maxWidth: 520 }}>
                  <span className="input-group-text">{x.nombre_usuario}</span>
                  <input className="form-control" placeholder="Especialidad" value={especialidad[x.id_usuario] || ''} onChange={(e) => setEspecialidad({ ...especialidad, [x.id_usuario]: e.target.value })} />
                  <button className="btn btn-primary" disabled={(especialidad[x.id_usuario] || '').length < 3}
                    onClick={() => hacer(() => api('usuarios', '/tecnicos', { method: 'POST', body: { id_usuario: x.id_usuario, especialidad: especialidad[x.id_usuario] } }), 'Perfil de técnico creado')}>Crear perfil</button>
                </div>
              ))}
            </div>
          )}
          <ErrorAlerta error={t.error} />
          <table className="table mb-0">
            <thead><tr><th>Técnico</th><th>Especialidad</th><th>Estado laboral</th></tr></thead>
            <tbody>
              {t.datos?.map((x) => (
                <tr key={x.id_tecnico}>
                  <td>{x.usuario.nombres} {x.usuario.apellidos}</td>
                  <td>{x.especialidad}</td>
                  <td style={{ maxWidth: 200 }}>
                    <select className="form-select form-select-sm" value={x.estado_laboral}
                      onChange={(e) => hacer(() => api('usuarios', `/tecnicos/${x.id_tecnico}`, { method: 'PUT', body: { estado_laboral: e.target.value } }), 'Estado actualizado')}>
                      {['ACTIVO', 'VACACIONES', 'INACTIVO'].map((s) => <option key={s}>{s}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {modal?.tipo === 'nuevo' && <ModalUsuario onCerrar={() => setModal(null)} onGuardado={recargar} />}
      {modal?.tipo === 'roles' && <ModalRoles usuario={modal.usuario} onCerrar={() => setModal(null)} onGuardado={recargar} />}
    </>
  )
}
