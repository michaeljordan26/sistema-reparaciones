// Catálogos de clientes y equipos (para mostrar nombres en las listas de órdenes y facturas).
import { useEffect, useState } from 'react'
import { api } from './services/api'

export function useCatalogos(activo = true) {
  const [cat, setCat] = useState({ clientes: {}, equipos: {} })
  useEffect(() => {
    if (!activo) return
    Promise.all([
      api('clientes', '/clientes', { query: { solo_activos: false } }),
      api('clientes', '/equipos'),
    ]).then(([clientes, equipos]) => {
      setCat({
        clientes: Object.fromEntries(clientes.map((c) => [c.id_cliente, c])),
        equipos: Object.fromEntries(equipos.map((e) => [e.id_equipo, e])),
      })
    }).catch(() => { /* las listas funcionan igual, solo sin nombres */ })
  }, [activo])
  return cat
}
