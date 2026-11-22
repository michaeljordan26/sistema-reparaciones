// Configuración de Vite.
// El navegador NUNCA llama directo a los puertos 8001-8007: llama a /api/<servicio>/...
// y este proxy reenvía la petición al microservicio. Así no hay problemas de CORS.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const SERVICIOS = {
  usuarios: 8001, clientes: 8002, ordenes: 8003, reparaciones: 8004,
  inventario: 8005, facturacion: 8006, reportes: 8007,
}

const proxy = Object.fromEntries(
  Object.entries(SERVICIOS).map(([nombre, puerto]) => [
    `/api/${nombre}`,
    {
      target: `http://127.0.0.1:${puerto}`,
      changeOrigin: true,
      rewrite: (ruta) => ruta.replace(`/api/${nombre}`, ''),
    },
  ]),
)

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true, proxy },
})
