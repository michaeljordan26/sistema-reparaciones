
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = (
        # RN01: todo cliente se identifica de manera única
        UniqueConstraint("tipo_documento", "numero_documento", name="uq_cliente_documento"),
        CheckConstraint("tipo_documento IN ('CC','CE','NIT','TI','PAS')", name="ck_cliente_tipo_doc"),
        CheckConstraint("estado IN ('ACTIVO','INACTIVO')", name="ck_cliente_estado"),
    )

    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    tipo_documento: Mapped[str] = mapped_column(String(5))
    numero_documento: Mapped[str] = mapped_column(String(20), index=True)
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str] = mapped_column(String(80))
    telefono: Mapped[str] = mapped_column(String(20))
    correo: Mapped[str | None] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(150))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    estado: Mapped[str] = mapped_column(String(10), default="ACTIVO")

    equipos: Mapped[list["Equipo"]] = relationship(back_populates="cliente", order_by="Equipo.id_equipo")


class Equipo(Base):
    __tablename__ = "equipo"
    __table_args__ = (
        CheckConstraint("tipo_equipo IN ('PORTATIL','ESCRITORIO','TODO_EN_UNO','IMPRESORA','TABLET','SERVIDOR','OTRO')",
                        name="ck_equipo_tipo"),
        CheckConstraint("estado IN ('ACTIVO','INACTIVO')", name="ck_equipo_estado"),
    )

    id_equipo: Mapped[int] = mapped_column(primary_key=True)
    # RN02: cada equipo pertenece a un solo cliente. RESTRICT: no se borra un cliente con equipos.
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente", ondelete="RESTRICT"), index=True)
    tipo_equipo: Mapped[str] = mapped_column(String(20))
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(80))
    numero_serie: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(String(300))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    estado: Mapped[str] = mapped_column(String(10), default="ACTIVO")

    cliente: Mapped[Cliente] = relationship(back_populates="equipos")
