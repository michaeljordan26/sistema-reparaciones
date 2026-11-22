// Sesión del usuario: token JWT, datos y roles. El token se guarda en localStorage
// para no tener que iniciar sesión cada vez que se recarga la página.
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, onSesionExpirada, setToken } from '../services/api'

const AuthContext = createContext(null)
const CLAVE = 'taller.token'

function leer() {
  try { return localStorage.getItem(CLAVE) } catch { return null }
}
function guardar(valor) {
  try { valor ? localStorage.setItem(CLAVE, valor) : localStorage.removeItem(CLAVE) } catch { /* sin almacenamiento */ }
}

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [expirada, setExpirada] = useState(false)

  const cerrarSesion = useCallback(() => {
    setToken(null)
    guardar(null)
    setUsuario(null)
  }, [])

  const cargarUsuario = useCallback(async () => {
    const [yo, validado] = await Promise.all([api('usuarios', '/auth/me'), api('usuarios', '/auth/validar')])
    setUsuario({ ...yo, roles: yo.roles.map((r) => r.nombre), id_tecnico: validado.id_tecnico })
  }, [])

  useEffect(() => {
    onSesionExpirada(() => { setExpirada(true); cerrarSesion() })
    const t = leer()
    if (!t) { setCargando(false); return }
    setToken(t)
    cargarUsuario().catch(cerrarSesion).finally(() => setCargando(false))
  }, [cargarUsuario, cerrarSesion])

  const iniciarSesion = async (nombreUsuario, contrasena) => {
    const r = await api('usuarios', '/auth/login', { method: 'POST', form: { username: nombreUsuario, password: contrasena } })
    setToken(r.access_token)
    guardar(r.access_token)
    setExpirada(false)
    await cargarUsuario()
  }

  const tieneRol = useCallback((...roles) => !!usuario && roles.some((r) => usuario.roles.includes(r)), [usuario])

  return (
    <AuthContext.Provider value={{ usuario, cargando, expirada, iniciarSesion, cerrarSesion, tieneRol }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
