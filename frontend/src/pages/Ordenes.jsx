import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Cargando, Encabezado, ErrorAlerta, EstadoOrden, Prioridad, Vacio, useCarga } from '../components/comunes'
import { useAuth } from '../context/AuthContext'
import { useCatalogos } from '../hooks'
import { api } from '../services/api'
import { ESTADOS_ORDEN, fecha, nombreCliente, nombreEquipo } from '../utils/formato'

export default function Ordenes() {
  const navegar = useNavigate()
  const { tieneRol } = useAuth()
  const soloTecnico = tieneRol('TECNICO') && !tieneRol('ADMINISTRADOR', 'RECEPCIONISTA', 'CAJA')
  const [grupo, setGrupo] = useState(soloTecnico ? 'mias' : 'pendientes')
  const [estado, setEstado] = useState('')
  const [texto, setTexto] = useState('')
  const cat = useCatalogos(!soloTecnico)

  const { datos, cargando, error, recargar } = useCarga(() => (grupo === 'mias'
    ? api('ordenes', '/ordenes/mis-ordenes')
    : api('ordenes', '/ordenes', { query: { grupo: grupo === 'todas' ? '' : grupo, estado } })), [grupo, estado])

  const filtradas = useMemo(() => {
    const t = texto.trim().toLowerCase()
    if (!t || !datos) return datos
    return datos.filter((o) => [o.codigo, nombreCliente(cat.clientes[o.id_cliente]), nombreEquipo(cat.equipos[o.id_equipo]),
      o.asignacion_activa?.nombre_tecnico].join(' ').toLowerCase().includes(t))
  }, [datos, texto, cat])

  const pestañas = [
    ...(tieneRol('TECNICO') ? [['mias', 'Mis órdenes']] : []),
    ['pendientes', 'Pendientes'], ['finalizadas', 'Finalizadas'], ['todas', 'Todas'],
  ]

  return (
    <>
      <Encabezado titulo="Órdenes de trabajo" icono="clipboard-check" subtitulo="Recepción, seguimiento y entrega de equipos">
        {tieneRol('ADMINISTRADOR', 'RECEPCIONISTA') && (
          <Link to="/ordenes/nueva" className="btn btn-primary"><i className="bi bi-clipboard-plus me-1" />Nueva orden</Link>
        )}
      </Encabezado>
      <div className="card shadow-sm border-0">
        <div className="card-header pb-0 border-0">
          <ul className="nav nav-tabs card-header-tabs">
            {pestañas.map(([k, t]) => (
              <li className="nav-item" key={k}>
                <button className={`nav-link ${grupo === k ? 'active' : ''}`} onClick={() => setGrupo(k)}>{t}</button>
              </li>
            ))}
          </ul>
        </div>
        <div className="card-body">
          <div className="row g-2 mb-3">
            <div className="col-md-8">
              <input className="form-control" placeholder="Buscar por código, cliente, equipo o técnico..." value={texto} onChange={(e) => setTexto(e.target.value)} />
            </div>
            {grupo !== 'mias' && (
              <div className="col-md-4">
                <select className="form-select" value={estado} onChange={(e) => setEstado(e.target.value)}>
                  <option value="">Todos los estados</option>
                  {Object.entries(ESTADOS_ORDEN).map(([k, v]) => <option key={k} value={k}>{v.texto}</option>)}
                </select>
              </div>
            )}
          </div>
          <ErrorAlerta error={error} onReintentar={recargar} />
          {cargando ? <Cargando /> : filtradas?.length === 0 ? <Vacio texto="No hay órdenes en esta vista" /> : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead><tr><th>Orden</th><th>Cliente / equipo</th><th>Estado</th><th>Prioridad</th><th>Técnico</th><th>Recibido</th></tr></thead>
                <tbody>
                  {filtradas?.map((o) => (
                    <tr key={o.id_orden} className="clicable" onClick={() => navegar(`/ordenes/${o.id_orden}`)}>
                      <td className="fw-semibold text-primary">{o.codigo}</td>
                      <td>
                        <div>{cat.clientes[o.id_cliente] ? nombreCliente(cat.clientes[o.id_cliente]) : `Cliente #${o.id_cliente}`}</div>
                        <div className="small text-muted">{cat.equipos[o.id_equipo] ? nombreEquipo(cat.equipos[o.id_equipo]) : `Equipo #${o.id_equipo}`}</div>
                      </td>
                      <td><EstadoOrden estado={o.estado_actual} /></td>
                      <td><Prioridad valor={o.prioridad} /></td>
                      <td className="small">{o.asignacion_activa?.nombre_tecnico || <span className="text-warning">Sin asignar</span>}</td>
                      <td className="small text-nowrap">{fecha(o.fecha_recepcion)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
