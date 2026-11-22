import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cargando, Encabezado, ErrorAlerta, Vacio, useCarga } from '../components/comunes'
import { ModalCliente } from '../components/formularios'
import { api } from '../services/api'
import { nombreCliente } from '../utils/formato'

export default function Clientes() {
  const navegar = useNavigate()
  const [buscar, setBuscar] = useState('')
  const [termino, setTermino] = useState('')
  const [nuevo, setNuevo] = useState(false)
  const { datos, cargando, error, recargar } = useCarga(
    () => api('clientes', '/clientes', { query: { buscar: termino, solo_activos: false } }), [termino])

  return (
    <>
      <Encabezado titulo="Clientes y equipos" icono="people" subtitulo="Busque por documento, nombre o teléfono">
        <button className="btn btn-primary" onClick={() => setNuevo(true)}><i className="bi bi-person-plus me-1" />Nuevo cliente</button>
      </Encabezado>
      <div className="card shadow-sm border-0">
        <div className="card-body">
          <form className="input-group mb-3" onSubmit={(e) => { e.preventDefault(); setTermino(buscar) }}>
            <span className="input-group-text"><i className="bi bi-search" /></span>
            <input className="form-control" placeholder="Documento, nombre o teléfono..." value={buscar} onChange={(e) => setBuscar(e.target.value)} />
            <button className="btn btn-outline-primary">Buscar</button>
          </form>
          <ErrorAlerta error={error} onReintentar={recargar} />
          {cargando ? <Cargando /> : datos?.length === 0 ? <Vacio texto="No hay clientes que coincidan" icono="person-x" /> : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead><tr><th>Documento</th><th>Nombre</th><th>Teléfono</th><th>Correo</th><th>Estado</th></tr></thead>
                <tbody>
                  {datos?.map((c) => (
                    <tr key={c.id_cliente} className="clicable" onClick={() => navegar(`/clientes/${c.id_cliente}`)}>
                      <td className="text-nowrap">{c.tipo_documento} {c.numero_documento}</td>
                      <td className="fw-semibold">{nombreCliente(c)}</td>
                      <td>{c.telefono}</td>
                      <td>{c.correo || <span className="text-muted">—</span>}</td>
                      <td><span className={`badge text-bg-${c.estado === 'ACTIVO' ? 'success' : 'secondary'}`}>{c.estado}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      {nuevo && <ModalCliente abierto onCerrar={() => setNuevo(false)} onGuardado={(c) => navegar(`/clientes/${c.id_cliente}`)} />}
    </>
  )
}
