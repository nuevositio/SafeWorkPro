from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator


class RevenueBase(BaseModel):
    cliente_id: int = Field(..., ge=1)
    proyecto_id: int = Field(..., ge=1)
    estado: str = Field(..., min_length=1)
    fecha_cobro: date
    monto_bruto: float = Field(..., ge=0)
    impuestos: float = Field(0, ge=0)
    descuentos: float = Field(0, ge=0)
    moneda: str = Field(..., min_length=1)

    @validator("descuentos")
    def validate_descuentos(cls, value, values):  # type: ignore[override]
        monto_bruto = values.get("monto_bruto", 0)
        impuestos = values.get("impuestos", 0)
        if value > monto_bruto + impuestos:
            raise ValueError("El descuento no puede ser mayor al monto bruto más impuestos")
        return value


class RevenueCreate(RevenueBase):
    pass


class RevenueUpdate(BaseModel):
    cliente_id: Optional[int] = Field(None, ge=1)
    proyecto_id: Optional[int] = Field(None, ge=1)
    estado: Optional[str] = Field(None, min_length=1)
    fecha_cobro: Optional[date]
    monto_bruto: Optional[float] = Field(None, ge=0)
    impuestos: Optional[float] = Field(None, ge=0)
    descuentos: Optional[float] = Field(None, ge=0)
    moneda: Optional[str] = Field(None, min_length=1)


class RevenueOut(RevenueBase):
    id: int
    monto_neto: float

    class Config:
        from_attributes = True


class RevenueReport(BaseModel):
    total_monto_neto: float
    total_monto_base: float
    base_currency: str
