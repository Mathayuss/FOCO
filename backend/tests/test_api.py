from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from app.main import app
from app.api.endpoints import imports as imports_endpoint
from app.db.session import SessionLocal
from app.models.occurrence import Occurrence, OccurrenceVehicle
from app.models.unit import Unit
from app.models.vehicle import Vehicle


def _xlsx_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    def col_name(index: int) -> str:
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    all_rows = [headers, *rows]
    row_xml = []
    for row_index, row in enumerate(all_rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{col_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        '</worksheet>'
    )
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        zf.writestr("xl/workbook.xml", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="sejusp" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>'
        ))
        zf.writestr("xl/_rels/workbook.xml.rels", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>'
        ))
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()



def _cleanup_imported_test_data(source_ids: list[str], unit_names: list[str]):
    db = SessionLocal()
    try:
        if source_ids:
            db.execute(
                delete(Occurrence).where(
                    Occurrence.source == "RELATORIO_SEJUSP",
                    Occurrence.source_id.in_(source_ids),
                )
            )
            db.commit()
        for unit_name in unit_names:
            unit = db.scalar(select(Unit).where(Unit.name == unit_name))
            if not unit:
                continue
            remaining = db.scalar(select(Occurrence.id).where(Occurrence.unit_id == unit.id).limit(1))
            if remaining is None:
                db.delete(unit)
        db.commit()
    finally:
        db.close()

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


def test_database_model_names_are_portuguese():
    assert Unit.__tablename__ == "unidade_operacional"
    assert Vehicle.__tablename__ == "viatura"
    assert Occurrence.__tablename__ == "ocorrencia"
    assert OccurrenceVehicle.__tablename__ == "ocorrencia_viatura"

    assert set(Unit.__table__.columns.keys()) == {"id_unidade_operacional", "nome", "comando", "ativo"}
    assert set(Vehicle.__table__.columns.keys()) == {"id_viatura", "codigo", "tipo_viatura", "id_unidade_operacional", "ativo"}
    assert set(OccurrenceVehicle.__table__.columns.keys()) == {
        "id_ocorrencia_viatura",
        "id_ocorrencia",
        "id_viatura",
        "despacho_em",
        "saida_em",
        "chegada_em",
        "liberacao_em",
        "retorno_em",
        "disponibilidade_em",
    }
    assert set(Occurrence.__table__.columns.keys()) == {
        "id_ocorrencia",
        "sistema_origem",
        "id_origem",
        "numero_externo",
        "abertura_em",
        "despacho_em",
        "saida_em",
        "chegada_em",
        "liberacao_em",
        "retorno_em",
        "disponibilidade_em",
        "grupo",
        "tipo",
        "subtipo",
        "prioridade",
        "municipio",
        "bairro",
        "endereco",
        "latitude",
        "longitude",
        "id_unidade_operacional",
        "situacao",
        "pontuacao_qualidade",
        "registro_em",
        "codigo_ibge",
        "segredo_de_justica",
        "dados_origem",
        "importado_em",
    }


def test_demo_rows_use_portuguese_database_values():
    with TestClient(app):
        db = SessionLocal()
        try:
            row = db.scalar(select(Occurrence).where(Occurrence.source == "DADO_DEMO").limit(1))
            assert row is not None
            assert row.status == "fechada"
        finally:
            db.close()


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
        assert "id_origem" in data["recognized_headers"]


def test_csv_preview_rejects_non_csv_extension():
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("sample.txt", b"id_origem\nEX-001\n", "text/plain")},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Envie um arquivo CSV, XLS ou XLSX"


def test_csv_preview_accepts_legacy_english_headers_as_aliases():
    content = (
        "source_id,opened_at,municipality,type_name\n"
        "EX-001,2026-09-01T12:00:00-04:00,Campo Grande,Incêndio\n"
    ).encode("utf-8")
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("legado.csv", content, "text/csv")},
        )
    data = r.json()
    assert r.status_code == 200
    assert data["recognized_headers"] == ["abertura_em", "id_origem", "municipio", "tipo"]
    assert data["missing_required_headers"] == []
    assert data["can_commit"] is True


def test_import_preview_maps_sejusp_csv_headers_to_foco_fields():
    content = (
        "Nº/ANO,DATA DO FATO,HORA DO FATO,FATO,FATO AGRUPADO,CATEGORIA,"
        "UNIDADE DE ORIGEM,MUNICÍPIO,CÓDIGO IBGE,BAIRRO,LOGRADOURO,REFERÊNCIA,"
        "LATITUDE,LONGITUDE,SEGREDO DE JUSTIÇA\n"
        "100/2025 1º GBM,45838,0.5,INCENDIO EM VEGETACAO,COMBATE A INCENDIO,"
        "COMBATE A INCENDIO,1º GBM,Campo Grande,5002704,Centro,R. A,Referência,"
        "-20.45,-54.62,Sim\n"
    ).encode("utf-8")
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp.csv", content, "text/csv")},
        )
    data = r.json()
    mappings = {item["source_header"]: item["target_field"] for item in data["column_mappings"]}
    assert r.status_code == 200
    assert data["source_profile"] == "RELATORIO_SEJUSP"
    assert data["source_format"] == "csv"
    assert data["valid_rows"] == 1
    assert data["sensitive_rows"] == 1
    assert data["invalid_coordinate_rows"] == 0
    assert data["can_commit"] is True
    assert mappings["Nº/ANO"] == "id_origem"
    assert mappings["DATA DO FATO"] == "abertura_em"
    assert mappings["FATO"] == "tipo"
    assert mappings["UNIDADE DE ORIGEM"] == "unidade_operacional"


def test_import_preview_accepts_sejusp_headers_with_extra_spaces_and_markup():
    content = (
        "Nº/ANO;FORÇA;MOVIMENTAÇÃO;SEGREDO DE   JUSTIÇA;FATO;FATO AGRUPADO;CATEGORIA;"
        "AUTORIA CONHECIDA / DESCONHECIDA;MOTIVAÇÃO;UNIDADE DE   ORIGEM;UF DE ORIGEM;"
        "MUNICÍPIO DE   ORIGEM;DATA DO REGISTRO;HORA DO REGISTRO;DIA DO REGISTRO;"
        "PERÍODO DO   REGISTRO;DATA DO FATO;HORA DO FATO;FAIXA IDADE;LOCAL;UF;"
        "MUNICÍPIO;CÓDIGO IBGE;BAIRRO;REFERÊNCIA;ÁREA DO   MUNICÍPIO;LOGRADOURO;"
        "LATITUDE;LONGITUDE<br>\n"
        "103/2025 1º GBM;CBMMS;Entrada;Não;REMOCAO AO PS;BUSCA E SALVAMENTO;"
        "BUSCA E SALVAMENTO;;;1º GBM;MS;Campo Grande;01/01/2025;08:10;quarta;"
        "Manhã;01/01/2025;08:20;Adulto;Via pública;MS;Campo Grande;5002704;Centro;"
        "Próximo ao marco;Urbana;R. Teste;-20.45;-54.62\n"
    ).encode("utf-8")
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp.xls", content, "text/html")},
        )
    data = r.json()
    mappings = {item["source_header"]: item["target_field"] for item in data["column_mappings"]}
    assert r.status_code == 200
    assert data["source_format"] == "xls"
    assert data["valid_rows"] == 1
    assert data["missing_required_headers"] == []
    assert mappings["SEGREDO DE   JUSTIÇA"] == "segredo_de_justica"
    assert mappings["UNIDADE DE   ORIGEM"] == "unidade_operacional"
    assert mappings["PERÍODO DO   REGISTRO"] == "periodo_registro"
    assert mappings["LONGITUDE<br>"] == "longitude"


def test_import_preview_accepts_markdown_pipe_table_headers():
    content = '| Nº/ANO | FORÇA | MOVIMENTAÇÃO | SEGREDO DE   JUSTIÇA | FATO | FATO AGRUPADO | CATEGORIA | AUTORIA   CONHECIDA / DESCONHECIDA | MOTIVAÇÃO | UNIDADE DE   ORIGEM | UF DE ORIGEM | MUNICÍPIO DE   ORIGEM | DATA DO REGISTRO | HORA DO REGISTRO | DIA DO REGISTRO | PERÍODO DO   REGISTRO | DATA DO FATO | HORA DO FATO | FAIXA IDADE | LOCAL | UF | MUNICÍPIO | CÓDIGO IBGE | BAIRRO | REFERÊNCIA | ÁREA DO   MUNICÍPIO | LOGRADOURO | LATITUDE | LONGITUDE |\n| ------ | ----- | ------------ | -------------------- | ---- | ------------- | --------- | ---------------------------------- | --------- | ------------------- | ------------ | --------------------- | ---------------- | ---------------- | --------------- | --------------------- | ------------ | ------------ | ----------- | ----- | -- | --------- | ----------- | ------ | ---------- | ------------------- | ---------- | -------- | --------- |\n| 104/2025 1º GBM | CBMMS | Entrada | Não | REMOCAO AO PS | BUSCA E SALVAMENTO | BUSCA E SALVAMENTO | Conhecida | Teste | 1º GBM | MS | Campo Grande | 01/01/2025 | 08:10 | quarta | Manhã | 01/01/2025 | 08:20 | Adulto | Via pública | MS | Campo Grande | 5002704 | Centro | Próximo ao marco | Urbana | R. Teste | -20.45 | -54.62 |\n'.encode("utf-8")
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp.xls", content, "application/vnd.ms-excel")},
        )
    data = r.json()
    mappings = {item["source_header"]: item["target_field"] for item in data["column_mappings"]}
    assert r.status_code == 200
    assert data["source_format"] == "xls"
    assert data["valid_rows"] == 1
    assert data["missing_required_headers"] == []
    assert "" not in data["headers"]
    assert mappings["AUTORIA   CONHECIDA / DESCONHECIDA"] == "autoria"
    assert mappings["LONGITUDE"] == "longitude"


def test_import_preview_accepts_xlsx_content_renamed_as_xls():
    headers = ["Nº/ANO", "DATA DO FATO", "HORA DO FATO", "FATO", "UNIDADE DE ORIGEM", "MUNICÍPIO"]
    body = _xlsx_bytes(headers, [["105/2025 1º GBM", "01/01/2025", "12:30", "REMOCAO AO PS", "1º GBM", "Campo Grande"]])
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp.xls", body, "application/vnd.ms-excel")},
        )
    data = r.json()
    assert r.status_code == 200
    assert data["source_format"] == "xlsx"
    assert data["source_profile"] == "RELATORIO_SEJUSP"
    assert data["valid_rows"] == 1


def test_import_preview_accepts_sejusp_xls_html_report_headers():
    body = """<html><body><table>
    <tr><td colspan="11">Relatório de ocorrências</td></tr>
    <tr><th>Nº/ANO</th><th>DATA DO FATO</th><th>HORA DO FATO</th><th>FATO</th><th>FATO AGRUPADO</th><th>CATEGORIA</th><th>UNIDADE DE   ORIGEM</th><th>MUNICÍPIO</th><th>LATITUDE</th><th>LONGITUDE<br></th><th>SEGREDO DE   JUSTIÇA</th></tr>
    <tr><td>102/2025 1º GBM</td><td>01/01/2025</td><td>13:45</td><td>REMOCAO AO PS</td><td>BUSCA E SALVAMENTO</td><td>BUSCA E SALVAMENTO</td><td>1º GBM</td><td>Campo Grande</td><td>-20.45</td><td>-54.62</td><td>Não</td></tr>
    </table></body></html>""".encode("utf-8")
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp.xls", body, "application/vnd.ms-excel")},
        )
    data = r.json()
    assert r.status_code == 200
    assert data["source_format"] == "xls"
    assert data["source_profile"] == "RELATORIO_SEJUSP"
    assert data["valid_rows"] == 1
    assert data["missing_required_headers"] == []
    assert "abertura_em" in data["recognized_headers"]


def test_import_preview_accepts_sejusp_xlsx_report_headers():
    headers = [
        "Nº/ANO",
        "DATA DO FATO",
        "HORA DO FATO",
        "FATO",
        "FATO AGRUPADO",
        "CATEGORIA",
        "UNIDADE DE ORIGEM",
        "MUNICÍPIO",
        "LATITUDE",
        "LONGITUDE",
        "SEGREDO DE JUSTIÇA",
    ]
    body = _xlsx_bytes(headers, [[
        "101/2025 1º GBM",
        "01/01/2025",
        "12:30",
        "REMOCAO AO PS",
        "BUSCA E SALVAMENTO",
        "BUSCA E SALVAMENTO",
        "1º GBM",
        "Campo Grande",
        "-20.45",
        "-54.62",
        "Não",
    ]])
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp.xlsx", body, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    data = r.json()
    assert r.status_code == 200
    assert data["source_format"] == "xlsx"
    assert data["source_profile"] == "RELATORIO_SEJUSP"
    assert data["valid_rows"] == 1
    assert data["missing_required_headers"] == []
    assert "abertura_em" in data["recognized_headers"]


def test_import_commit_inserts_sejusp_rows_with_equivalent_fields():
    source_id = f"{uuid4()}/2025 9º GBM"
    unit_name = f"9º GBM TESTE {uuid4()}"
    content = (
        "Nº/ANO,DATA DO REGISTRO,HORA DO REGISTRO,DATA DO FATO,HORA DO FATO,FATO,"
        "FATO AGRUPADO,CATEGORIA,UNIDADE DE ORIGEM,MUNICÍPIO,CÓDIGO IBGE,BAIRRO,"
        "LOGRADOURO,REFERÊNCIA,LATITUDE,LONGITUDE,SEGREDO DE JUSTIÇA\n"
        f"{source_id},01/01/2025,08:10,01/01/2025,08:20,INCENDIO EM VEGETACAO,"
        f"COMBATE A INCENDIO,COMBATE A INCENDIO,{unit_name},Campo Grande,5002704,"
        "Centro,R. Teste,Próximo ao marco,-20.45,-54.62,Sim\n"
    ).encode("utf-8")
    try:
        with TestClient(app) as client:
            first = client.post(
                "/api/v1/imports",
                files={"file": ("sejusp.csv", content, "text/csv")},
            ).json()
            second = client.post(
                "/api/v1/imports",
                files={"file": ("sejusp.csv", content, "text/csv")},
            ).json()

        assert first["inserted_rows"] == 1
        assert first["skipped_duplicate_rows"] == 0
        assert first["source_scope"] == "RELATORIO_SEJUSP"
        assert second["inserted_rows"] == 0
        assert second["skipped_duplicate_rows"] == 1

        db = SessionLocal()
        try:
            row = db.scalar(
                select(Occurrence).where(
                    Occurrence.source == "RELATORIO_SEJUSP",
                    Occurrence.source_id == source_id,
                )
            )
            assert row is not None
            assert row.type_name == "INCENDIO EM VEGETACAO"
            assert row.group_name == "COMBATE A INCENDIO"
            assert row.subtype_name == "COMBATE A INCENDIO"
            assert row.municipality == "Campo Grande"
            assert row.ibge_code == "5002704"
            assert row.status == "importada"
            assert row.priority == "sigilo_judicial"
            assert row.judicial_secret is True
            assert row.source_payload and "Nº/ANO" in row.source_payload
            assert row.unit and row.unit.name == unit_name
        finally:
            db.close()
    finally:
        _cleanup_imported_test_data([source_id], [unit_name])


def test_analytics_sejusp_source_applies_cross_filters():
    source_id = f"ANALYTICS-{uuid4()}"
    unit_name = f"UNIDADE ANALYTICS {uuid4()}"
    type_name = f"TIPO ANALYTICS {uuid4()}"
    subtype_name = f"SUBTIPO ANALYTICS {uuid4()}"
    municipality = f"Municipio Analytics {uuid4()}"
    db = SessionLocal()
    try:
        unit = Unit(name=unit_name, command="TESTE", active=True)
        db.add(unit)
        db.flush()
        db.add(
            Occurrence(
                source="RELATORIO_SEJUSP",
                source_id=source_id,
                opened_at=datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
                type_name=type_name,
                group_name="GRUPO ANALYTICS",
                subtype_name=subtype_name,
                municipality=municipality,
                neighborhood="Centro",
                latitude=-20.45,
                longitude=-54.62,
                unit_id=unit.id,
                status="importada",
                judicial_secret=False,
            )
        )
        db.commit()
    finally:
        db.close()

    try:
        with TestClient(app) as client:
            filters = client.get("/api/v1/analytics/filters", params={"source": "sejusp"}).json()
            assert filters["source_scope"] == "sejusp_importado"
            assert filters["limited_dimensions"] == []
            assert type_name in filters["types"]
            assert municipality in filters["municipalities"]
            assert unit_name in filters["units"]
            assert subtype_name in filters["subtypes"]

            params = {
                "source": "sejusp",
                "period": "jan",
                "type": type_name,
                "municipality": municipality,
                "unit": unit_name,
                "subtype": subtype_name,
                "shift": "Tarde",
            }
            overview = client.get("/api/v1/analytics/overview", params=params).json()
            cities = client.get("/api/v1/analytics/cities", params=params).json()
            hours = client.get("/api/v1/analytics/hours", params=params).json()

        assert overview["total"] == 1
        assert overview["source_scope"] == "sejusp_importado"
        assert overview["applied_filters"]["municipality"] == municipality
        assert overview["applied_filters"]["unit"] == unit_name
        assert overview["applied_filters"]["subtype"] == subtype_name
        assert overview["applied_filters"]["shift"] == "Tarde"
        assert overview["coverage"]["limited_dimensions"] == []
        assert overview["comparison"]["available"] is False
        assert cities["items"][0]["nome"] == municipality
        assert cities["items"][0]["total"] == 1
        assert hours["items"][14] == 1
    finally:
        _cleanup_imported_test_data([source_id], [unit_name])

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


def test_analytics_rejects_invalid_source():
    with TestClient(app) as client:
        r = client.get("/api/v1/analytics/overview?source=invalida")
        data = r.json()
        assert r.status_code == 400
        assert data["detail"]["code"] == "INVALID_FILTER"
        assert data["detail"]["errors"][0]["field"] == "source"


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
            files={"file": ("sample.csv", b"id_origem,abertura_em,municipio,tipo\n", "application/json")},
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Tipo MIME inválido para importação"


def test_csv_preview_rejects_path_like_filename():
    with TestClient(app) as client:
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("../sample.csv", b"id_origem,abertura_em,municipio,tipo\n", "text/csv")},
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
        assert r.json()["detail"] == "Arquivo vazio"


def test_import_upload_limit_is_512_mb():
    assert imports_endpoint.MAX_IMPORT_MEGABYTES == 512
    assert imports_endpoint.MAX_IMPORT_BYTES == 512 * 1024 * 1024
    assert imports_endpoint.MAX_CSV_MEGABYTES == 512
    assert imports_endpoint.MAX_CSV_BYTES == 512 * 1024 * 1024


def test_csv_preview_rejects_large_file(monkeypatch):
    monkeypatch.setattr(imports_endpoint, "MAX_IMPORT_MEGABYTES", 1)
    monkeypatch.setattr(imports_endpoint, "MAX_IMPORT_BYTES", 64)
    with TestClient(app) as client:
        content = b"id_origem,abertura_em,municipio,tipo\n" + b"A" * 65
        r = client.post(
            "/api/v1/imports/csv/preview",
            files={"file": ("large.csv", content, "text/csv")},
        )
        assert r.status_code == 413
        assert r.json()["detail"] == "Arquivo excede o limite de 1 MB"
