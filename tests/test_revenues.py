from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.converters import CurrencyConverter
from app.database import Base
from app.main import app, get_converter, get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_converter():
    return CurrencyConverter(base_currency="USD", rates={"USD": 1, "EUR": 1.2, "MXN": 0.05})


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_converter] = override_converter

client = TestClient(app)


def _create_payload(**kwargs):
    payload = {
        "cliente_id": 1,
        "proyecto_id": 1,
        "estado": "pendiente",
        "fecha_cobro": date(2024, 1, 10).isoformat(),
        "monto_bruto": 1000,
        "impuestos": 50,
        "descuentos": 20,
        "moneda": "USD",
    }
    payload.update(kwargs)
    return payload


def test_create_and_get_revenue():
    response = client.post("/revenues", json=_create_payload())
    assert response.status_code == 201
    revenue = response.json()
    assert revenue["monto_neto"] == 930

    get_response = client.get(f"/revenues/{revenue['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == revenue["id"]
    assert fetched["monto_neto"] == revenue["monto_neto"]


def test_filters_and_listing():
    client.post("/revenues", json=_create_payload(estado="pagado", cliente_id=5, proyecto_id=9))
    client.post("/revenues", json=_create_payload(estado="pendiente", cliente_id=6, proyecto_id=10, fecha_cobro=date(2024, 2, 1).isoformat()))

    filtered = client.get("/revenues", params={"estado": "pagado", "cliente_id": 5}).json()
    assert len(filtered) == 1
    assert filtered[0]["estado"] == "pagado"

    date_filtered = client.get(
        "/revenues",
        params={"start_date": date(2024, 2, 1).isoformat(), "end_date": date(2024, 2, 28).isoformat()},
    ).json()
    assert len(date_filtered) == 1
    assert date_filtered[0]["fecha_cobro"] == date(2024, 2, 1).isoformat()


def test_update_and_delete_revenue():
    created = client.post("/revenues", json=_create_payload(estado="pendiente")).json()
    update_resp = client.put(
        f"/revenues/{created['id']}", json={"estado": "pagado", "descuentos": 10}
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["estado"] == "pagado"
    assert updated["monto_neto"] == 940

    delete_resp = client.delete(f"/revenues/{created['id']}")
    assert delete_resp.status_code == 204
    missing = client.get(f"/revenues/{created['id']}")
    assert missing.status_code == 404


def test_report_conversion_to_base_currency():
    client.post("/revenues", json=_create_payload(monto_bruto=100, impuestos=10, descuentos=0, moneda="USD"))
    client.post(
        "/revenues",
        json=_create_payload(monto_bruto=200, impuestos=0, descuentos=20, moneda="EUR", fecha_cobro=date(2024, 3, 3).isoformat()),
    )
    client.post(
        "/revenues",
        json=_create_payload(monto_bruto=5000, impuestos=0, descuentos=0, moneda="MXN", fecha_cobro=date(2024, 3, 15).isoformat()),
    )

    report = client.get("/revenues/report").json()
    # net amounts: USD 90, EUR 180, MXN 5000
    expected_base = 90 * 1 + 180 * 1.2 + 5000 * 0.05
    assert report["total_monto_neto"] == 90 + 180 + 5000
    assert report["total_monto_base"] == expected_base
    assert report["base_currency"] == "USD"
