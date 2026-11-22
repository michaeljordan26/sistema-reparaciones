import { useState } from 'react'
import { BotonEnviar } from '../components/comunes'
import { useAuth } from '../context/AuthContext'

const DEMO = [
  ['admin', 'Admin123*', 'Administrador'],
  ['recepcion', 'Recepcion123*', 'Recepción'],
  ['tecnico1', 'Tecnico123*', 'Técnico'],
  ['caja', 'Caja1234*', 'Caja'],
  ['inventario', 'Inventario123*', 'Inventario'],
]

export default function Login() {
  const { iniciarSesion, expirada } = useAuth()
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const entrar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      await iniciarSesion(usuario.trim(), clave)
    } catch (err) {
      setError(err.status === 401 ? 'Usuario o contraseña incorrectos' : err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login-fondo">
      <div className="card login-tarjeta shadow-lg border-0">
        <div className="card-body p-4 p-md-5">
          <div className="text-center mb-4">
            <i className="bi bi-pc-display-horizontal display-5 text-primary" />
            <h1 className="h4 mt-2 mb-0">Taller de Reparaciones</h1>
            <div className="text-muted small">Gestión de mantenimiento de equipos de cómputo</div>
          </div>
          {expirada && <div className="alert alert-warning py-2 small">Su sesión expiró. Ingrese de nuevo.</div>}
          {error && <div className="alert alert-danger py-2 small">{error}</div>}
          <form onSubmit={entrar}>
            <div className="mb-3">
              <label className="form-label" htmlFor="usuario">Usuario o correo</label>
              <input id="usuario" className="form-control" value={usuario} onChange={(e) => setUsuario(e.target.value)}
                autoComplete="username" autoFocus required />
            </div>
            <div className="mb-4">
              <label className="form-label" htmlFor="clave">Contraseña</label>
              <input id="clave" type="password" className="form-control" value={clave}
                onChange={(e) => setClave(e.target.value)} autoComplete="current-password" required />
            </div>
            <BotonEnviar enviando={enviando} className="btn btn-primary w-100">Ingresar</BotonEnviar>
          </form>
          <details className="mt-4 small">
            <summary className="text-muted">Usuarios de demostración</summary>
            <div className="d-flex flex-wrap gap-1 mt-2">
              {DEMO.map(([u, c, t]) => (
                <button key={u} type="button" className="btn btn-sm btn-outline-secondary"
                  onClick={() => { setUsuario(u); setClave(c) }}>{t}</button>
              ))}
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}
