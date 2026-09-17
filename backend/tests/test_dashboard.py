from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
import pytest

from app.db.session import SessionLocal
from app.main import app
from app.models.occurrence import Occurrence
from app.models.unit import Unit
from app.services import sejusp_analytics_service as analytics


@pytest.fixture
def ocorrencias_dashboard():
    with SessionLocal() as db:
        unidade = Unit(name="UNIDADE TESTE")
        db.add(unidade)
        db.flush()
        for indice, mes, municipio, tipo in [
            (1, 1, "CAMPO GRANDE", "INCENDIO"),
            (2, 2, "CAMPO GRANDE", "INCENDIO"),
            (3, 2, "DOURADOS", "RESGATE"),
        ]:
            db.add(Occurrence(
                source=analytics.SOURCE_SCOPE,
                source_id=f"DASHBOARD-{indice}",
                opened_at=datetime(2025, mes, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")),
                type_name=tipo,
                subtype_name="SUBTIPO TESTE",
                municipality=municipio,
                unit_id=unidade.id,
            ))
        db.commit()


@pytest.mark.parametrize("params", [
    {},
    {"period": "2025-02", "type": "INCENDIO", "municipality": "CAMPO GRANDE",
     "unit": "UNIDADE TESTE", "subtype": "SUBTIPO TESTE", "shift": "Manhã"},
])
def test_dashboard_matches_existing_endpoints(ocorrencias_dashboard, params):
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard", params=params)
        assert response.status_code == 200
        dashboard = response.json()
        for painel in ["filters", "overview", "monthly", "types", "cities", "hours", "units", "shifts"]:
            individual = client.get(f"/api/v1/analytics/{painel}", params=params)
            assert individual.status_code == 200
            assert dashboard[painel] == individual.json()
        # O SLA existente e global, nao um indicador novo do recorte filtrado.
        assert dashboard["sla"] == client.get("/api/v1/analytics/sla").json()


def test_dashboard_handles_empty_database():
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        dashboard = response.json()
        assert dashboard["overview"]["total"] == 0
        assert dashboard["monthly"]["items"] == []
        assert dashboard["types"]["items"] == []
        assert dashboard["hours"]["items"] == [0] * 24
        assert dashboard["sla"]["sample_size"] == 0


@pytest.mark.parametrize("params,field", [
    ({"source": "demo"}, "source"),
    ({"fonte": "invalida"}, "source"),
    ({"period": "ano-1900"}, "period"),
])
def test_dashboard_rejects_invalid_filters(params, field):
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard", params=params)
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["code"] == "INVALID_FILTER"
        assert detail["errors"][0]["field"] == field


def test_dashboard_reads_dataset_signature_once(ocorrencias_dashboard, monkeypatch):
    consultas = []
    original = analytics._dataset_signature

    def contar(db):
        consultas.append(1)
        return original(db)

    monkeypatch.setattr(analytics, "_dataset_signature", contar)
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        assert response.json()["overview"]["total"] == 3
    assert len(consultas) == 1


def test_dataset_snapshot_is_released_after_error(ocorrencias_dashboard):
    with SessionLocal() as db:
        with pytest.raises(RuntimeError, match="erro de teste"):
            with analytics.dataset_snapshot(db):
                assert len(analytics._rows(db)) == 3
                raise RuntimeError("erro de teste")
        db.add(Occurrence(
            source=analytics.SOURCE_SCOPE,
            source_id="DASHBOARD-NOVA",
            opened_at=datetime(2025, 2, 11, 9),
            type_name="RESGATE",
            municipality="DOURADOS",
        ))
        db.commit()
        assert len(analytics._rows(db)) == 4
