from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.occurrence import Occurrence
from app.models.unit import Unit
from app.services.sejusp_analytics_service import SOURCE_LABEL, SOURCE_SCOPE


FUSO_LOCAL = ZoneInfo("America/Campo_Grande")
FILTROS = {
    "period": "2026-02",
    "type": "INCENDIO",
    "municipality": "CAMPO GRANDE",
    "unit": "UNIDADE ALFA",
    "subtype": "RESIDENCIAL",
    "shift": "Tarde",
}


def _ocorrencia(
    identificador: str,
    registro_em: datetime,
    unidade: Unit,
    *,
    tipo: str = "INCENDIO",
    municipio: str = "CAMPO GRANDE",
    subtipo: str = "RESIDENCIAL",
    origem: str = SOURCE_SCOPE,
    abertura_em: datetime | None = None,
) -> Occurrence:
    return Occurrence(
        source=origem,
        source_id=identificador,
        opened_at=abertura_em or registro_em,
        registered_at=registro_em,
        type_name=tipo,
        subtype_name=subtipo,
        municipality=municipio,
        unit=unidade,
    )


def _data(ano: int, hora: int, dia: int = 10) -> datetime:
    return datetime(ano, 2, dia, hora, tzinfo=FUSO_LOCAL)


def _preparar_cenario() -> None:
    with SessionLocal() as db:
        alfa = Unit(name="UNIDADE ALFA")
        beta = Unit(name="UNIDADE BETA")
        db.add_all([alfa, beta])
        db.flush()

        registros = [
            _ocorrencia("ALVO-2025-1", _data(2025, 13), alfa),
            _ocorrencia("ALVO-2025-2", _data(2025, 15), alfa),
            _ocorrencia("ALVO-2026-1", _data(2026, 13), alfa),
            _ocorrencia("ALVO-2026-2", _data(2026, 14, 11), alfa),
            _ocorrencia(
                "ALVO-2026-3",
                _data(2026, 15, 12),
                alfa,
                abertura_em=_data(2024, 15, 12),
            ),
            _ocorrencia("CONTROLE-TIPO", _data(2026, 13), alfa, tipo="RESGATE"),
            _ocorrencia("CONTROLE-MUNICIPIO", _data(2026, 13), alfa, municipio="DOURADOS"),
            _ocorrencia("CONTROLE-UNIDADE", _data(2026, 13), beta),
            _ocorrencia("CONTROLE-SUBTIPO", _data(2026, 13), alfa, subtipo="COMERCIAL"),
            _ocorrencia("CONTROLE-TURNO", _data(2026, 20), alfa),
            _ocorrencia("CONTROLE-FONTE", _data(2026, 13), alfa, origem="DADO_DEMO_TESTE"),
        ]
        db.add_all(registros)
        db.commit()


def _itens(painel: dict) -> list[dict]:
    return painel["items"]


def test_criterios_de_aceite_v03_usam_o_mesmo_recorte_em_todos_os_paineis():
    _preparar_cenario()

    with TestClient(app) as client:
        resposta = client.get("/api/v1/analytics/dashboard", params=FILTROS)

    assert resposta.status_code == 200
    dashboard = resposta.json()
    overview = dashboard["overview"]

    assert overview["total"] == 3
    assert overview["top_type"] == "INCENDIO"
    assert overview["top_municipality"] == "CAMPO GRANDE"
    assert overview["source_scope"] == SOURCE_LABEL
    assert overview["applied_filters"] == {
        "period": "Fev/2026",
        "type": "INCENDIO",
        "municipality": "CAMPO GRANDE",
        "unit": "UNIDADE ALFA",
        "subtype": "RESIDENCIAL",
        "shift": "Tarde",
    }

    assert overview["comparison"] == {
        "available": True,
        "current_label": "Fev/2026",
        "baseline_label": "Fev/2025",
        "current_total": 3,
        "baseline_total": 2,
        "delta_abs": 1,
        "delta_pct": 50.0,
        "reason": None,
        "source_scope": SOURCE_LABEL,
    }

    assert _itens(dashboard["monthly"]) == [
        {"mes": "Fev/2026", "total": 3, "tip": [{"nome": "INCENDIO", "total": 3, "pct": 100.0}]}
    ]
    assert dashboard["monthly"]["comparison"] == [{
        "current_month": "Fev/2026",
        "baseline_month": "Fev/2025",
        "current": 3,
        "baseline": 2,
        "delta": 1,
    }]
    assert _itens(dashboard["types"]) == [{"nome": "INCENDIO", "total": 3, "pct": 100.0}]
    assert _itens(dashboard["cities"]) == [{
        "nome": "CAMPO GRANDE", "total": 3, "pct": 100.0, "lat": None, "lon": None,
    }]
    assert _itens(dashboard["units"]) == [{"nome": "UNIDADE ALFA", "total": 3, "pct": 100.0}]
    assert _itens(dashboard["shifts"]) == [{"nome": "Tarde", "total": 3, "pct": 100.0}]
    assert sum(_itens(dashboard["hours"])) == 3
    assert _itens(dashboard["hours"])[13:16] == [1, 1, 1]

    filtros_disponiveis = dashboard["filters"]
    assert FILTROS["type"] in filtros_disponiveis["types"]
    assert FILTROS["municipality"] in filtros_disponiveis["municipalities"]
    assert FILTROS["unit"] in filtros_disponiveis["units"]
    assert FILTROS["subtype"] in filtros_disponiveis["subtypes"]
    assert FILTROS["shift"] in filtros_disponiveis["shifts"]
    assert FILTROS["period"] in {periodo["key"] for periodo in filtros_disponiveis["periods"]}

    for nome in ("monthly", "types", "cities", "hours", "units", "shifts"):
        painel = dashboard[nome]
        assert painel["source_scope"] == SOURCE_LABEL
        assert painel["applied_filters"] == overview["applied_filters"]
        assert painel["unavailable_filters"] == []
