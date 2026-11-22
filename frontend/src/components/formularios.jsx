// Formularios de cliente y equipo, usados en varias pantallas.
import { useState } from 'react'
import { useAvisos } from '../context/AvisosContext'
import { api } from '../services/api'
import { TIPOS_EQUIPO } from '../utils/formato'
import { BotonEnviar, useFormulario } from './comunes'
import Modal from './Modal'

export function ModalCliente({ abierto, onCerrar, cliente, onGuardado }) {
  const aviso = useAvisos()
  const editando = !!cliente
  const [v, cambiar] = useFormulario({
    tipo_documento: cliente?.tipo_documento || 'CC', numero_documento: cliente?.numero_documento || '',
    nombres: cliente?.nombres || '', apellidos: cliente?.apellidos || '', telefono: cliente?.telefono || '',
    correo: cliente?.correo || '', direccion: cliente?.direccion || '',
  })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const guardar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    const datos = { ...v, correo: v.correo || null, direccion: v.direccion || null }
    try {
      const r = editando
        ? await api('clientes', `/clientes/${cliente.id_cliente}`, {
          method: 'PUT',
          body: { nombres: datos.nombres, apellidos: datos.apellidos, telefono: datos.telefono, correo: datos.correo, direccion: datos.direccion },
        })
        : await api('clientes', '/clientes', { method: 'POST', body: datos })
      aviso.ok(editando ? 'Cliente actualizado' : 'Cliente registrado')
      onGuardado?.(r)
      onCerrar()
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo={editando ? 'Editar cliente' : 'Nuevo cliente'} abierto={abierto} onCerrar={onCerrar}>
      <form onSubmit={guardar}>
        {error && <div className="alert alert-danger py-2 small">{error}</div>}
        <div className="row g-2">
          <div className="col-4">
            <label className="form-label small">Tipo doc.</label>
            <select className="form-select" value={v.tipo_documento} onChange={cambiar('tipo_documento')} disabled={editando}>
              {['CC', 'CE', 'NIT', 'TI', 'PAS'].map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="col-8">
            <label className="form-label small">Número de documento</label>
            <input className="form-control" value={v.numero_documento} onChange={cambiar('numero_documento')} required disabled={editando} />
          </div>
          <div className="col-6">
            <label className="form-label small">Nombres</label>
            <input className="form-control" value={v.nombres} onChange={cambiar('nombres')} required />
          </div>
          <div className="col-6">
            <label className="form-label small">Apellidos</label>
            <input className="form-control" value={v.apellidos} onChange={cambiar('apellidos')} required />
          </div>
          <div className="col-6">
            <label className="form-label small">Teléfono</label>
            <input className="form-control" value={v.telefono} onChange={cambiar('telefono')} required />
          </div>
          <div className="col-6">
            <label className="form-label small">Correo (opcional)</label>
            <input type="email" className="form-control" value={v.correo} onChange={cambiar('correo')} />
          </div>
          <div className="col-12">
            <label className="form-label small">Dirección (opcional)</label>
            <input className="form-control" value={v.direccion} onChange={cambiar('direccion')} />
          </div>
        </div>
        <div className="text-end mt-3">
          <button type="button" className="btn btn-light me-2" onClick={onCerrar}>Cancelar</button>
          <BotonEnviar enviando={enviando}>Guardar</BotonEnviar>
        </div>
      </form>
    </Modal>
  )
}

export function ModalEquipo({ abierto, onCerrar, idCliente, onGuardado }) {
  const aviso = useAvisos()
  const [v, cambiar] = useFormulario({ tipo_equipo: 'PORTATIL', marca: '', modelo: '', numero_serie: '', descripcion: '' })
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  const guardar = async (e) => {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      const r = await api('clientes', '/equipos', {
        method: 'POST', body: { ...v, id_cliente: Number(idCliente), descripcion: v.descripcion || null },
      })
      aviso.ok('Equipo registrado')
      onGuardado?.(r)
      onCerrar()
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Modal titulo="Registrar equipo" abierto={abierto} onCerrar={onCerrar}>
      <form onSubmit={guardar}>
        {error && <div className="alert alert-danger py-2 small">{error}</div>}
        <div className="row g-2">
          <div className="col-6">
            <label className="form-label small">Tipo</label>
            <select className="form-select" value={v.tipo_equipo} onChange={cambiar('tipo_equipo')}>
              {Object.entries(TIPOS_EQUIPO).map(([k, t]) => <option key={k} value={k}>{t}</option>)}
            </select>
          </div>
          <div className="col-6">
            <label className="form-label small">Marca</label>
            <input className="form-control" value={v.marca} onChange={cambiar('marca')} required />
          </div>
          <div className="col-6">
            <label className="form-label small">Modelo</label>
            <input className="form-control" value={v.modelo} onChange={cambiar('modelo')} required />
          </div>
          <div className="col-6">
            <label className="form-label small">Número de serie</label>
            <input className="form-control" value={v.numero_serie} onChange={cambiar('numero_serie')} required />
          </div>
          <div className="col-12">
            <label className="form-label small">Descripción (opcional)</label>
            <textarea className="form-control" rows="2" value={v.descripcion} onChange={cambiar('descripcion')} />
          </div>
        </div>
        <div className="text-end mt-3">
          <button type="button" className="btn btn-light me-2" onClick={onCerrar}>Cancelar</button>
          <BotonEnviar enviando={enviando}>Guardar</BotonEnviar>
        </div>
      </form>
    </Modal>
  )
}
