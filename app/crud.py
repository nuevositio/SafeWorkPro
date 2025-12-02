from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .converters import CurrencyConverter
from .models import Revenue
from .schemas import RevenueCreate, RevenueUpdate


def create_revenue(db: Session, revenue_in: RevenueCreate) -> Revenue:
    revenue = Revenue(**revenue_in.dict())
    db.add(revenue)
    db.commit()
    db.refresh(revenue)
    return revenue


def get_revenue(db: Session, revenue_id: int) -> Optional[Revenue]:
    return db.get(Revenue, revenue_id)


def delete_revenue(db: Session, revenue: Revenue) -> None:
    db.delete(revenue)
    db.commit()


def update_revenue(db: Session, revenue: Revenue, revenue_in: RevenueUpdate) -> Revenue:
    for field, value in revenue_in.dict(exclude_unset=True).items():
        setattr(revenue, field, value)
    db.add(revenue)
    db.commit()
    db.refresh(revenue)
    return revenue


def _build_filters(
    start_date: Optional[date],
    end_date: Optional[date],
    estado: Optional[str],
    cliente_id: Optional[int],
    proyecto_id: Optional[int],
    moneda: Optional[str],
):
    filters: Iterable = []
    if start_date:
        filters = (*filters, Revenue.fecha_cobro >= start_date)
    if end_date:
        filters = (*filters, Revenue.fecha_cobro <= end_date)
    if estado:
        filters = (*filters, Revenue.estado == estado)
    if cliente_id:
        filters = (*filters, Revenue.cliente_id == cliente_id)
    if proyecto_id:
        filters = (*filters, Revenue.proyecto_id == proyecto_id)
    if moneda:
        filters = (*filters, Revenue.moneda == moneda)
    return filters


def list_revenues(
    db: Session,
    *,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    estado: Optional[str] = None,
    cliente_id: Optional[int] = None,
    proyecto_id: Optional[int] = None,
    moneda: Optional[str] = None,
) -> List[Revenue]:
    filters = _build_filters(start_date, end_date, estado, cliente_id, proyecto_id, moneda)
    stmt = select(Revenue)
    if filters:
        stmt = stmt.where(and_(*filters))
    return list(db.scalars(stmt).all())


def summarize_revenues(
    revenues: List[Revenue], converter: CurrencyConverter
) -> dict[str, float]:
    total_neto = 0.0
    total_base = 0.0
    for revenue in revenues:
        neto = revenue.monto_neto
        total_neto += neto
        total_base += converter.convert_to_base(neto, revenue.moneda)
    return {"total_monto_neto": total_neto, "total_monto_base": total_base}
