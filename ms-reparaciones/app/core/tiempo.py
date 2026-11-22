"""Fecha y hora de Colombia (UTC-5, sin horario de verano).
Se usa en vez de date.today(), que depende de la zona horaria del equipo o del contenedor."""
from datetime import date, datetime, timedelta, timezone

COLOMBIA = timezone(timedelta(hours=-5))


def hoy() -> date:
    return datetime.now(COLOMBIA).date()
