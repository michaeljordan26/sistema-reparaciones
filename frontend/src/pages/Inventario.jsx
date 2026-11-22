import { useState } from 'react'
import { BotonEnviar, Cargando, Encabezado, ErrorAlerta, Vacio, useCarga, useFormulario } from '../components/comunes'
import Modal from '../components/Modal'
import { useAuth } from '../context/AuthContext'
import { useAvisos } from '../context/AvisosContext'
import { api } from '../services/api'
import { dinero, fecha } from '../utils/formato'

const TIPOS_MOV = {
  ENTRADA: ['Entrada', 'success'], SALIDA: ['Salida', 'danger'], DEVOLUCION: ['Devolución', 'info'],
  AJUSTE_POSITIVO: ['Ajuste +', 'secondary'], AJUSTE_NEGATIVO: ['Ajuste −', 'warning'],
}

function ModalRepuesto({ repuesto, onCerrar, onGuardado }) {
  const aviso = useAvisos()
  const editar = !!repuesto
  const [v, cambiar] = useFormulario({
    codigo: repuesto?.codigo || '', nombre: repuesto?.nombre || '', categoria: repuesto?.categoria || '', marca: repuesto?.marca || '',
    precio_costo: repuesto?.precio_costo ?? '', precio_venta: repuesto?.precio_venta ?? '', stock_minimo: repuesto?.stock_minimo ?? 1, stock_inicial: 0,
  })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const guardar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    const base = { nombre: v.nombre, categoria: v.categoria, marca: v.marca || null, precio_costo: Number(v.precio_costo),
      precio_venta: Number(v.precio_venta), stock_minimo: Number(v.stock_minimo) }
    try {
      if (editar) await api('inventario', `/repuestos/${repuesto.id_repuesto}`, { method: 'PUT', body: base })
      else await api('inventario', '/repuestos', { method: 'POST', body: { ...base, codigo: v.codigo, stock_inicial: Number(v.stock_inicial) } })
      aviso.ok(editar ? 'Repuesto actualizado' : 'Repuesto registrado')
      onGuardado()
      onCerrar()
    } catch (err) { setError(err.message); setEnviando(false) }
  }
  return (
    <Modal titulo={editar ? `Editar ${repuesto.codigo}` : 'Nuevo repuesto'} abierto onCerrar={onCerrar}>
      <form onSubmit={guardar}>
        {error && <div className="alert alert-danger py-2 small">{error}</div>}
        <div className="row g-2">
          {!editar && <div className="col-6"><label className="form-label small">Código</label><input className="form-control" value={v.codigo} onChange={cambiar('codigo')} required placeholder="RAM-DDR4-16GB" /></div>}
          <div className={editar ? 'col-12' : 'col-6'}><label className="form-label small">Categoría</label><input className="form-control" value={v.categoria} onChange={cambiar('categoria')} required /></div>
          <div className="col-8"><label className="form-label small">Nombre</label><input className="form-control" value={v.nombre} onChange={cambiar('nombre')} required /></div>
          <div className="col-4"><label className="form-label small">Marca</label><input className="form-control" value={v.marca} onChange={cambiar('marca')} /></div>
          <div className="col-4"><label className="form-label small">Precio costo</label><input type="number" min="0" className="form-control" value={v.precio_costo} onChange={cambiar('precio_costo')} required /></div>
          <div className="col-4"><label className="form-label small">Precio venta</label><input type="number" min="0" className="form-control" value={v.precio_venta} onChange={cambiar('precio_venta')} required /></div>
          <div className="col-4"><label className="form-label small">Stock mínimo</label><input type="number" min="0" className="form-control" value={v.stock_minimo} onChange={cambiar('stock_minimo')} required /></div>
          {!editar && <div className="col-4"><label className="form-label small">Stock inicial</label><input type="number" min="0" className="form-control" value={v.stock_inicial} onChange={cambiar('stock_inicial')} /></div>}
        </div>
        {editar && <div className="small text-muted mt-2">El stock no se edita aquí: use entradas o ajustes, para que quede en el kardex.</div>}
        <div className="text-end mt-3"><BotonEnviar enviando={enviando}>Guardar</BotonEnviar></div>
      </form>
    </Modal>
  )
}

function ModalMovimiento({ repuesto, tipo, onCerrar, onGuardado }) {
  const aviso = useAvisos()
  const [v, cambiar] = useFormulario({ cantidad: 1, costo_unitario: '', motivo: tipo === 'entrada' ? 'Compra a proveedor' : '', ajuste: 'NEGATIVO' })
  const [error, setError] = useState(null)
  const guardar = async (e) => {
    e.preventDefault()
    try {
      if (tipo === 'entrada') {
        await api('inventario', `/repuestos/${repuesto.id_repuesto}/entradas`, {
          method: 'POST', body: { cantidad: Number(v.cantidad), costo_unitario: v.costo_unitario ? Number(v.costo_unitario) : null, motivo: v.motivo || null },
        })
      } else {
        await api('inventario', `/repuestos/${repuesto.id_repuesto}/ajustes`, {
          method: 'POST', body: { tipo: v.ajuste, cantidad: Number(v.cantidad), motivo: v.motivo },
        })
      }
      aviso.ok('Movimiento registrado')
      onGuardado()
      onCerrar()
    } catch (err) { setError(err.message) }
  }
  return (
    <Modal titulo={`${tipo === 'entrada' ? 'Entrada' : 'Ajuste'} · ${repuesto.codigo}`} abierto onCerrar={onCerrar}>
      <form onSubmit={guardar}>
        {error && <div className="alert alert-danger py-2 small">{error}</div>}
        <div className="small text-muted mb-2">Stock actual: <strong>{repuesto.stock_actual}</strong></div>
        <div className="row g-2">
          {tipo === 'ajuste' && (
            <div className="col-6"><label className="form-label small">Tipo de ajuste</label>
              <select className="form-select" value={v.ajuste} onChange={cambiar('ajuste')}><option value="NEGATIVO">Restar (daño, pérdida)</option><option value="POSITIVO">Sumar (conteo)</option></select>
            </div>
          )}
          <div className="col-6"><label className="form-label small">Cantidad</label><input type="number" min="1" className="form-control" value={v.cantidad} onChange={cambiar('cantidad')} required /></div>
          {tipo === 'entrada' && <div className="col-6"><label className="form-label small">Costo unitario (opcional)</label><input type="number" min="0" className="form-control" value={v.costo_unitario} onChange={cambiar('costo_unitario')} /></div>}
          <div className="col-12"><label className="form-label small">Motivo</label><input className="form-control" value={v.motivo} onChange={cambiar('motivo')} required={tipo === 'ajuste'} minLength={tipo === 'ajuste' ? 5 : 0} /></div>
        </div>
        <div className="text-end mt-3"><button className="btn btn-primary">Registrar</button></div>
      </form>
    </Modal>
  )
}

function ModalKardex({ repuesto, onCerrar }) {
  const { datos, cargando, error } = useCarga(() => api('inventario', `/repuestos/${repuesto.id_repuesto}/movimientos`), [repuesto.id_repuesto])
  return (
    <Modal titulo={`Kardex · ${repuesto.codigo}`} abierto onCerrar={onCerrar} tamano="lg">
      <ErrorAlerta error={error} />
      {cargando ? <Cargando /> : (
        <table className="table table-sm">
          <thead><tr><th>Fecha</th><th>Tipo</th><th className="text-end">Cant.</th><th className="text-end">Antes</th><th className="text-end">Después</th><th>Orden</th><th>Motivo</th></tr></thead>
          <tbody>
            {datos.map((m) => (
              <tr key={m.id_movimiento}>
                <td className="small text-nowrap">{fecha(m.fecha)}</td>
                <td><span className={`badge text-bg-${TIPOS_MOV[m.tipo][1]}`}>{TIPOS_MOV[m.tipo][0]}</span></td>
                <td className="text-end">{m.cantidad}</td><td className="text-end">{m.stock_anterior}</td><td className="text-end fw-semibold">{m.stock_resultante}</td>
                <td>{m.id_orden ? `#${m.id_orden}` : '—'}</td><td className="small">{m.motivo || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Modal>
  )
}

export default function Inventario() {
  const { tieneRol } = useAuth()
  const gestiona = tieneRol('ADMINISTRADOR', 'INVENTARIO')
  const [buscar, setBuscar] = useState('')
  const [soloBajo, setSoloBajo] = useState(false)
  const [modal, setModal] = useState(null)   // { tipo, repuesto }
  const { datos, cargando, error, recargar } = useCarga(() => api('inventario', '/repuestos', { query: { buscar, stock_bajo: soloBajo } }), [buscar, soloBajo])

  return (
    <>
      <Encabezado titulo="Inventario de repuestos" icono="box-seam" subtitulo="Existencias, entradas, ajustes y kardex">
        {gestiona && <button className="btn btn-primary" onClick={() => setModal({ tipo: 'nuevo' })}><i className="bi bi-plus-lg me-1" />Nuevo repuesto</button>}
      </Encabezado>
      <div className="card shadow-sm border-0">
        <div className="card-body">
          <div className="row g-2 mb-3 align-items-center">
            <div className="col-md-8"><input className="form-control" placeholder="Buscar por código, nombre o marca..." value={buscar} onChange={(e) => setBuscar(e.target.value)} /></div>
            <div className="col-md-4">
              <div className="form-check form-switch">
                <input id="bajo" className="form-check-input" type="checkbox" checked={soloBajo} onChange={(e) => setSoloBajo(e.target.checked)} />
                <label htmlFor="bajo" className="form-check-label">Solo stock bajo</label>
              </div>
            </div>
          </div>
          <ErrorAlerta error={error} onReintentar={recargar} />
          {cargando && !datos ? <Cargando /> : datos?.length === 0 ? <Vacio texto="No hay repuestos" /> : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead><tr><th>Código</th><th>Repuesto</th><th>Categoría</th><th className="text-end">Costo</th><th className="text-end">Venta</th><th className="text-center">Stock</th><th /></tr></thead>
                <tbody>
                  {datos?.map((r) => (
                    <tr key={r.id_repuesto}>
                      <td><code>{r.codigo}</code></td>
                      <td><div className="fw-semibold">{r.nombre}</div><div className="small text-muted">{r.marca}</div></td>
                      <td className="small">{r.categoria}</td>
                      <td className="text-end">{dinero(r.precio_costo)}</td>
                      <td className="text-end">{dinero(r.precio_venta)}</td>
                      <td className="text-center">
                        <span className={`badge fs-6 text-bg-${r.stock_actual === 0 ? 'danger' : r.stock_bajo ? 'warning' : 'success'}`}>{r.stock_actual}</span>
                        <div className="small text-muted">mín. {r.stock_minimo}</div>
                      </td>
                      <td className="text-end text-nowrap">
                        <button className="btn btn-sm btn-outline-secondary me-1" title="Kardex" onClick={() => setModal({ tipo: 'kardex', repuesto: r })}><i className="bi bi-list-columns" /></button>
                        {gestiona && <>
                          <button className="btn btn-sm btn-outline-success me-1" title="Entrada" onClick={() => setModal({ tipo: 'entrada', repuesto: r })}><i className="bi bi-box-arrow-in-down" /></button>
                          <button className="btn btn-sm btn-outline-warning me-1" title="Ajuste" onClick={() => setModal({ tipo: 'ajuste', repuesto: r })}><i className="bi bi-sliders" /></button>
                          <button className="btn btn-sm btn-outline-primary" title="Editar" onClick={() => setModal({ tipo: 'editar', repuesto: r })}><i className="bi bi-pencil" /></button>
                        </>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      {modal?.tipo === 'nuevo' && <ModalRepuesto onCerrar={() => setModal(null)} onGuardado={recargar} />}
      {modal?.tipo === 'editar' && <ModalRepuesto repuesto={modal.repuesto} onCerrar={() => setModal(null)} onGuardado={recargar} />}
      {['entrada', 'ajuste'].includes(modal?.tipo) && <ModalMovimiento repuesto={modal.repuesto} tipo={modal.tipo} onCerrar={() => setModal(null)} onGuardado={recargar} />}
      {modal?.tipo === 'kardex' && <ModalKardex repuesto={modal.repuesto} onCerrar={() => setModal(null)} />}
    </>
  )
}
