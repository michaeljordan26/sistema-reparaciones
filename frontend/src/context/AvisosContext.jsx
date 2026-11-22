// Mensajes emergentes (toasts) de éxito o error.
import { createContext, useCallback, useContext, useState } from 'react'

const AvisosContext = createContext(null)

export function AvisosProvider({ children }) {
  const [avisos, setAvisos] = useState([])

  const quitar = (id) => setAvisos((a) => a.filter((x) => x.id !== id))
  const agregar = useCallback((tipo, texto) => {
    const id = Date.now() + Math.random()
    setAvisos((a) => [...a, { id, tipo, texto }])
    setTimeout(() => quitar(id), tipo === 'danger' ? 7000 : 3500)
  }, [])

  const valor = {
    ok: useCallback((t) => agregar('success', t), [agregar]),
    error: useCallback((t) => agregar('danger', t), [agregar]),
  }

  return (
    <AvisosContext.Provider value={valor}>
      {children}
      <div className="toast-container position-fixed top-0 end-0 p-3" style={{ zIndex: 2000 }}>
        {avisos.map((a) => (
          <div key={a.id} className={`toast show align-items-center text-bg-${a.tipo} border-0`} role="alert">
            <div className="d-flex">
              <div className="toast-body">
                <i className={`bi ${a.tipo === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'} me-2`} />
                {a.texto}
              </div>
              <button type="button" className="btn-close btn-close-white me-2 m-auto" onClick={() => quitar(a.id)} />
            </div>
          </div>
        ))}
      </div>
    </AvisosContext.Provider>
  )
}

export const useAvisos = () => useContext(AvisosContext)
