# Interfaz web – React + Vite + Bootstrap

Una sola aplicación web que habla con los siete microservicios. Cada usuario ve un menú y unas
acciones distintas según su rol.

- URL: **http://localhost:5173**
- Tecnologías: React 18, React Router 6, Bootstrap 5.3, Bootstrap Icons, Vite 5

## Cómo se comunica con el backend

El navegador **no** llama a los puertos 8001-8007. Llama a rutas como `/api/ordenes/...` y un
**proxy** las reenvía al microservicio:

| Ruta en el navegador | Microservicio |
|---|---|
| /api/usuarios/... | ms-usuarios :8001 |
| /api/clientes/... | ms-clientes :8002 |
| /api/ordenes/... | ms-ordenes :8003 |
| /api/reparaciones/... | ms-reparaciones :8004 |
| /api/inventario/... | ms-inventario :8005 |
| /api/facturacion/... | ms-facturacion :8006 |
| /api/reportes/... | ms-reportes :8007 |

En desarrollo el proxy es Vite (`vite.config.js`). En Docker es nginx (`nginx.conf`). Así no hay
problemas de CORS y el frontend no necesita saber en qué puerto está cada servicio.

## Estructura

```
frontend/
├── index.html
├── vite.config.js              # Proxy hacia los 7 microservicios
├── nginx.conf / Dockerfile     # Versión para Docker
└── src/
    ├── main.jsx                # Punto de entrada
    ├── App.jsx                 # Rutas y protección por rol
    ├── config.js               # Rutas base de cada servicio
    ├── styles.css
    ├── services/api.js         # Cliente HTTP: token, errores legibles
    ├── context/
    │   ├── AuthContext.jsx     # Sesión, usuario y roles
    │   └── AvisosContext.jsx   # Mensajes emergentes
    ├── components/
    │   ├── Layout.jsx          # Menú lateral según el rol
    │   ├── comunes.jsx         # Insignias, tarjetas, hooks de carga y formularios
    │   ├── formularios.jsx     # Cliente y equipo
    │   ├── Modal.jsx
    │   └── orden/Secciones.jsx # Diagnóstico, presupuesto, reparación, factura, garantía
    └── pages/                  # Una pantalla por archivo
```

## Pantallas y roles

| Pantalla | Admin | Recepción | Técnico | Caja | Inventario |
|---|:-:|:-:|:-:|:-:|:-:|
| Inicio (tablero según el rol) | ✔ | ✔ | ✔ | ✔ | ✔ |
| Órdenes y detalle de la orden | ✔ | ✔ | ✔ (mis órdenes) | ✔ | |
| Nueva orden | ✔ | ✔ | | | |
| Clientes y equipos | ✔ | ✔ | | | |
| Inventario | ✔ | | consulta | | ✔ |
| Facturación (facturas, cartera, ingresos) | ✔ | | | ✔ | |
| Garantías y reclamaciones | ✔ | ✔ | | | |
| Usuarios y técnicos | ✔ | | | | |
| Auditoría | ✔ | | | | |

El **detalle de la orden** es la pantalla central. Muestra la barra de progreso, el siguiente paso,
el historial, las notificaciones y, según el estado y el rol, el formulario que corresponde:
diagnóstico (técnico asignado), presupuesto, respuesta del cliente (recepción o caja), reparación con
repuestos (técnico), factura y pagos (caja), y entrega (recepción, solo si el saldo es 0).

La interfaz oculta lo que el usuario no puede hacer, pero **la seguridad real está en el backend**:
aunque alguien llame a la API directamente, cada microservicio vuelve a verificar el rol.

## Ejecutar en Windows

Requisitos: Node.js 22 (`node --version`) y los siete microservicios encendidos.

```bat
cd C:\Users\MAICOL\sistema-reparaciones\frontend
npm install
npm run dev
```

O simplemente `iniciar.bat`, que instala las dependencias la primera vez, abre la interfaz y el navegador.

## Compilar para producción

```bat
npm run build
```

Genera la carpeta `dist/`, que en Docker sirve nginx.
