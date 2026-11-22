// Cliente HTTP único para todos los microservicios.
// Agrega el token, arma la URL y convierte los errores del backend en mensajes legibles.
import { NOMBRE_SERVICIO, SERVICIOS } from '../config'

let token = null
let alExpirarSesion = null

export function setToken(nuevo) {
  token = nuevo
}

export function onSesionExpirada(fn) {
  alExpirarSesion = fn
}

export class ApiError extends Error {
  constructor(status, mensaje) {
    super(mensaje)
    this.status = status
  }
}

function mensajeDe(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    // Errores 422 de validación de Pydantic
    return detail
      .map((d) => {
        const campo = (d.loc || []).filter((x) => x !== 'body').join('.')
        const msg = String(d.msg || '').replace('Value error, ', '')
        return campo ? `${campo}: ${msg}` : msg
      })
      .join(' · ')
  }
  return JSON.stringify(detail)
}

export async function api(servicio, ruta, { method = 'GET', body, form, query } = {}) {
  let url = `${SERVICIOS[servicio]}${ruta}`
  if (query) {
    const q = new URLSearchParams(
      Object.entries(query).filter(([, v]) => v !== undefined && v !== null && v !== ''),
    )
    if (q.toString()) url += `?${q}`
  }
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let cuerpo
  if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    cuerpo = new URLSearchParams(form)
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    cuerpo = JSON.stringify(body)
  }

  let respuesta
  try {
    respuesta = await fetch(url, { method, headers, body: cuerpo })
  } catch {
    throw new ApiError(0, `No hay conexión con el servicio de ${NOMBRE_SERVICIO[servicio]}.`)
  }

  let datos = null
  try {
    datos = await respuesta.json()
  } catch {
    datos = null
  }

  if (!respuesta.ok) {
    if (respuesta.status === 401 && token && ruta !== '/auth/login') alExpirarSesion?.()
    if (respuesta.status >= 500 && !datos) {
      throw new ApiError(respuesta.status,
        `El servicio de ${NOMBRE_SERVICIO[servicio]} no responde. ¿Está encendida su ventana?`)
    }
    throw new ApiError(respuesta.status, mensajeDe(datos?.detail) || `Error ${respuesta.status}`)
  }
  return datos
}

// Igual que api(), pero devuelve null si el recurso no existe (404)
export async function apiOpcional(servicio, ruta, opciones) {
  try {
    return await api(servicio, ruta, opciones)
  } catch (e) {
    if (e.status === 404) return null
    throw e
  }
}
