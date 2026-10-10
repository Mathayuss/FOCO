from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
import pytest

from app.db.session import SessionLocal
from app.main import app
from app.models.occurrence import Occurrence
from app.models.unit import Unit
from app.services import dashboard_service
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
    {"period": "2025-02"},
    {"type": "RESGATE"},
    {"municipality": "DOURADOS"},
    {"unit": "UNIDADE TESTE"},
    {"subtype": "SUBTIPO TESTE"},
    {"shift": "Noite"},
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


def test_dashboard_empty_slice_has_no_top_demand(ocorrencias_dashboard):
    with TestClient(app) as client:
        params = {"period": "2025-01", "type": "RESGATE", "municipality": "DOURADOS"}
        empty = client.get("/api/v1/analytics/dashboard", params=params)
        assert empty.status_code == 200
        overview = empty.json()["overview"]
        assert overview["total"] == 0
        assert overview["applied_filters"]["type"] == "RESGATE"
        assert overview["applied_filters"]["municipality"] == "DOURADOS"
        assert overview["top_type"] == ""
        assert overview["top_municipality"] == ""

        params["period"] = "2025-02"
        populated = client.get("/api/v1/analytics/dashboard", params=params)
        assert populated.status_code == 200
        overview = populated.json()["overview"]
        assert overview["total"] == 1
        assert overview["top_type"] == "RESGATE"
        assert overview["top_municipality"] == "DOURADOS"


def test_dashboard_zero_baseline_has_no_percentage():
    with SessionLocal() as db:
        for year, month, type_name in [(2024, 2, "OUTRO"), (2025, 1, "OUTRO"), (2025, 2, "OUTRO"), (2025, 3, "ALVO")]:
            db.add(Occurrence(
                source=analytics.SOURCE_SCOPE,
                source_id=f"COMPARACAO-ZERO-{year}-{month}",
                opened_at=datetime(year, month, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")),
                type_name=type_name,
                municipality="MUNICIPIO TESTE",
            ))
        db.commit()

    with TestClient(app) as client:
        params = {"period": "2025-02", "type": "ALVO"}
        response = client.get("/api/v1/analytics/dashboard", params=params)
        assert response.status_code == 200
        dashboard = response.json()
        comparison = dashboard["overview"]["comparison"]
        assert comparison["available"] is True
        assert comparison["current_total"] == 0
        assert comparison["baseline_total"] == 0
        assert comparison["delta_abs"] == 0
        assert comparison["delta_pct"] is None
        assert dashboard["overview"]["delta_pct"] is None
        assert comparison["reason"] == "A base anterior não possui ocorrências para calcular a variação percentual."
        assert dashboard["monthly"]["comparison"] == [{
            "current_month": "Fev/2025", "baseline_month": "Fev/2024",
            "current": 0, "baseline": 0, "delta": 0,
        }]


def test_dashboard_compares_year_with_equivalent_months_from_previous_year():
    with SessionLocal() as db:
        for year, last_month, occurrences_per_month in [(2025, 6, 1), (2026, 8, 2)]:
            for month in range(1, last_month + 1):
                for sequence in range(occurrences_per_month):
                    db.add(Occurrence(
                        source=analytics.SOURCE_SCOPE,
                        source_id=f"COMPARACAO-ANUAL-{year}-{month}-{sequence}",
                        opened_at=datetime(year, month, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")),
                        registered_at=datetime(year, month, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")),
                        type_name="TIPO TESTE",
                        municipality="MUNICIPIO TESTE",
                    ))
        db.commit()

    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard", params={"period": "ano-2026"})

    assert response.status_code == 200
    dashboard = response.json()
    comparison = dashboard["overview"]["comparison"]
    assert dashboard["overview"]["total"] == 16
    assert comparison == {
        "available": True,
        "current_label": "Jan-Jun/2026",
        "baseline_label": "Jan-Jun/2025",
        "current_total": 12,
        "baseline_total": 6,
        "delta_abs": 6,
        "delta_pct": 100.0,
        "reason": "Comparação limitada aos meses equivalentes com cobertura nos dois anos: Jan-Jun.",
        "source_scope": "sejusp_importado",
    }
    assert len(dashboard["monthly"]["items"]) == 8
    assert len(dashboard["monthly"]["comparison"]) == 6
    assert dashboard["monthly"]["comparison"][-1] == {
        "current_month": "Jun/2026",
        "baseline_month": "Jun/2025",
        "current": 2,
        "baseline": 1,
        "delta": 1,
    }


def test_dashboard_compares_month_with_same_month_from_previous_year():
    with SessionLocal() as db:
        for year, month, total in [(2025, 2, 1), (2026, 1, 7), (2026, 2, 3)]:
            for sequence in range(total):
                db.add(Occurrence(
                    source=analytics.SOURCE_SCOPE,
                    source_id=f"COMPARACAO-MENSAL-{year}-{month}-{sequence}",
                    opened_at=datetime(year, month, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")),
                    registered_at=datetime(year, month, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")),
                    type_name="TIPO TESTE",
                    municipality="MUNICIPIO TESTE",
                ))
        db.commit()

    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard", params={"period": "2026-02"})

    assert response.status_code == 200
    comparison = response.json()["overview"]["comparison"]
    assert comparison["current_label"] == "Fev/2026"
    assert comparison["baseline_label"] == "Fev/2025"
    assert comparison["current_total"] == 3
    assert comparison["baseline_total"] == 1
    assert comparison["delta_abs"] == 2
    assert comparison["delta_pct"] == 200.0


def test_dashboard_compares_custom_date_range_with_same_dates_from_previous_year():
    dates = [
        (datetime(2025, 1, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
        (datetime(2025, 1, 20, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
        (datetime(2025, 2, 5, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
        (datetime(2025, 2, 20, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
        (datetime(2026, 1, 10, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
        (datetime(2026, 1, 20, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 2),
        (datetime(2026, 2, 5, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
        (datetime(2026, 2, 20, 9, tzinfo=ZoneInfo("America/Campo_Grande")), 1),
    ]
    with SessionLocal() as db:
        for date_value, total in dates:
            for sequence in range(total):
                db.add(Occurrence(
                    source=analytics.SOURCE_SCOPE,
                    source_id=f"COMPARACAO-FAIXA-{date_value.date()}-{sequence}",
                    opened_at=date_value,
                    registered_at=date_value,
                    type_name="TIPO TESTE",
                    municipality="MUNICIPIO TESTE",
                ))
        db.commit()

    period = "faixa-2026-01-15--2026-02-10"
    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/dashboard", params={"period": period})

    assert response.status_code == 200
    dashboard = response.json()
    comparison = dashboard["overview"]["comparison"]
    assert dashboard["overview"]["total"] == 3
    assert dashboard["overview"]["applied_filters"]["period"] == "15/01/2026 a 10/02/2026"
    assert comparison["available"] is True
    assert comparison["current_label"] == "15/01/2026 a 10/02/2026"
    assert comparison["baseline_label"] == "15/01/2025 a 10/02/2025"
    assert comparison["current_total"] == 3
    assert comparison["baseline_total"] == 2
    assert comparison["delta_abs"] == 1
    assert comparison["delta_pct"] == 50.0
    assert dashboard["monthly"]["comparison"] == [
        {"current_month": "Jan/2026", "baseline_month": "Jan/2025", "current": 2, "baseline": 1, "delta": 1},
        {"current_month": "Fev/2026", "baseline_month": "Fev/2025", "current": 1, "baseline": 1, "delta": 0},
    ]


@pytest.mark.parametrize("params,field", [
    ({"source": "demo"}, "source"),
    ({"fonte": "invalida"}, "source"),
    ({"period": "ano-1900"}, "period"),
    ({"period": "faixa-2026-03-10--2026-03-01"}, "period"),
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


def test_dashboard_reuses_periods_and_filtered_rows(ocorrencias_dashboard, monkeypatch):
    chamadas = {"periodos": 0, "filtros": 0}
    periodos_original = analytics._period_defs
    filtros_original = analytics._filtered_rows

    def periodos(*args, **kwargs):
        chamadas["periodos"] += 1
        return periodos_original(*args, **kwargs)

    def filtros(*args, **kwargs):
        chamadas["filtros"] += 1
        return filtros_original(*args, **kwargs)

    monkeypatch.setattr(analytics, "_period_defs", periodos)
    monkeypatch.setattr(analytics, "_filtered_rows", filtros)
    with SessionLocal() as db:
        with analytics.dataset_snapshot(db):
            assert analytics.validate_filter_params(db, period="all") == []
            resultado = dashboard_service.snapshot(db, period="all")
    assert resultado["overview"]["total"] == 3
    assert chamadas == {"periodos": 1, "filtros": 1}


def test_filter_metadata_is_built_once_per_selection(ocorrencias_dashboard, monkeypatch):
    chamadas = []
    original = analytics._build_filter_metadata

    def contar(*args, **kwargs):
        chamadas.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(analytics, "_build_filter_metadata", contar)
    with SessionLocal() as db:
        resultado = dashboard_service.snapshot(db, period="2025-02", type_name="INCENDIO")
    assert resultado["overview"]["total"] == 1
    assert len(chamadas) == 1


def test_filter_metadata_returns_independent_values(ocorrencias_dashboard):
    with SessionLocal() as db:
        with analytics.dataset_snapshot(db):
            primeira = analytics.filter_metadata(db, period="2025-02")
            primeira["coverage"]["months"].clear()
            primeira["available_periods"][0]["months"].clear()
            primeira["applied_filters"]["type"] = "ALTERADO"
            primeira["unavailable_filters"].append("ALTERADO")
            segunda = analytics.filter_metadata(db, period="2025-02")
            assert segunda["coverage"]["months"] == ["Fev/2025"]
            assert segunda["available_periods"][0]["months"] == ["Jan/2025", "Fev/2025"]
            assert segunda["applied_filters"]["type"] is None
            assert segunda["unavailable_filters"] == []


def test_snapshot_cache_does_not_outlive_request(ocorrencias_dashboard):
    with SessionLocal() as db:
        primeira = dashboard_service.snapshot(db, period="all")
        db.add(Occurrence(
            source=analytics.SOURCE_SCOPE,
            source_id="DASHBOARD-NOVA",
            opened_at=datetime(2025, 2, 11, 9),
            type_name="RESGATE",
            municipality="DOURADOS",
        ))
        db.commit()
        segunda = dashboard_service.snapshot(db, period="all")
    assert primeira["overview"]["total"] == 3
    assert segunda["overview"]["total"] == 4
    assert segunda["types"]["items"][0]["total"] == 2


def test_nested_snapshot_keeps_parent_and_isolates_sessions(ocorrencias_dashboard):
    with SessionLocal() as primeira, SessionLocal() as segunda:
        with analytics.dataset_snapshot(primeira):
            estado = primeira.info[analytics._SNAPSHOT_ROWS_KEY]
            with analytics.dataset_snapshot(primeira):
                assert analytics.overview(primeira, type_name="INCENDIO")["total"] == 2
            assert primeira.info[analytics._SNAPSHOT_ROWS_KEY] is estado
            outro = dashboard_service.snapshot(segunda, type_name="RESGATE")
            assert outro["overview"]["total"] == 1
            assert analytics._SNAPSHOT_ROWS_KEY not in segunda.info
            assert analytics.overview(primeira, type_name="INCENDIO")["total"] == 2
        assert analytics._SNAPSHOT_ROWS_KEY not in primeira.info


@pytest.mark.parametrize("filtros", [
    {"period": "2025-02", "type_name": "INCENDIO"},
    {"period": "2025-02", "municipality": "DOURADOS"},
    {"period": "", "type_name": ""},
    {"shift": "Noite"},
])
def test_snapshot_preserves_standalone_analytics(ocorrencias_dashboard, filtros):
    paineis = ["filter_options", "overview", "monthly", "types", "cities", "hours", "units", "shifts"]
    with SessionLocal() as db:
        esperados = {nome: getattr(analytics, nome)(db, **filtros) for nome in paineis}
        with analytics.dataset_snapshot(db):
            atuais = {nome: getattr(analytics, nome)(db, **filtros) for nome in paineis}
    assert atuais == esperados


def test_combined_filters_are_computed_once_per_key(ocorrencias_dashboard, monkeypatch):
    chaves = []
    original = analytics._filtered_rows

    def contar(rows, *args, **kwargs):
        chaves.append(args)
        return original(rows, *args, **kwargs)

    monkeypatch.setattr(analytics, "_filtered_rows", contar)
    with SessionLocal() as db:
        resultado = dashboard_service.snapshot(db, period="2025-02", type_name="INCENDIO")
    assert resultado["overview"]["total"] == 1
    assert set(chaves) == {
        (None, "INCENDIO", None, None, None, None),
        ("2025-02", None, None, None, None, None),
        ("2025-02", "INCENDIO", None, None, None, None),
    }
    assert len(chaves) == 3


def test_empty_filters_share_rows_without_changing_metadata(ocorrencias_dashboard, monkeypatch):
    chamadas = []
    original = analytics._filtered_rows

    def contar(*args, **kwargs):
        chamadas.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(analytics, "_filtered_rows", contar)
    with SessionLocal() as db:
        with analytics.dataset_snapshot(db):
            vazios = analytics.overview(db, period="", type_name="")
            todos = analytics.overview(db, period="all")
            ausentes = analytics.overview(db)
    assert vazios["total"] == todos["total"] == ausentes["total"] == 3
    assert vazios["applied_filters"]["type"] == ""
    assert todos["applied_filters"]["type"] is None
    assert len(chamadas) == 1
