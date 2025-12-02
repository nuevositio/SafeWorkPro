from __future__ import annotations

from sqlalchemy import Column, Date, Float, Index, Integer, String

from .database import Base


class Revenue(Base):
    __tablename__ = "revenues"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, nullable=False, index=True)
    proyecto_id = Column(Integer, nullable=False, index=True)
    estado = Column(String(50), nullable=False, index=True)
    fecha_cobro = Column(Date, nullable=False, index=True)
    monto_bruto = Column(Float, nullable=False)
    impuestos = Column(Float, default=0.0)
    descuentos = Column(Float, default=0.0)
    moneda = Column(String(10), nullable=False)

    __table_args__ = (
        Index("ix_revenues_cliente_id", "cliente_id"),
        Index("ix_revenues_proyecto_id", "proyecto_id"),
        Index("ix_revenues_estado", "estado"),
        Index("ix_revenues_fecha_cobro", "fecha_cobro"),
    )

    @property
    def monto_neto(self) -> float:
        return float(self.monto_bruto - self.impuestos - self.descuentos)
