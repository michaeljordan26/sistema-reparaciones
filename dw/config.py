"""Configuración común del Sprint 7 (Data Warehouse y ETL).

Lee las credenciales del archivo .env de la carpeta raíz (el mismo de Docker Compose),
así ninguna contraseña queda escrita en el código.
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _leer_env(ruta: Path) -> dict:
    valores = {}
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


_ENV = _leer_env(RAIZ / ".env")


def var(nombre: str, defecto: str) -> str:
    """Primero la variable de entorno, luego el .env de la raíz, luego el valor por defecto."""
    return os.environ.get(nombre) or _ENV.get(nombre) or defecto


HOST = var("DB_HOST", "localhost")
USUARIO = var("DB_USER", "taller")
CLAVE = var("DB_PASSWORD", "taller123")


def url(base: str, puerto: int) -> str:
    return f"postgresql+psycopg://{USUARIO}:{CLAVE}@{HOST}:{puerto}/{base}"


# Bases OLTP (origen). Mismos puertos que publica docker-compose.yml en el PC.
ORIGENES = {
    "usuarios": url("db_usuarios", int(var("PUERTO_USUARIOS", "5432"))),
    "clientes": url("db_clientes", int(var("PUERTO_CLIENTES", "5433"))),
    "ordenes": url("db_ordenes", int(var("PUERTO_ORDENES", "5434"))),
    "reparaciones": url("db_reparaciones", int(var("PUERTO_REPARACIONES", "5435"))),
    "inventario": url("db_inventario", int(var("PUERTO_INVENTARIO", "5436"))),
    "facturacion": url("db_facturacion", int(var("PUERTO_FACTURACION", "5437"))),
    "reportes": url("db_reportes", int(var("PUERTO_REPORTES", "5438"))),
}

# Data Warehouse (destino): contenedor db-dw de docker-compose.yml
DW = url("db_dw", int(var("PUERTO_DW", "5439")))

# APIs (solo las usa generar_historico.py)
API = {
    "usuarios": var("USUARIOS_URL", "http://localhost:8001"),
    "clientes": var("CLIENTES_URL", "http://localhost:8002"),
    "ordenes": var("ORDENES_URL", "http://localhost:8003"),
    "reparaciones": var("REPARACIONES_URL", "http://localhost:8004"),
    "inventario": var("INVENTARIO_URL", "http://localhost:8005"),
    "facturacion": var("FACTURACION_URL", "http://localhost:8006"),
}

# Usuarios de prueba que crea ms-usuarios (seed.py)
CREDENCIALES = {
    "admin": var("ADMIN_PASSWORD", "Admin123*"),
    "recepcion": var("CLAVE_RECEPCION", "Recepcion123*"),
    "tecnico1": var("CLAVE_TECNICO", "Tecnico123*"),
    "tecnico2": var("CLAVE_TECNICO", "Tecnico123*"),
    "caja": var("CLAVE_CAJA", "Caja1234*"),
    "inventario": var("CLAVE_INVENTARIO", "Inventario123*"),
}
