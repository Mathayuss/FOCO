from fastapi.testclient import TestClient
from app.main import app
from app.api.endpoints import imports as imports_endpoint


def test_health():
    with TestClient(app) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_overview_uses_historical_scope():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/overview").json()
        assert data["total"] > 0
        assert data["source_scope"] == "historical_consolidated"


def test_sla_is_explicit_demo_scope():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/sla").json()
        assert data["sample_size"] > 0
        assert data["source_scope"] == "demo_operational"


def test_product_identity():
    with TestClient(app) as client:
        root = client.get("/").json()
        health = client.get("/api/v1/health").json()
        assert root["name"].startswith("FOCO API")
        assert root["version"] == "0.2.0"
        assert health["service"] == "foco-api"


def test_csv_preview_accepts_sample_file():
    with TestClient(app) as client:
        with open("sample_import.csv", "rb") as sample:
            r = client.post(
                "/api/v1/imports/csv/preview",
                files={"file": ("sample_import.csv", sample, "text/csv")},
            )
        data = r.json()
        assert r.status_code == 200
        assert data["total_rows"] == 1
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 0
        assert data["can_commit"] is True
        assert "source_id" in data["recognized_headers"]


def test_csv_preview_rejects_non_csv_extension():
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("sample.txt", b"source_id\nEX-001\n", "text/plain")},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Envie um arquivo CSV"


def test_analytics_period_filter_recalculates_overview():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/overview?period=q1").json()
        assert data["total"] == 20723
        assert data["average_per_day"] == 230.3
        assert data["applied_filters"]["period"] == "Jan-Mar/2026"
        assert data["coverage"]["months"] == ["Jan", "Fev", "Mar"]


def test_analytics_month_period_filter_recalculates_overview_and_comparison():
    with TestClient(app) as client:
        overview = client.get("/api/v1/analytics/overview?period=jul").json()
        monthly = client.get("/api/v1/analytics/monthly?period=jul").json()
        assert overview["total"] == 7006
        assert overview["average_per_day"] == 226.0
        assert overview["delta_pct"] == 5.4
        assert overview["applied_filters"]["period"] == "Jul/2026"
        assert overview["coverage"]["months"] == ["Jul"]
        assert [item["mes"] for item in monthly["items"]] == ["Jul"]
        assert [item["mes"] for item in monthly["comparison"]] == ["Jul"]


def test_overview_exposes_comparison_summary_for_period():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/overview?period=q1").json()
        comparison = data["comparison"]
        assert comparison["available"] is True
        assert comparison["current_label"] == "Jan-Mar/2026"
        assert comparison["baseline_label"] == "Jan-Mar/2025"
        assert comparison["current_total"] == 20723
        assert comparison["baseline_total"] == 19254
        assert comparison["delta_abs"] == 1469
        assert comparison["delta_pct"] == 7.6


def test_overview_exposes_type_comparison_only_when_available():
    with TestClient(app) as client:
        consolidated = client.get("/api/v1/analytics/overview?type=Emerg%C3%AAncia%20Cl%C3%ADnica").json()
        limited = client.get("/api/v1/analytics/overview?period=q1&type=Emerg%C3%AAncia%20Cl%C3%ADnica").json()
        assert consolidated["comparison"]["available"] is True
        assert consolidated["comparison"]["current_total"] == 9367
        assert consolidated["comparison"]["baseline_total"] == 8679
        assert consolidated["comparison"]["delta_abs"] == 688
        assert consolidated["comparison"]["delta_pct"] == 7.9
        assert limited["comparison"]["available"] is False
        assert limited["comparison"]["delta_pct"] is None
        assert limited["delta_pct"] is None
        assert "somente no consolidado" in limited["comparison"]["reason"]


def test_analytics_type_filter_recalculates_monthly_series():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/monthly?period=q1&type=Inc%C3%AAndio").json()
        assert [item["total"] for item in data["items"]] == [382, None, 395]
        assert data["coverage"]["partial_type_series"] is True
        assert data["coverage"]["missing_type_months"] == ["Fev"]
        assert data["comparison"] == []
        assert data["applied_filters"]["type"] == "Incêndio"


def test_analytics_declares_unavailable_cross_filters():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/overview?period=q1&municipality=Campo%20Grande&unit=CMB%2F1%C2%BAGBM&shift=Tarde").json()
        unavailable = {item["field"] for item in data["unavailable_filters"]}
        assert unavailable == {"municipality", "unit", "shift"}
        assert "period" in data["coverage"]["filterable_dimensions"]
        assert "municipality" in data["coverage"]["limited_dimensions"]


def test_analytics_filters_endpoint_lists_available_values():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/filters").json()
        period_keys = [period["key"] for period in data["periods"]]
        assert period_keys[0] == "all"
        assert "jan" in period_keys
        assert "jul" in period_keys
        assert "Emergência Clínica" in data["types"]
        assert "Campo Grande" in data["municipalities"]
        assert data["subtypes"] == []
        assert data["filterable_dimensions"] == ["period", "type"]


def test_consolidated_dimension_endpoints_do_not_claim_cross_filters():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/cities?period=q1&type=Inc%C3%AAndio").json()
        unavailable = {item["field"] for item in data["unavailable_filters"]}
        assert unavailable == {"period", "type"}
        assert data["applied_filters"]["period"] is None
        assert data["applied_filters"]["type"] is None
        assert data["coverage"]["filterable_dimensions"] == ["municipality"]
        hours = client.get("/api/v1/analytics/hours?period=q1&type=Inc%C3%AAndio").json()
        assert {item["field"] for item in hours["unavailable_filters"]} == {"period", "type"}
        assert hours["coverage"]["filterable_dimensions"] == []


def test_dimension_endpoints_apply_their_own_dimension():
    with TestClient(app) as client:
        city = client.get("/api/v1/analytics/cities?municipality=Campo%20Grande").json()
        unit = client.get("/api/v1/analytics/units?unit=CMB%2F1%C2%BAGBM").json()
        shift = client.get("/api/v1/analytics/shifts?shift=Tarde").json()
        assert [item["nome"] for item in city["items"]] == ["Campo Grande"]
        assert city["applied_filters"]["municipality"] == "Campo Grande"
        assert [item["nome"] for item in unit["items"]] == ["CMB/1ºGBM"]
        assert unit["applied_filters"]["unit"] == "CMB/1ºGBM"
        assert [item["nome"] for item in shift["items"]] == ["Tarde"]
        assert shift["applied_filters"]["shift"] == "Tarde"


def test_analytics_rejects_invalid_period():
    with TestClient(app) as client:
        r = client.get("/api/v1/analytics/overview?period=invalid")
        data = r.json()
        assert r.status_code == 400
        assert data["detail"]["code"] == "INVALID_FILTER"
        assert data["detail"]["errors"][0]["field"] == "period"


def test_analytics_rejects_unknown_type():
    with TestClient(app) as client:
        r = client.get("/api/v1/analytics/monthly?type=Tipo%20Inexistente")
        data = r.json()
        assert r.status_code == 400
        assert data["detail"]["code"] == "INVALID_FILTER"
        assert data["detail"]["errors"][0]["field"] == "type"


def test_analytics_rejects_unknown_subtype():
    with TestClient(app) as client:
        r = client.get("/api/v1/analytics/overview?subtype=Sem%20Cadastro")
        data = r.json()
        assert r.status_code == 400
        assert data["detail"]["code"] == "INVALID_FILTER"
        assert data["detail"]["errors"][0]["field"] == "subtype"


def test_csv_preview_rejects_invalid_mime_type():
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("sample.csv", b"source_id,opened_at,municipality,type_name\n", "application/json")},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Tipo MIME inválido para CSV"


def test_csv_preview_rejects_path_like_filename():
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("../sample.csv", b"source_id,opened_at,municipality,type_name\n", "text/csv")},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Nome de arquivo inválido"


def test_csv_preview_rejects_empty_file():
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "CSV vazio"


def test_csv_upload_limit_is_512_mb():
    assert imports_endpoint.MAX_CSV_MEGABYTES == 512
    assert imports_endpoint.MAX_CSV_BYTES == 512 * 1024 * 1024


def test_csv_preview_rejects_large_file(monkeypatch):
    monkeypatch.setattr(imports_endpoint, "MAX_CSV_MEGABYTES", 1)
    monkeypatch.setattr(imports_endpoint, "MAX_CSV_BYTES", 64)
    with TestClient(app) as client:
        content = b"source_id,opened_at,municipality,type_name\n" + b"A" * 65
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("large.csv", content, "text/csv")},
        )
        assert r.status_code == 413
        assert r.json()["detail"] == "CSV excede o limite de 1 MB"
