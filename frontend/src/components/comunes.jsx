// Componentes pequeños reutilizados en todas las pantallas.
import { useCallback, useEffect, useState } from 'react'
import { ESTADOS_ORDEN, PRIORIDADES } from '../utils/formato'

export function Cargando({ texto = 'Cargando...' }) {
  return (
    <div className="text-center text-muted py-5">
      <div className="spinner-border spinner-border-sm me-2" role="status" />
      {texto}
    </div>
  )
}

export function ErrorAlerta({ error, onReintentar }) {
  if (!error) return null
  return (
    <div className="alert alert-danger d-flex align-items-center justify-content-between">
      <span><i className="bi bi-exclamation-octagon me-2" />{error}</span>
      {onReintentar && <button className="btn btn-sm btn-outline-danger" onClick={onReintentar}>Reintentar</button>}
    </div>
  )
}

export function EstadoOrden({ estado }) {
  const e = ESTADOS_ORDEN[estado] || { texto: estado, color: 'secondary', icono: 'circle' }
  return <span className={`badge text-bg-${e.color}`}><i className={`bi bi-${e.icono} me-1`} />{e.texto}</span>
}

export function Prioridad({ valor }) {
  return <span className={`badge rounded-pill border border-${PRIORIDADES[valor] || 'secondary'} text-${PRIORIDADES[valor] || 'secondary'}`}>{valor}</span>
}

export function Insignia({ texto, color = 'secondary' }) {
  return <span className={`badge text-bg-${color}`}>{texto}</span>
}

export function Vacio({ texto, icono = 'inbox' }) {
  return (
    <div className="text-center text-muted py-4">
      <i className={`bi bi-${icono} fs-2 d-block mb-2`} />
      {texto}
    </div>
  )
}

export function Encabezado({ titulo, subtitulo, icono, children }) {
  return (
    <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-4">
      <div>
        <h1 className="h3 mb-0">{icono && <i className={`bi bi-${icono} me-2 text-primary`} />}{titulo}</h1>
        {subtitulo && <div className="text-muted small">{subtitulo}</div>}
      </div>
      <div className="d-flex gap-2">{children}</div>
    </div>
  )
}

export function Kpi({ titulo, valor, icono, color = 'primary', detalle }) {
  return (
    <div className="card h-100 shadow-sm border-0 kpi">
      <div className="card-body d-flex align-items-center gap-3">
        <div className={`kpi-icono bg-${color}-subtle text-${color}`}><i className={`bi bi-${icono}`} /></div>
        <div>
          <div className="text-muted small">{titulo}</div>
          <div className="fs-4 fw-semibold">{valor}</div>
          {detalle && <div className="small text-muted">{detalle}</div>}
        </div>
      </div>
    </div>
  )
}

// Botón que pide una segunda confirmación (sin ventanas emergentes del navegador)
export function BotonConfirmar({ children, onConfirmar, className = 'btn btn-outline-danger btn-sm', texto = '¿Seguro?', disabled }) {
  const [pidiendo, setPidiendo] = useState(false)
  if (!pidiendo) {
    return <button type="button" className={className} disabled={disabled} onClick={() => setPidiendo(true)}>{children}</button>
  }
  return (
    <span className="d-inline-flex gap-1 align-items-center">
      <span className="small text-muted">{texto}</span>
      <button type="button" className="btn btn-danger btn-sm" onClick={() => { setPidiendo(false); onConfirmar() }}>Sí</button>
      <button type="button" className="btn btn-light btn-sm" onClick={() => setPidiendo(false)}>No</button>
    </span>
  )
}

export function BotonEnviar({ enviando, children, className = 'btn btn-primary', ...resto }) {
  return (
    <button type="submit" className={className} disabled={enviando} {...resto}>
      {enviando && <span className="spinner-border spinner-border-sm me-2" />}
      {children}
    </button>
  )
}

// Carga datos al montar y permite recargar: const { datos, cargando, error, recargar } = useCarga(fn, [deps])
export function useCarga(funcion, dependencias = []) {
  const [estado, setEstado] = useState({ datos: null, cargando: true, error: null })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const recargar = useCallback(async () => {
    setEstado((e) => ({ ...e, cargando: true }))
    try {
      const datos = await funcion()
      setEstado({ datos, cargando: false, error: null })
    } catch (err) {
      setEstado({ datos: null, cargando: false, error: err.message })
    }
  }, dependencias)
  useEffect(() => { recargar() }, [recargar])
  return { ...estado, recargar }
}

// Manejo de formularios: const [v, cambiar, setV] = useFormulario({ nombre: '' })
export function useFormulario(inicial) {
  const [valores, setValores] = useState(inicial)
  const cambiar = (campo) => (e) => {
    const valor = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setValores((v) => ({ ...v, [campo]: valor }))
  }
  return [valores, cambiar, setValores]
}
