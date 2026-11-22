// Ventana modal con estilos de Bootstrap, controlada por React (sin el JavaScript de Bootstrap).
export default function Modal({ titulo, abierto, onCerrar, children, pie, tamano }) {
  if (!abierto) return null
  return (
    <>
      <div className="modal d-block" tabIndex="-1" onMouseDown={(e) => e.target === e.currentTarget && onCerrar()}>
        <div className={`modal-dialog modal-dialog-scrollable modal-dialog-centered ${tamano ? `modal-${tamano}` : ''}`}>
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">{titulo}</h5>
              <button type="button" className="btn-close" onClick={onCerrar} aria-label="Cerrar" />
            </div>
            <div className="modal-body">{children}</div>
            {pie && <div className="modal-footer">{pie}</div>}
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  )
}
