import { Navigate, Route, Routes } from 'react-router-dom'
import { Cargando } from './components/comunes'
import Layout from './components/Layout'
import { useAuth } from './context/AuthContext'
import Auditoria from './pages/Auditoria'
import ClienteDetalle from './pages/ClienteDetalle'
import Clientes from './pages/Clientes'
import Facturacion from './pages/Facturacion'
import Garantias from './pages/Garantias'
import Inicio from './pages/Inicio'
import Inventario from './pages/Inventario'
import Login from './pages/Login'
import NuevaOrden from './pages/NuevaOrden'
import OrdenDetalle from './pages/OrdenDetalle'
import Ordenes from './pages/Ordenes'
import Usuarios from './pages/Usuarios'

// Protege una pantalla: si el usuario no tiene el rol, vuelve al inicio
function ConRol({ roles, children }) {
  const { tieneRol } = useAuth()
  return tieneRol(...roles) ? children : <Navigate to="/" replace />
}

export default function App() {
  const { usuario, cargando } = useAuth()
  if (cargando) return <Cargando texto="Iniciando..." />
  if (!usuario) return <Login />

  const recepcion = ['ADMINISTRADOR', 'RECEPCIONISTA']
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Inicio />} />
        <Route path="ordenes" element={<ConRol roles={['ADMINISTRADOR', 'RECEPCIONISTA', 'TECNICO', 'CAJA']}><Ordenes /></ConRol>} />
        <Route path="ordenes/nueva" element={<ConRol roles={recepcion}><NuevaOrden /></ConRol>} />
        <Route path="ordenes/:id" element={<OrdenDetalle />} />
        <Route path="clientes" element={<ConRol roles={recepcion}><Clientes /></ConRol>} />
        <Route path="clientes/:id" element={<ConRol roles={recepcion}><ClienteDetalle /></ConRol>} />
        <Route path="inventario" element={<ConRol roles={['ADMINISTRADOR', 'INVENTARIO', 'TECNICO']}><Inventario /></ConRol>} />
        <Route path="facturacion" element={<ConRol roles={['ADMINISTRADOR', 'CAJA']}><Facturacion /></ConRol>} />
        <Route path="garantias" element={<ConRol roles={recepcion}><Garantias /></ConRol>} />
        <Route path="usuarios" element={<ConRol roles={['ADMINISTRADOR']}><Usuarios /></ConRol>} />
        <Route path="auditoria" element={<ConRol roles={['ADMINISTRADOR']}><Auditoria /></ConRol>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
