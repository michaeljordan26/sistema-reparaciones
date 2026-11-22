// Estructura general: menú lateral (según el rol) + barra superior + contenido.
import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Cada opción del menú dice qué roles la ven
export const MENU = [
  { ruta: '/', texto: 'Inicio', icono: 'speedometer2', roles: null },
  { ruta: '/ordenes', texto: 'Órdenes', icono: 'clipboard-check', roles: ['ADMINISTRADOR', 'RECEPCIONISTA', 'TECNICO', 'CAJA'] },
  { ruta: '/clientes', texto: 'Clientes y equipos', icono: 'people', roles: ['ADMINISTRADOR', 'RECEPCIONISTA'] },
  { ruta: '/inventario', texto: 'Inventario', icono: 'box-seam', roles: ['ADMINISTRADOR', 'INVENTARIO', 'TECNICO'] },
  { ruta: '/facturacion', texto: 'Facturación', icono: 'cash-coin', roles: ['ADMINISTRADOR', 'CAJA'] },
  { ruta: '/garantias', texto: 'Garantías', icono: 'shield-check', roles: ['ADMINISTRADOR', 'RECEPCIONISTA'] },
  { ruta: '/usuarios', texto: 'Usuarios y técnicos', icono: 'person-gear', roles: ['ADMINISTRADOR'] },
  { ruta: '/auditoria', texto: 'Auditoría', icono: 'journal-text', roles: ['ADMINISTRADOR'] },
]

const COLOR_ROL = { ADMINISTRADOR: 'danger', RECEPCIONISTA: 'primary', TECNICO: 'success', CAJA: 'warning', INVENTARIO: 'info' }

export default function Layout() {
  const { usuario, cerrarSesion, tieneRol } = useAuth()
  const [abierto, setAbierto] = useState(false)
  const ubicacion = useLocation()
  const opciones = MENU.filter((m) => !m.roles || tieneRol(...m.roles))

  return (
    <div className="app">
      <aside className={`menu-lateral ${abierto ? 'abierto' : ''}`}>
        <div className="marca">
          <i className="bi bi-pc-display-horizontal me-2" />
          <div>
            <div className="fw-semibold">Taller de Reparaciones</div>
            <div className="small opacity-75">Gestión de equipos</div>
          </div>
        </div>
        <nav className="nav flex-column mt-2">
          {opciones.map((m) => (
            <NavLink key={m.ruta} to={m.ruta} end={m.ruta === '/'} onClick={() => setAbierto(false)}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <i className={`bi bi-${m.icono} me-2`} />{m.texto}
            </NavLink>
          ))}
        </nav>
      </aside>
      {abierto && <div className="velo d-lg-none" onClick={() => setAbierto(false)} />}

      <div className="contenido">
        <header className="barra-superior">
          <button className="btn btn-light d-lg-none" onClick={() => setAbierto(!abierto)} aria-label="Menú">
            <i className="bi bi-list" />
          </button>
          <div className="ms-auto d-flex align-items-center gap-3">
            <div className="text-end d-none d-sm-block">
              <div className="fw-semibold small">{usuario.nombres} {usuario.apellidos}</div>
              <div>{usuario.roles.map((r) => <span key={r} className={`badge text-bg-${COLOR_ROL[r] || 'secondary'} ms-1`}>{r}</span>)}</div>
            </div>
            <button className="btn btn-outline-secondary btn-sm" onClick={cerrarSesion} title="Cerrar sesión">
              <i className="bi bi-box-arrow-right me-1" />Salir
            </button>
          </div>
        </header>
        <main className="p-3 p-md-4" key={ubicacion.pathname}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
