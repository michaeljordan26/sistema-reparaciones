// Secciones del detalle de una orden. Cada una decide si muestra un formulario
// (cuando es el paso actual y el usuario tiene permiso) o solo la información.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../services/api'
import { dia, dinero, fecha } from '../../utils/formato'
import { BotonConfirmar, BotonEnviar, Insignia, useFormulario } from '../comunes'

const IVA = 0.19

// ----------------------------------------------------------- Asignar técnico
export function AsignarTecnico({ orden, onHecho, ejecutar }) {
  const [tecnicos, setTecnicos] = useState([])
  const [elegido, setElegido] = useState('')
  useEffect(() => {
    api('usuarios', '/tecnicos', { query: { estado: 'ACTIVO' } }).then(setTecnicos).catch(() => setTecnicos([]))
  }, [])
  const actual = orden.asignacion_activa?.id_tecnico
  return (
    <form className="d-flex gap-2" onSubmit={(e) => {
      e.preventDefault()
      ejecutar(() => api('ordenes', `/ordenes/${orden.id_orden}/asignar`, { method: 'POST', body: { id_tecnico: Number(elegido) } }),
        'Técnico asignado').then((ok) => ok && onHecho?.())
    }}>
      <select className="form-select form-select-sm" value={elegido} onChange={(e) => setElegido(e.target.value)} required>
        <option value="">{actual ? 'Reasignar a...' : 'Elegir técnico...'}</option>
        {tecnicos.filter((t) => t.id_tecnico !== actual).map((t) => (
          <option key={t.id_tecnico} value={t.id_tecnico}>{t.usuario.nombres} {t.usuario.apellidos} · {t.especialidad}</option>
        ))}
      </select>
      <button className="btn btn-sm btn-primary text-nowrap" disabled={!elegido}>{actual ? 'Reasignar' : 'Asignar'}</button>
    </form>
  )
}

// ----------------------------------------------------------- Diagnóstico
export function SeccionDiagnostico({ orden, diagnostico, puedeEditar, ejecutar }) {
  const [v, cambiar] = useFormulario({ hallazgos: '', causa_probable: '', solucion_propuesta: '', requiere_repuestos: false, tiempo_estimado_horas: '' })
  const [enviando, setEnviando] = useState(false)

  if (diagnostico) {
    return (
      <div className="card shadow-sm border-0 mb-3">
        <div className="card-header"><i className="bi bi-search me-2 text-primary" />Diagnóstico</div>
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-6"><div className="seccion-titulo">Hallazgos</div><div>{diagnostico.hallazgos}</div></div>
            <div className="col-md-6"><div className="seccion-titulo">Causa probable</div><div>{diagnostico.causa_probable}</div></div>
            <div className="col-md-6"><div className="seccion-titulo">Solución propuesta</div><div>{diagnostico.solucion_propuesta}</div></div>
            <div className="col-md-3"><div className="seccion-titulo">Tiempo estimado</div><div>{diagnostico.tiempo_estimado_horas ? `${diagnostico.tiempo_estimado_horas} h` : '—'}</div></div>
            <div className="col-md-3"><div className="seccion-titulo">Fecha</div><div className="small">{fecha(diagnostico.fecha)}</div></div>
          </div>
        </div>
      </div>
    )
  }
  if (!(orden.estado_actual === 'EN_DIAGNOSTICO' && puedeEditar)) return null

  const guardar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    await ejecutar(() => api('reparaciones', '/diagnosticos', {
      method: 'POST',
      body: { ...v, id_orden: orden.id_orden, tiempo_estimado_horas: v.tiempo_estimado_horas ? Number(v.tiempo_estimado_horas) : null },
    }), 'Diagnóstico registrado: la orden quedó esperando aprobación del cliente')
    setEnviando(false)
  }
  return (
    <div className="card shadow-sm border-0 mb-3 paso-siguiente">
      <div className="card-header"><i className="bi bi-search me-2 text-primary" />Registrar diagnóstico</div>
      <div className="card-body">
        <form onSubmit={guardar}>
          <div className="mb-2">
            <label className="form-label small">Hallazgos</label>
            <textarea className="form-control" rows="3" value={v.hallazgos} onChange={cambiar('hallazgos')} required minLength={10}
              placeholder="Qué se encontró al revisar el equipo" />
          </div>
          <div className="row g-2 mb-2">
            <div className="col-md-6">
              <label className="form-label small">Causa probable</label>
              <input className="form-control" value={v.causa_probable} onChange={cambiar('causa_probable')} required minLength={5} />
            </div>
            <div className="col-md-6">
              <label className="form-label small">Solución propuesta</label>
              <input className="form-control" value={v.solucion_propuesta} onChange={cambiar('solucion_propuesta')} required minLength={5} />
            </div>
            <div className="col-md-4">
              <label className="form-label small">Tiempo estimado (horas)</label>
              <input type="number" step="0.5" min="0.5" className="form-control" value={v.tiempo_estimado_horas} onChange={cambiar('tiempo_estimado_horas')} />
            </div>
            <div className="col-md-8 d-flex align-items-end">
              <div className="form-check mb-2">
                <input id="rr" type="checkbox" className="form-check-input" checked={v.requiere_repuestos} onChange={cambiar('requiere_repuestos')} />
                <label htmlFor="rr" className="form-check-label">Requiere repuestos</label>
              </div>
            </div>
          </div>
          <BotonEnviar enviando={enviando}><i className="bi bi-send me-1" />Registrar diagnóstico</BotonEnviar>
        </form>
      </div>
    </div>
  )
}

// ----------------------------------------------------------- Presupuesto
function TablaDetalles({ detalles }) {
  return (
    <div className="table-responsive"><table className="table table-sm mb-2">
      <thead><tr><th>Concepto</th><th className="text-end">Cant.</th><th className="text-end">Valor unit.</th><th className="text-end">Subtotal</th></tr></thead>
      <tbody>
        {detalles.map((d) => (
          <tr key={d.id_detalle}>
            <td><span className={`badge me-2 text-bg-${d.tipo === 'MANO_OBRA' ? 'info' : 'secondary'}`}>{d.tipo === 'MANO_OBRA' ? 'Mano de obra' : 'Repuesto'}</span>{d.descripcion}</td>
            <td className="text-end">{d.cantidad}{d.tipo === 'MANO_OBRA' ? ' h' : ''}</td>
            <td className="text-end">{dinero(d.precio_unitario)}</td>
            <td className="text-end">{dinero(d.subtotal)}</td>
          </tr>
        ))}
      </tbody>
    </table></div>
  )
}

function Totales({ doc }) {
  return (
    <div className="row justify-content-end">
      <div className="col-sm-7 col-md-5">
        <div className="table-responsive"><table className="table table-sm mb-0">
          <tbody>
            <tr><td>Materiales</td><td className="text-end">{dinero(doc.subtotal_materiales)}</td></tr>
            <tr><td>Mano de obra</td><td className="text-end">{dinero(doc.subtotal_mano_obra)}</td></tr>
            <tr><td>IVA ({doc.iva_porcentaje}%)</td><td className="text-end">{dinero(doc.iva)}</td></tr>
            <tr className="fw-bold"><td>Total</td><td className="text-end">{dinero(doc.total)}</td></tr>
          </tbody>
        </table></div>
      </div>
    </div>
  )
}

function FormPresupuesto({ orden, ejecutar }) {
  const [repuestos, setRepuestos] = useState([])
  const [mano, setMano] = useState([{ descripcion: '', horas: 1, valor_hora: 40000 }])
  const [usados, setUsados] = useState([])
  const [obs, setObs] = useState('')
  const [enviando, setEnviando] = useState(false)
  useEffect(() => { api('inventario', '/repuestos').then(setRepuestos).catch(() => setRepuestos([])) }, [])

  const porId = useMemo(() => Object.fromEntries(repuestos.map((r) => [r.id_repuesto, r])), [repuestos])
  const subMano = mano.reduce((s, m) => s + Number(m.horas || 0) * Number(m.valor_hora || 0), 0)
  const subMat = usados.reduce((s, u) => s + (porId[u.id_repuesto]?.precio_venta || 0) * Number(u.cantidad || 0), 0)
  const estimado = (subMano + subMat) * (1 + IVA)

  const setLinea = (lista, setLista, i, campo) => (e) => setLista(lista.map((x, j) => (j === i ? { ...x, [campo]: e.target.value } : x)))

  const guardar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    await ejecutar(() => api('facturacion', '/presupuestos', {
      method: 'POST',
      body: {
        id_orden: orden.id_orden, observaciones: obs || null,
        mano_obra: mano.map((m) => ({ descripcion: m.descripcion, horas: Number(m.horas), valor_hora: Number(m.valor_hora) })),
        repuestos: usados.filter((u) => u.id_repuesto).map((u) => ({ id_repuesto: Number(u.id_repuesto), cantidad: Number(u.cantidad) })),
      },
    }), 'Presupuesto creado')
    setEnviando(false)
  }

  return (
    <form onSubmit={guardar}>
      <div className="seccion-titulo mb-2">Mano de obra</div>
      {mano.map((m, i) => (
        <div className="row g-2 mb-2" key={i}>
          <div className="col-md-6"><input className="form-control form-control-sm" placeholder="Actividad" value={m.descripcion} onChange={setLinea(mano, setMano, i, 'descripcion')} required minLength={3} /></div>
          <div className="col-4 col-md-2"><input type="number" step="0.5" min="0.5" className="form-control form-control-sm" title="Horas" value={m.horas} onChange={setLinea(mano, setMano, i, 'horas')} required /></div>
          <div className="col-6 col-md-3"><input type="number" min="0" step="1000" className="form-control form-control-sm" title="Valor hora" value={m.valor_hora} onChange={setLinea(mano, setMano, i, 'valor_hora')} required /></div>
          <div className="col-2 col-md-1">{mano.length > 1 && <button type="button" className="btn btn-sm btn-light" onClick={() => setMano(mano.filter((_, j) => j !== i))}><i className="bi bi-x" /></button>}</div>
        </div>
      ))}
      <button type="button" className="btn btn-sm btn-link px-0 mb-3" onClick={() => setMano([...mano, { descripcion: '', horas: 1, valor_hora: 40000 }])}>+ Agregar actividad</button>

      <div className="seccion-titulo mb-2">Repuestos estimados</div>
      {usados.map((u, i) => (
        <div className="row g-2 mb-2" key={i}>
          <div className="col-md-8">
            <select className="form-select form-select-sm" value={u.id_repuesto} onChange={setLinea(usados, setUsados, i, 'id_repuesto')} required>
              <option value="">Elegir repuesto...</option>
              {repuestos.map((r) => <option key={r.id_repuesto} value={r.id_repuesto}>{r.codigo} · {r.nombre} · {dinero(r.precio_venta)} (stock {r.stock_actual})</option>)}
            </select>
          </div>
          <div className="col-4 col-md-3"><input type="number" min="1" className="form-control form-control-sm" value={u.cantidad} onChange={setLinea(usados, setUsados, i, 'cantidad')} required /></div>
          <div className="col-2 col-md-1"><button type="button" className="btn btn-sm btn-light" onClick={() => setUsados(usados.filter((_, j) => j !== i))}><i className="bi bi-x" /></button></div>
        </div>
      ))}
      <button type="button" className="btn btn-sm btn-link px-0 mb-3" onClick={() => setUsados([...usados, { id_repuesto: '', cantidad: 1 }])}>+ Agregar repuesto</button>

      <input className="form-control form-control-sm mb-3" placeholder="Observaciones (opcional)" value={obs} onChange={(e) => setObs(e.target.value)} />
      <div className="d-flex justify-content-between align-items-center">
        <div className="small text-muted">Total estimado con IVA: <strong className="text-body">{dinero(estimado)}</strong></div>
        <BotonEnviar enviando={enviando}><i className="bi bi-file-earmark-text me-1" />Crear presupuesto</BotonEnviar>
      </div>
    </form>
  )
}

function FormRespuesta({ presupuesto, nombreSugerido, ejecutar }) {
  const [v, cambiar] = useFormulario({ nombre_responde: nombreSugerido || '', medio: 'PRESENCIAL', observacion: '' })
  const responder = (decision) => ejecutar(() => api('facturacion', `/presupuestos/${presupuesto.id_presupuesto}/respuesta`, {
    method: 'POST', body: { ...v, decision, observacion: v.observacion || null },
  }), decision === 'APROBADO' ? 'Presupuesto aprobado: la orden pasó a reparación' : 'Presupuesto rechazado: el equipo se devolverá sin reparar')
  return (
    <div className="border rounded p-3 bg-light mt-3">
      <div className="fw-semibold mb-2">Respuesta del cliente</div>
      <div className="row g-2 mb-2">
        <div className="col-md-6"><input className="form-control form-control-sm" placeholder="Quién responde" value={v.nombre_responde} onChange={cambiar('nombre_responde')} /></div>
        <div className="col-md-6">
          <select className="form-select form-select-sm" value={v.medio} onChange={cambiar('medio')}>
            {['PRESENCIAL', 'TELEFONO', 'CORREO', 'WHATSAPP'].map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div className="col-12"><input className="form-control form-control-sm" placeholder="Observación (opcional)" value={v.observacion} onChange={cambiar('observacion')} /></div>
      </div>
      <div className="d-flex gap-2">
        <button className="btn btn-success" disabled={v.nombre_responde.trim().length < 3} onClick={() => responder('APROBADO')}><i className="bi bi-hand-thumbs-up me-1" />Aprobó</button>
        <button className="btn btn-outline-danger" disabled={v.nombre_responde.trim().length < 3} onClick={() => responder('RECHAZADO')}><i className="bi bi-hand-thumbs-down me-1" />Rechazó</button>
      </div>
    </div>
  )
}

export function SeccionPresupuesto({ orden, presupuesto, permisos, nombreCliente, ejecutar }) {
  const esperando = orden.estado_actual === 'ESPERANDO_APROBACION'
  if (!presupuesto && !esperando) return null
  const color = { PENDIENTE: 'warning', APROBADO: 'success', RECHAZADO: 'danger', ANULADO: 'secondary' }
  return (
    <div className={`card shadow-sm border-0 mb-3 ${esperando ? 'paso-siguiente' : ''}`}>
      <div className="card-header d-flex justify-content-between align-items-center">
        <span><i className="bi bi-file-earmark-text me-2 text-primary" />Presupuesto {presupuesto?.codigo}</span>
        {presupuesto && <Insignia texto={presupuesto.estado} color={color[presupuesto.estado]} />}
      </div>
      <div className="card-body">
        {!presupuesto && (permisos.presupuestar
          ? <FormPresupuesto orden={orden} ejecutar={ejecutar} />
          : <div className="text-muted">Esperando que se elabore el presupuesto.</div>)}
        {presupuesto && (
          <>
            <TablaDetalles detalles={presupuesto.detalles} />
            <Totales doc={presupuesto} />
            <div className="small text-muted mt-2">
              Elaborado {dia(presupuesto.fecha)} · válido hasta {dia(presupuesto.fecha_vencimiento)}
              {presupuesto.vencido && <span className="text-danger fw-semibold"> · VENCIDO</span>}
            </div>
            {presupuesto.respuesta && (
              <div className="small mt-2"><i className="bi bi-chat-left-text me-1" />
                {presupuesto.respuesta.decision === 'APROBADO' ? 'Aprobado' : 'Rechazado'} por <strong>{presupuesto.respuesta.nombre_responde}</strong> ({presupuesto.respuesta.medio.toLowerCase()}) el {fecha(presupuesto.respuesta.fecha)}
                {presupuesto.respuesta.observacion && ` — "${presupuesto.respuesta.observacion}"`}
              </div>
            )}
            {presupuesto.estado === 'PENDIENTE' && esperando && permisos.atiende && (
              <FormRespuesta presupuesto={presupuesto} nombreSugerido={nombreCliente} ejecutar={ejecutar} />
            )}
            {presupuesto.estado === 'PENDIENTE' && permisos.caja && (
              <div className="mt-2 text-end">
                <BotonConfirmar texto="¿Anular para elaborar otro?" onConfirmar={() => ejecutar(() => api('facturacion',
                  `/presupuestos/${presupuesto.id_presupuesto}/anular`, { method: 'PATCH', body: { motivo: 'Anulado desde la interfaz para corregirlo' } }),
                'Presupuesto anulado')}>Anular presupuesto</BotonConfirmar>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ----------------------------------------------------------- Reparación
export function SeccionReparacion({ orden, reparacion, puedeEditar, ejecutar }) {
  const enReparacion = orden.estado_actual === 'EN_REPARACION'
  const [repuestos, setRepuestos] = useState([])
  const [uso, setUso] = useState({ id_repuesto: '', cantidad: 1 })
  const [fin, cambiarFin] = useFormulario({ actividades_realizadas: '', resultado: 'EXITOSA', garantia_dias: 90, observaciones: '' })
  const editable = enReparacion && puedeEditar && reparacion?.estado === 'EN_PROCESO'
  useEffect(() => {
    if (editable) api('inventario', '/repuestos').then(setRepuestos).catch(() => setRepuestos([]))
  }, [editable, reparacion?.repuestos?.length])

  if (!reparacion && !enReparacion) return null
  const base = reparacion ? `/reparaciones/${reparacion.id_reparacion}` : ''

  return (
    <div className={`card shadow-sm border-0 mb-3 ${enReparacion ? 'paso-siguiente' : ''}`}>
      <div className="card-header d-flex justify-content-between align-items-center">
        <span><i className="bi bi-tools me-2 text-primary" />Reparación</span>
        {reparacion && <Insignia texto={reparacion.estado === 'FINALIZADA' ? `FINALIZADA · ${reparacion.resultado}` : 'EN PROCESO'}
          color={reparacion.estado === 'FINALIZADA' ? 'success' : 'primary'} />}
      </div>
      <div className="card-body">
        {!reparacion && (puedeEditar
          ? <button className="btn btn-primary" onClick={() => ejecutar(() => api('reparaciones', '/reparaciones', { method: 'POST', body: { id_orden: orden.id_orden } }), 'Reparación iniciada')}>
            <i className="bi bi-play-fill me-1" />Iniciar reparación</button>
          : <div className="text-muted">El técnico asignado debe iniciar la reparación.</div>)}

        {reparacion && (
          <>
            <div className="seccion-titulo mb-2">Repuestos utilizados</div>
            {reparacion.repuestos.length === 0 ? <div className="text-muted small mb-3">Aún no se han usado repuestos.</div> : (
              <div className="table-responsive"><table className="table table-sm">
                <thead><tr><th>Repuesto</th><th className="text-end">Cant.</th><th className="text-end">Precio</th><th className="text-end">Subtotal</th>{editable && <th />}</tr></thead>
                <tbody>
                  {reparacion.repuestos.map((r) => (
                    <tr key={r.id_repuesto_utilizado}>
                      <td><code>{r.codigo}</code> {r.nombre}</td>
                      <td className="text-end">{r.cantidad}</td>
                      <td className="text-end">{dinero(r.precio_unitario)}</td>
                      <td className="text-end">{dinero(r.cantidad * r.precio_unitario)}</td>
                      {editable && <td className="text-end"><BotonConfirmar texto="¿Devolver?" onConfirmar={() => ejecutar(() => api('reparaciones',
                        `${base}/repuestos/${r.id_repuesto_utilizado}`, { method: 'DELETE' }), 'Repuesto devuelto al inventario')}><i className="bi bi-arrow-counterclockwise" /></BotonConfirmar></td>}
                    </tr>
                  ))}
                  <tr className="fw-semibold"><td colSpan={3}>Total repuestos</td><td className="text-end">{dinero(reparacion.total_repuestos)}</td>{editable && <td />}</tr>
                </tbody>
              </table></div>
            )}

            {editable && (
              <form className="row g-2 mb-4" onSubmit={(e) => {
                e.preventDefault()
                ejecutar(() => api('reparaciones', `${base}/repuestos`, { method: 'POST', body: { id_repuesto: Number(uso.id_repuesto), cantidad: Number(uso.cantidad) } }),
                  'Repuesto descontado del inventario').then((ok) => ok && setUso({ id_repuesto: '', cantidad: 1 }))
              }}>
                <div className="col-md-8">
                  <select className="form-select form-select-sm" value={uso.id_repuesto} onChange={(e) => setUso({ ...uso, id_repuesto: e.target.value })} required>
                    <option value="">Usar repuesto del inventario...</option>
                    {repuestos.map((r) => <option key={r.id_repuesto} value={r.id_repuesto} disabled={r.stock_actual === 0}>
                      {r.codigo} · {r.nombre} — stock {r.stock_actual}</option>)}
                  </select>
                </div>
                <div className="col-6 col-md-2"><input type="number" min="1" className="form-control form-control-sm" value={uso.cantidad} onChange={(e) => setUso({ ...uso, cantidad: e.target.value })} /></div>
                <div className="col-6 col-md-2"><button className="btn btn-sm btn-outline-primary w-100">Usar</button></div>
              </form>
            )}

            {reparacion.estado === 'FINALIZADA' ? (
              <div className="row g-3">
                <div className="col-md-8"><div className="seccion-titulo">Actividades realizadas</div><div>{reparacion.actividades_realizadas}</div></div>
                <div className="col-md-4"><div className="seccion-titulo">Finalizada</div><div className="small">{fecha(reparacion.fecha_fin)}</div></div>
                {reparacion.observaciones && <div className="col-12"><div className="seccion-titulo">Observaciones</div><div>{reparacion.observaciones}</div></div>}
              </div>
            ) : editable && (
              <form className="border rounded p-3 bg-light" onSubmit={(e) => {
                e.preventDefault()
                ejecutar(() => api('reparaciones', `${base}/finalizar`, {
                  method: 'POST',
                  body: { ...fin, garantia_dias: Number(fin.garantia_dias), observaciones: fin.observaciones || null },
                }), 'Reparación finalizada: el equipo está listo para entregar')
              }}>
                <div className="fw-semibold mb-2">Finalizar reparación</div>
                <textarea className="form-control form-control-sm mb-2" rows="2" placeholder="Actividades realizadas" value={fin.actividades_realizadas}
                  onChange={cambiarFin('actividades_realizadas')} required minLength={10} />
                <div className="row g-2 mb-2">
                  <div className="col-md-5">
                    <label className="form-label small mb-0">Resultado</label>
                    <select className="form-select form-select-sm" value={fin.resultado} onChange={cambiarFin('resultado')}>
                      <option value="EXITOSA">Exitosa</option><option value="PARCIAL">Parcial</option><option value="NO_REPARABLE">No reparable</option>
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label className="form-label small mb-0">Garantía (días)</label>
                    <input type="number" min="0" max="730" className="form-control form-control-sm" value={fin.garantia_dias} onChange={cambiarFin('garantia_dias')} />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label small mb-0">Observaciones</label>
                    <input className="form-control form-control-sm" value={fin.observaciones} onChange={cambiarFin('observaciones')} />
                  </div>
                </div>
                <button className="btn btn-success"><i className="bi bi-check2-circle me-1" />Finalizar y dejar listo para entrega</button>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ----------------------------------------------------------- Factura y pagos
export function SeccionFactura({ orden, presupuesto, factura, permisos, ejecutar }) {
  const listo = orden.estado_actual === 'LISTO_ENTREGA'
  const [pago, setPago] = useState({ monto: '', metodo: 'EFECTIVO', referencia: '' })
  if (presupuesto?.estado !== 'APROBADO' || !['LISTO_ENTREGA', 'ENTREGADO'].includes(orden.estado_actual)) return null

  return (
    <div className={`card shadow-sm border-0 mb-3 ${listo && (!factura || factura.saldo > 0) ? 'paso-siguiente' : ''}`}>
      <div className="card-header d-flex justify-content-between align-items-center">
        <span><i className="bi bi-receipt me-2 text-primary" />Factura {factura?.numero}</span>
        {factura && <Insignia texto={factura.estado} color={{ PENDIENTE: 'warning', PARCIAL: 'info', PAGADA: 'success', ANULADA: 'secondary' }[factura.estado]} />}
      </div>
      <div className="card-body">
        {!factura && (permisos.caja && listo
          ? <div>
            <p className="text-muted small">La factura toma la mano de obra del presupuesto y los repuestos <strong>realmente usados</strong> según el inventario.</p>
            <button className="btn btn-primary" onClick={() => ejecutar(() => api('facturacion', '/facturas', { method: 'POST', body: { id_orden: orden.id_orden } }), 'Factura generada')}>
              <i className="bi bi-receipt me-1" />Generar factura</button>
          </div>
          : <div className="text-muted">Caja debe generar la factura antes de la entrega.</div>)}
        {factura && (
          <>
            <TablaDetalles detalles={factura.detalles} />
            <Totales doc={factura} />
            <div className="d-flex justify-content-end gap-4 mt-2">
              <div>Pagado: <strong className="text-success">{dinero(factura.total_pagado)}</strong></div>
              <div>Saldo: <strong className={factura.saldo > 0 ? 'text-danger' : 'text-success'}>{dinero(factura.saldo)}</strong></div>
            </div>
            {factura.pagos.length > 0 && (
              <>
                <div className="seccion-titulo mt-3 mb-1">Pagos</div>
                <div className="table-responsive"><table className="table table-sm mb-0">
                  <thead><tr><th>Fecha</th><th>Tipo</th><th>Método</th><th>Referencia</th><th className="text-end">Monto</th></tr></thead>
                  <tbody>
                    {factura.pagos.map((p) => (
                      <tr key={p.id_pago} className={p.anulado ? 'text-decoration-line-through text-muted' : ''}>
                        <td className="small">{fecha(p.fecha)}</td>
                        <td><Insignia texto={p.tipo === 'ABONO' ? 'Abono' : 'Pago total'} color={p.tipo === 'ABONO' ? 'info' : 'success'} /></td>
                        <td>{p.metodo}</td><td className="small">{p.referencia || '—'}</td>
                        <td className="text-end">{dinero(p.monto)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table></div>
              </>
            )}
            {factura.saldo > 0 && permisos.cobra && (
              <form className="row g-2 mt-3 border rounded p-2 bg-light mx-0" onSubmit={(e) => {
                e.preventDefault()
                ejecutar(() => api('facturacion', `/facturas/${factura.id_factura}/pagos`, {
                  method: 'POST', body: { monto: Number(pago.monto || factura.saldo), metodo: pago.metodo, referencia: pago.referencia || null },
                }), 'Pago registrado').then((ok) => ok && setPago({ monto: '', metodo: 'EFECTIVO', referencia: '' }))
              }}>
                <div className="col-12 fw-semibold small">Registrar pago o abono</div>
                <div className="col-md-4"><input type="number" min="1" max={factura.saldo} step="any" className="form-control form-control-sm"
                  placeholder={`Saldo: ${dinero(factura.saldo)}`} value={pago.monto} onChange={(e) => setPago({ ...pago, monto: e.target.value })} /></div>
                <div className="col-md-3">
                  <select className="form-select form-select-sm" value={pago.metodo} onChange={(e) => setPago({ ...pago, metodo: e.target.value })}>
                    {['EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'NEQUI', 'DAVIPLATA'].map((m) => <option key={m}>{m}</option>)}
                  </select>
                </div>
                <div className="col-md-3"><input className="form-control form-control-sm" placeholder={pago.metodo === 'EFECTIVO' ? 'Referencia (opcional)' : 'Referencia *'}
                  value={pago.referencia} onChange={(e) => setPago({ ...pago, referencia: e.target.value })} required={pago.metodo !== 'EFECTIVO'} /></div>
                <div className="col-md-2"><button className="btn btn-sm btn-success w-100">Cobrar</button></div>
                <div className="col-12 small text-muted">Si deja el monto vacío se cobra el saldo completo.</div>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ----------------------------------------------------------- Garantía
export function SeccionGarantia({ garantia }) {
  if (!garantia) return null
  const color = { VIGENTE: 'success', VENCIDA: 'secondary', ANULADA: 'danger' }[garantia.estado]
  return (
    <div className="card shadow-sm border-0 mb-3">
      <div className="card-header d-flex justify-content-between align-items-center">
        <span><i className="bi bi-shield-check me-2 text-primary" />Garantía #{garantia.id_garantia}</span>
        <Insignia texto={garantia.estado} color={color} />
      </div>
      <div className="card-body">
        <div className="row g-2">
          <div className="col-md-4"><div className="seccion-titulo">Vigencia</div>{dia(garantia.fecha_inicio)} → {dia(garantia.fecha_fin)} ({garantia.dias} días)</div>
          <div className="col-md-8"><div className="seccion-titulo">Cobertura</div>{garantia.cobertura}</div>
          <div className="col-12 small text-muted">{garantia.condiciones}</div>
          {garantia.reclamaciones.length > 0 && (
            <div className="col-12"><div className="seccion-titulo">Reclamaciones</div>
              {garantia.reclamaciones.map((r) => (
                <div key={r.id_reclamacion} className="small">• {r.descripcion} — <strong>{r.estado}</strong>{r.respuesta && `: ${r.respuesta}`}</div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
