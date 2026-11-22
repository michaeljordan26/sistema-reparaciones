// Pantalla central: todo el ciclo de vida de una orden en un solo lugar.
// Reúne datos de 6 microservicios y muestra a cada rol solo las acciones que le corresponden.
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { BotonConfirmar, Cargando, ErrorAlerta, EstadoOrden, Prioridad } from '../components/comunes'
import { AsignarTecnico, SeccionDiagnostico, SeccionFactura, SeccionGarantia, SeccionPresupuesto, SeccionReparacion } from '../components/orden/Secciones'
import { useAuth } from '../context/AuthContext'
import { useAvisos } from '../context/AvisosContext'
import { api, apiOpcional } from '../services/api'
import { dinero, ESTADOS_ORDEN, fecha, FLUJO, nombreCliente, nombreEquipo } from '../utils/formato'

function Pasos({ estado }) {
  const indice = FLUJO.indexOf(estado)
  return (
    <div className="pasos">
      {FLUJO.map((e, i) => (
        <div key={e} className={`paso ${i < indice ? 'hecho' : ''} ${i === indice ? 'actual' : ''}`}>
          <div className="punto"><i className={`bi bi-${i < indice ? 'check-lg' : ESTADOS_ORDEN[e].icono}`} /></div>
          {ESTADOS_ORDEN[e].texto}
        </div>
      ))}
    </div>
  )
}

function SiguientePaso({ orden, saldo, presupuesto, permisos, ejecutar }) {
  const e = orden.estado_actual
  const id = orden.id_orden
  const mover = (estado, texto, obs) => ejecutar(() => api('ordenes', `/ordenes/${id}/estado`, { method: 'PATCH', body: { estado, observacion: obs } }), texto)

  let contenido = null
  if (e === 'RECIBIDO') {
    contenido = !orden.asignacion_activa
      ? (permisos.recepcion ? 'Asigne un técnico para que diagnostique el equipo (panel derecho).' : 'Esperando que recepción asigne un técnico.')
      : permisos.tecnico
        ? <button className="btn btn-primary" onClick={() => mover('EN_DIAGNOSTICO', 'Diagnóstico iniciado', 'Inicio de revisión')}><i className="bi bi-search me-1" />Iniciar diagnóstico</button>
        : `Esperando que ${orden.asignacion_activa.nombre_tecnico} inicie el diagnóstico.`
  } else if (e === 'EN_DIAGNOSTICO') {
    contenido = permisos.tecnico ? 'Registre el diagnóstico abajo. Al guardarlo, la orden pasa a esperar la aprobación del cliente.' : 'El técnico está revisando el equipo.'
  } else if (e === 'ESPERANDO_APROBACION') {
    contenido = !presupuesto ? 'Elabore el presupuesto para el cliente.' : 'Registre si el cliente aprueba o rechaza el presupuesto.'
  } else if (e === 'EN_REPARACION') {
    contenido = 'El técnico registra los repuestos usados y finaliza la reparación.'
  } else if (e === 'LISTO_ENTREGA') {
    const debe = saldo?.saldo_pendiente > 0
    contenido = (
      <div className="d-flex flex-wrap align-items-center gap-3">
        <div>
          {debe ? <>Saldo pendiente: <strong className="text-danger">{dinero(saldo.saldo_pendiente)}</strong> <span className="small text-muted">({saldo.detalle})</span></>
            : <><i className="bi bi-check-circle text-success me-1" />Sin saldo pendiente. Puede entregar el equipo.</>}
        </div>
        {permisos.recepcion && (
          <button className="btn btn-success" disabled={debe} title={debe ? 'Primero debe pagarse el saldo' : ''}
            onClick={() => mover('ENTREGADO', 'Equipo entregado', 'Entregado al cliente')}>
            <i className="bi bi-bag-check me-1" />Entregar equipo
          </button>
        )}
      </div>
    )
  } else {
    contenido = <span><i className="bi bi-lock me-1" />Orden cerrada el {fecha(orden.fecha_cierre)}</span>
  }

  return (
    <div className="card shadow-sm border-0 mb-3 paso-siguiente">
      <div className="card-body d-flex flex-wrap justify-content-between align-items-center gap-2">
        <div><div className="seccion-titulo mb-1">Siguiente paso</div>{contenido}</div>
        {permisos.recepcion && orden.transiciones_permitidas.includes('CANCELADO') && (
          <BotonConfirmar texto="¿Cancelar la orden?" onConfirmar={() => mover('CANCELADO', 'Orden cancelada', 'Cancelada desde recepción')}>
            <i className="bi bi-x-circle me-1" />Cancelar orden
          </BotonConfirmar>
        )}
      </div>
    </div>
  )
}

export default function OrdenDetalle() {
  const { id } = useParams()
  const { usuario, tieneRol } = useAuth()
  const aviso = useAvisos()
  const [d, setD] = useState(null)
  const [error, setError] = useState(null)

  const cargar = useCallback(async () => {
    try {
      const orden = await api('ordenes', `/ordenes/${id}`)
      const opcional = (p) => p.catch(() => null)
      const [equipo, resumen, presupuesto, facturas, saldo, notificaciones] = await Promise.all([
        opcional(api('clientes', `/equipos/${orden.id_equipo}`)),
        opcional(api('reparaciones', `/ordenes/${id}/resumen`)),
        opcional(apiOpcional('facturacion', `/ordenes/${id}/presupuesto`)),
        opcional(api('facturacion', '/facturas', { query: { id_orden: id } })),
        opcional(api('facturacion', `/ordenes/${id}/saldo`)),
        tieneRol('ADMINISTRADOR', 'RECEPCIONISTA') ? opcional(api('reportes', '/notificaciones', { query: { id_orden: id } })) : null,
      ])
      setD({ orden, equipo, resumen, presupuesto, factura: (facturas || []).find((f) => f.estado !== 'ANULADA') || null, saldo, notificaciones })
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [id, tieneRol])

  useEffect(() => { cargar() }, [cargar])

  // Ejecuta una acción, muestra el resultado y recarga. Devuelve true si salió bien.
  const ejecutar = async (accion, exito) => {
    try {
      await accion()
      await cargar()          // primero se actualiza la pantalla y luego se avisa
      aviso.ok(exito)
      setTimeout(cargar, 1500)   // las notificaciones (MS7) llegan un instante después
      return true
    } catch (e) {
      aviso.error(e.message)
      return false
    }
  }

  if (error) return <ErrorAlerta error={error} onReintentar={cargar} />
  if (!d) return <Cargando />

  const { orden, equipo, resumen, presupuesto, factura, saldo, notificaciones } = d
  const asignacion = orden.asignacion_activa
  const esMiOrden = !!asignacion && usuario.id_tecnico === asignacion.id_tecnico
  const permisos = {
    recepcion: tieneRol('ADMINISTRADOR', 'RECEPCIONISTA'),
    tecnico: tieneRol('ADMINISTRADOR') || (tieneRol('TECNICO') && esMiOrden),
    presupuestar: tieneRol('ADMINISTRADOR', 'RECEPCIONISTA', 'CAJA') || (tieneRol('TECNICO') && esMiOrden),
    atiende: tieneRol('ADMINISTRADOR', 'RECEPCIONISTA', 'CAJA'),
    caja: tieneRol('ADMINISTRADOR', 'CAJA'),
    cobra: tieneRol('ADMINISTRADOR', 'CAJA', 'RECEPCIONISTA'),
  }
  const cliente = equipo?.cliente
  const abierta = !['ENTREGADO', 'CANCELADO'].includes(orden.estado_actual)

  return (
    <>
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <div>
          <Link to="/ordenes" className="small text-decoration-none"><i className="bi bi-arrow-left me-1" />Órdenes</Link>
          <h1 className="h3 mb-0 d-flex align-items-center gap-2 flex-wrap">
            {orden.codigo}
            <span className="fs-6 d-inline-flex gap-1"><EstadoOrden estado={orden.estado_actual} /><Prioridad valor={orden.prioridad} /></span>
          </h1>
          <div className="text-muted small">Recibida el {fecha(orden.fecha_recepcion)}</div>
        </div>
        <button className="btn btn-light" onClick={cargar} title="Actualizar"><i className="bi bi-arrow-clockwise" /></button>
      </div>

      {orden.estado_actual !== 'CANCELADO' && <div className="card shadow-sm border-0 mb-3"><div className="card-body"><Pasos estado={orden.estado_actual} /></div></div>}

      <div className="row g-3">
        <div className="col-xl-8">
          <SiguientePaso orden={orden} saldo={saldo} presupuesto={presupuesto} permisos={permisos} ejecutar={ejecutar} />
          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header"><i className="bi bi-chat-square-text me-2 text-primary" />Problema reportado</div>
            <div className="card-body">
              <div>{orden.descripcion_problema}</div>
              {orden.accesorios_recibidos && <div className="small text-muted mt-1"><i className="bi bi-paperclip me-1" />Accesorios: {orden.accesorios_recibidos}</div>}
            </div>
          </div>
          <SeccionDiagnostico orden={orden} diagnostico={resumen?.diagnostico} puedeEditar={permisos.tecnico} ejecutar={ejecutar} />
          <SeccionPresupuesto orden={orden} presupuesto={presupuesto} permisos={permisos} nombreCliente={cliente ? nombreCliente(cliente) : ''} ejecutar={ejecutar} />
          <SeccionReparacion orden={orden} reparacion={resumen?.reparacion} puedeEditar={permisos.tecnico} ejecutar={ejecutar} />
          <SeccionFactura orden={orden} presupuesto={presupuesto} factura={factura} permisos={permisos} ejecutar={ejecutar} />
          <SeccionGarantia garantia={resumen?.garantia} />
        </div>

        <div className="col-xl-4">
          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header"><i className="bi bi-person me-2 text-primary" />Cliente y equipo</div>
            <div className="card-body">
              {cliente ? (
                <>
                  <div className="fw-semibold">{permisos.recepcion ? <Link to={`/clientes/${cliente.id_cliente}`}>{nombreCliente(cliente)}</Link> : nombreCliente(cliente)}</div>
                  <div className="small text-muted mb-2">{cliente.telefono}{cliente.correo && ` · ${cliente.correo}`}</div>
                  <div><i className="bi bi-laptop me-1" />{nombreEquipo(equipo)}</div>
                  <div className="small text-muted">Serie <code>{equipo.numero_serie}</code></div>
                </>
              ) : <div className="text-muted small">Cliente #{orden.id_cliente} · Equipo #{orden.id_equipo}</div>}
            </div>
          </div>

          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header"><i className="bi bi-person-gear me-2 text-primary" />Técnico</div>
            <div className="card-body">
              {asignacion ? (
                <div className="mb-2"><div className="fw-semibold">{asignacion.nombre_tecnico}</div><div className="small text-muted">Desde {fecha(asignacion.fecha_asignacion)}</div></div>
              ) : orden.asignaciones.length > 0 ? (
                <div><div className="fw-semibold">{orden.asignaciones.at(-1).nombre_tecnico}</div><div className="small text-muted">Atendió la orden</div></div>
              ) : <div className="text-warning mb-2"><i className="bi bi-exclamation-triangle me-1" />Sin técnico asignado</div>}
              {permisos.recepcion && abierta && <AsignarTecnico orden={orden} ejecutar={ejecutar} />}
            </div>
          </div>

          <div className="card shadow-sm border-0 mb-3">
            <div className="card-header"><i className="bi bi-clock-history me-2 text-primary" />Historial</div>
            <div className="card-body">
              <ul className="linea-tiempo">
                {[...orden.historial].reverse().map((h) => (
                  <li key={h.id_historial}>
                    <div className="small fw-semibold">
                      {h.estado_anterior === h.estado_nuevo ? 'Asignación' : (ESTADOS_ORDEN[h.estado_nuevo]?.texto || h.estado_nuevo)}
                    </div>
                    {h.observacion && <div className="small">{h.observacion}</div>}
                    <div className="small text-muted">{fecha(h.fecha_cambio)}</div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {notificaciones && (
            <div className="card shadow-sm border-0 mb-3">
              <div className="card-header"><i className="bi bi-envelope me-2 text-primary" />Notificaciones al cliente</div>
              <div className="list-group list-group-flush">
                {notificaciones.length === 0 && <div className="list-group-item small text-muted">Sin notificaciones todavía</div>}
                {notificaciones.map((n) => (
                  <div key={n.id_notificacion} className="list-group-item small">
                    <div className="d-flex justify-content-between">
                      <strong>{n.asunto}</strong>
                      <span className={`badge text-bg-${n.estado === 'ENVIADA' ? 'success' : 'danger'}`}>{n.canal}</span>
                    </div>
                    <div className="text-muted">{n.mensaje}</div>
                    <div className="text-muted">{n.destinatario} · {fecha(n.fecha)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
