from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from . import crud, schemas
from .converters import CurrencyConverter
from .database import Base, SessionLocal, engine
from .models import Revenue

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Revenue Service")


DEFAULT_RATES = {"USD": 1.0, "EUR": 1.1, "MXN": 0.058}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_converter() -> CurrencyConverter:
    return CurrencyConverter(base_currency="USD", rates=DEFAULT_RATES)


@app.post("/revenues", response_model=schemas.RevenueOut, status_code=201)
def create_revenue(
    revenue_in: schemas.RevenueCreate, db: Session = Depends(get_db)
):
    revenue = crud.create_revenue(db, revenue_in)
    return revenue


@app.get("/revenues", response_model=list[schemas.RevenueOut])
def list_revenues(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    estado: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    moneda: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return crud.list_revenues(
        db,
        start_date=start_date,
        end_date=end_date,
        estado=estado,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        moneda=moneda,
    )


@app.get("/revenues/{revenue_id}", response_model=schemas.RevenueOut)
def get_revenue(revenue_id: int, db: Session = Depends(get_db)):
    revenue = crud.get_revenue(db, revenue_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue no encontrado")
    return revenue


@app.put("/revenues/{revenue_id}", response_model=schemas.RevenueOut)
def update_revenue(
    revenue_id: int,
    revenue_in: schemas.RevenueUpdate,
    db: Session = Depends(get_db),
):
    revenue = crud.get_revenue(db, revenue_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue no encontrado")
    return crud.update_revenue(db, revenue, revenue_in)


@app.delete("/revenues/{revenue_id}", status_code=204)
def delete_revenue(revenue_id: int, db: Session = Depends(get_db)):
    revenue = crud.get_revenue(db, revenue_id)
    if not revenue:
        raise HTTPException(status_code=404, detail="Revenue no encontrado")
    crud.delete_revenue(db, revenue)
    return None


@app.get("/revenues/report", response_model=schemas.RevenueReport)
def revenue_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    estado: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    moneda: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    converter: CurrencyConverter = Depends(get_converter),
):
    revenues = crud.list_revenues(
        db,
        start_date=start_date,
        end_date=end_date,
        estado=estado,
        cliente_id=cliente_id,
        proyecto_id=proyecto_id,
        moneda=moneda,
    )
    totals = crud.summarize_revenues(revenues, converter)
    return schemas.RevenueReport(
        total_monto_neto=totals["total_monto_neto"],
        total_monto_base=totals["total_monto_base"],
        base_currency=converter.base_currency,
    )
