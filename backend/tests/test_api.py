from datetime import datetime, timezone
import hashlib
import importlib.util
import inspect
import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, delete, select, text
from app.core.config import Settings
from app.main import app
from app.api.endpoints import imports as imports_endpoint
from app.db.session import SessionLocal
from app.models.import_batch import ImportBatch, RejectedImportLine
from app.models.occurrence import Occurrence, OccurrenceVehicle
from app.models.unit import Unit
from app.models.vehicle import Vehicle
from app.services import import_audit_service, import_service, sejusp_analytics_service


FUSO_LOCAL = ZoneInfo("America/Campo_Grande")


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



def _cleanup_imported_test_data(source_ids: list[str], unit_names: list[str], batch_ids: list[int] | None = None):
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
        for batch_id in batch_ids or []:
            batch = db.get(ImportBatch, batch_id)
            if batch:
                db.delete(batch)
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
        sejusp_analytics_service.clear_cache()

def test_health():
    with TestClient(app) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["database"] == "ok"


def test_overview_defaults_to_sejusp_scope():
    with TestClient(app) as client:
        r = client.get("/api/v1/analytics/overview")
        data = r.json()
        assert r.status_code == 200
        assert data["source_scope"] == "sejusp_importado"
        assert data["comparison"]["available"] is False


def test_sla_uses_sejusp_without_fabricated_coverage():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/sla").json()
        assert data["source_scope"] == "sejusp_importado"
        assert data["computable"] <= data["sample_size"]


def test_product_identity():
    with TestClient(app) as client:
        root = client.get("/").json()
        health = client.get("/api/v1/health").json()
        assert root["name"].startswith("FOCO API")
        assert root["version"] == "0.3.1"
        assert health["service"] == "foco-api"


def test_database_model_names_are_portuguese():
    assert Unit.__tablename__ == "unidade_operacional"
    assert Vehicle.__tablename__ == "viatura"
    assert Occurrence.__tablename__ == "ocorrencia"
    assert OccurrenceVehicle.__tablename__ == "ocorrencia_viatura"
    assert ImportBatch.__tablename__ == "lote_importacao"
    assert RejectedImportLine.__tablename__ == "linha_importacao_rejeitada"

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
        "id_lote_importacao",
        "importado_em",
    }
    assert set(ImportBatch.__table__.columns.keys()) == {
        "id_lote_importacao",
        "nome_arquivo",
        "hash_arquivo",
        "formato_arquivo",
        "perfil_origem",
        "sistema_origem",
        "total_linhas",
        "linhas_validas",
        "linhas_invalidas",
        "linhas_inseridas",
        "linhas_duplicadas",
        "linhas_sensiveis",
        "linhas_coordenada_invalida",
        "linhas_sem_coordenada",
        "periodos_registro",
        "linhas_validas_sem_data_registro",
        "situacao",
        "avisos",
        "erro",
        "iniciado_em",
        "concluido_em",
    }
    assert set(RejectedImportLine.__table__.columns.keys()) == {
        "id_linha_importacao_rejeitada",
        "id_lote_importacao",
        "numero_linha",
        "motivos",
        "dados_origem",
    }


def test_startup_does_not_create_demo_rows():
    with TestClient(app):
        db = SessionLocal()
        try:
            row = db.scalar(select(Occurrence.id).where(Occurrence.source == "DADO_DEMO").limit(1))
            assert row is None
        finally:
            db.close()


def test_migration_0005_is_idempotent_when_indexes_already_exist():
    migration_path = Path(__file__).resolve().parents[1] / "migracoes" / "versoes" / "20260914_0005_alinha_indices_e_chave_lote.py"
    spec = importlib.util.spec_from_file_location("migration_0005", migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE lote_importacao (id_lote_importacao INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE ocorrencia (id_ocorrencia INTEGER PRIMARY KEY, id_lote_importacao INTEGER, id_unidade_operacional INTEGER)"))
        conn.execute(text("CREATE INDEX ix_ocorrencia_id_lote_importacao ON ocorrencia (id_lote_importacao)"))

        assert module._index_exists(conn, "ocorrencia", "ix_ocorrencia_id_lote_importacao") is True
        assert module._index_exists(conn, "ocorrencia", "ix_ocorrencia_id_unidade_operacional") is False

        module._ensure_index(conn, "ocorrencia", "ix_ocorrencia_id_unidade_operacional", ["id_unidade_operacional"])
        assert module._index_exists(conn, "ocorrencia", "ix_ocorrencia_id_unidade_operacional") is True


def test_csv_preview_accepts_sample_file():
    with TestClient(app) as client:
        with (Path(__file__).resolve().parents[1] / "sample_import.csv").open("rb") as sample:
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


def test_import_preview_uses_first_row_from_hybrid_html_xls():
    headers = [
        "Nº/Ano",
        "Fato",
        "Data do registro",
        "Data do fato",
        "Município",
        "Tempo de atendimento",
        "Despacho",
        "Especial",
    ]
    values = [
        "3736/2026 CMB/1ºGBM",
        "INCENDIO EM EDIFICACAO",
        "07/08/2026 - 23:37:03",
        "07/08/2026 - 22:16:00",
        "Campo Grande",
        "01:21:03",
        "6429993",
        "Não",
    ]

    def cells(items: list[str]) -> bytes:
        return b"".join(
            b"<td>" + b"".join(bytes((byte, 0)) for byte in item.encode("cp1252")) + b"</td>"
            for item in items
        )

    body = (
        b"<table><thead><tr>"
        + cells(headers)
        + b"</tr></thead><tbody><tr>"
        + cells(values)
        + b"</tr></tbody></table>"
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("relatorio.xls", body, "application/vnd.ms-excel")},
        )

    data = response.json()
    mappings = {item["source_header"]: item["target_field"] for item in data["column_mappings"]}
    assert response.status_code == 200
    assert data["headers"] == headers
    assert data["total_rows"] == 1
    assert data["valid_rows"] == 1
    assert data["registration_years"] == [2026]
    assert data["can_commit"] is True
    assert mappings["Tempo de atendimento"] == "tempo_atendimento"
    assert mappings["Despacho"] == "despacho"
    assert mappings["Especial"] == "especial"


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


def test_import_preview_rejects_ambiguous_duplicate_headers():
    content = (
        "Nº/ANO,DATA DO FATO,FATO,MUNICÍPIO,MUNICIPIO\n"
        "100/2025,01/01/2025,INCENDIO,Campo Grande,Corumbá\n"
    ).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("duplicada.csv", content, "text/csv")},
        )

    assert response.status_code == 400
    assert "colunas ambíguas" in response.json()["detail"]
    assert "municipio" in response.json()["detail"]


def test_import_preview_rejects_corrupted_xlsx_package():
    body = BytesIO()
    with ZipFile(body, "w", ZIP_DEFLATED) as workbook:
        workbook.writestr("arquivo.txt", "não é uma planilha")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={
                "file": (
                    "corrompida.xlsx",
                    body.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Arquivo XLSX inválido ou corrompido"


def test_import_preview_validates_time_lengths_and_coordinate_ranges():
    content = (
        "Nº/ANO,DATA DO FATO,HORA DO FATO,FATO,UNIDADE DE ORIGEM,MUNICÍPIO,LATITUDE,LONGITUDE\n"
        f"{'X' * 121},01/01/2025,25:99,INCENDIO,1º GBM,Campo Grande,95,-54.62\n"
    ).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("campos-invalidos.csv", content, "text/csv")},
        )

    data = response.json()
    assert response.status_code == 200
    assert data["valid_rows"] == 0
    assert data["invalid_coordinate_rows"] == 1
    assert data["can_commit"] is False
    assert "id_origem excede 120 caracteres" in data["issues"][0]["issues"]
    assert "abertura_em inválido" in data["issues"][0]["issues"]


def test_import_preview_does_not_allow_header_only_file():
    content = "id_origem,abertura_em,municipio,tipo\n".encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sem-dados.csv", content, "text/csv")},
        )

    data = response.json()
    assert response.status_code == 200
    assert data["total_rows"] == 0
    assert data["can_commit"] is False
    assert "Arquivo sem linhas de dados" in data["validation_errors"]


def test_import_preview_reports_physical_row_after_report_title():
    content = (
        "Relatório de ocorrências\n"
        "Nº/ANO,DATA DO FATO,HORA DO FATO,FATO,MUNICÍPIO\n"
        "SEM-DATA,,08:20,REMOCAO AO PS,Campo Grande\n"
    ).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("titulo.csv", content, "text/csv")},
        )

    data = response.json()
    assert response.status_code == 200
    assert data["issues"][0]["row"] == 3


def test_import_preview_accepts_windows_1252_csv():
    content = (
        "Nº/ANO;DATA DO FATO;FATO;MUNICÍPIO\n"
        "100/2025;01/01/2025;INCÊNDIO;Campo Grande\n"
    ).encode("cp1252")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("sejusp-cp1252.csv", content, "text/csv")},
        )

    data = response.json()
    assert response.status_code == 200
    assert data["valid_rows"] == 1
    assert data["can_commit"] is True


def test_import_rejects_csv_invalid_in_utf8_and_windows_1252():
    content = (
        b"id_origem,abertura_em,municipio,tipo\n"
        b"ENC-1,2026-10-01,Campo Grande,INCENDIO\x81\n"
    )

    with TestClient(app) as client:
        preview = client.post(
            "/api/v1/imports/preview",
            files={"file": ("invalido.csv", content, "text/csv")},
        )
        commit = client.post(
            "/api/v1/imports",
            files={"file": ("invalido.csv", content, "text/csv")},
        )

    expected = "CSV deve estar em UTF-8 ou Windows-1252"
    assert preview.status_code == 400
    assert preview.json()["detail"] == expected
    assert commit.status_code == 400
    assert commit.json()["detail"] == expected


def test_import_preview_years_ignore_rejected_rows_and_allow_valid_subset():
    content = (
        "Nº/ANO,DATA DO REGISTRO,DATA DO FATO,FATO,MUNICÍPIO\n"
        "VALIDA-2025,01/01/2025,01/01/2025,INCENDIO,Campo Grande\n"
        "INVALIDA-2024,01/01/2024,01/01/2024,INCENDIO,\n"
    ).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("parcial.csv", content, "text/csv")},
        )

    data = response.json()
    assert response.status_code == 200
    assert data["valid_rows"] == 1
    assert data["invalid_rows"] == 1
    assert data["registration_years"] == [2025]
    assert data["can_commit"] is True


def test_import_commit_inserts_sejusp_rows_with_equivalent_fields(monkeypatch):
    first = None
    second = None
    duplicate_preview = None
    cache_clears = 0

    def fake_clear_cache():
        nonlocal cache_clears
        cache_clears += 1

    monkeypatch.setattr(sejusp_analytics_service, "clear_cache", fake_clear_cache)

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
            duplicate_preview = client.post(
                "/api/v1/imports/preview",
                files={"file": ("sejusp.csv", content, "text/csv")},
            ).json()
            second = client.post(
                "/api/v1/imports",
                files={"file": ("sejusp.csv", content, "text/csv")},
            ).json()

        assert first["id_lote_importacao"] > 0
        assert first["inserted_rows"] == 1
        assert first["skipped_duplicate_rows"] == 0
        assert first["source_scope"] == "RELATORIO_SEJUSP"
        assert duplicate_preview["already_imported"] is True
        assert duplicate_preview["previous_import_batch_id"] == first["id_lote_importacao"]
        assert duplicate_preview["previous_import_status"] == "concluido"
        assert duplicate_preview["previous_import_at"]
        assert duplicate_preview["existing_rows"] == 1
        assert duplicate_preview["new_rows"] == 0
        assert any("já foi processado" in warning for warning in duplicate_preview["warnings"])
        assert any("já existem" in warning for warning in duplicate_preview["warnings"])
        assert duplicate_preview["can_commit"] is True
        assert second["inserted_rows"] == 0
        assert second["skipped_duplicate_rows"] == 1
        assert cache_clears == 1

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
            assert row.import_batch_id == first["id_lote_importacao"]
            assert row.import_batch and row.import_batch.filename == "sejusp.csv"
            assert row.unit and row.unit.name == unit_name
        finally:
            db.close()
    finally:
        batch_ids = [item["id_lote_importacao"] for item in (first, second) if item]
        _cleanup_imported_test_data([source_id], [unit_name], batch_ids)


def test_reprocessing_duplicate_does_not_create_orphan_unit():
    first = None
    second = None
    source_id = f"UNIDADE-{uuid4()}"
    original_unit = f"UNIDADE ORIGINAL {uuid4()}"
    changed_unit = f"UNIDADE DUPLICADA {uuid4()}"

    def content(unit_name: str) -> bytes:
        return (
            "Nº/ANO,DATA DO REGISTRO,DATA DO FATO,FATO,UNIDADE DE ORIGEM,MUNICÍPIO\n"
            f"{source_id},01/10/2026,01/10/2026,INCENDIO,{unit_name},Campo Grande\n"
        ).encode("utf-8")

    try:
        with TestClient(app) as client:
            first_response = client.post(
                "/api/v1/imports",
                files={"file": ("original.csv", content(original_unit), "text/csv")},
            )
            second_response = client.post(
                "/api/v1/imports",
                files={"file": ("duplicada.csv", content(changed_unit), "text/csv")},
            )

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        first = first_response.json()
        second = second_response.json()
        assert first["inserted_rows"] == 1
        assert second["inserted_rows"] == 0
        assert second["skipped_duplicate_rows"] == 1

        db = SessionLocal()
        try:
            original = db.scalar(select(Unit).where(Unit.name == original_unit))
            orphan = db.scalar(select(Unit).where(Unit.name == changed_unit))
            assert original is not None
            assert orphan is None
        finally:
            db.close()
    finally:
        batch_ids = [item["id_lote_importacao"] for item in (first, second) if item]
        _cleanup_imported_test_data(
            [source_id],
            [original_unit, changed_unit],
            batch_ids,
        )


def test_import_normalizes_fields_but_preserves_original_cell_values():
    result = None
    source_id = f"RASTREIO-{uuid4()}"
    unit_name = f"UNIDADE RASTREIO {uuid4()}"
    content = (
        "Nº/ANO,DATA DO REGISTRO,DATA DO FATO,FATO,UNIDADE DE ORIGEM,MUNICÍPIO\n"
        f"  {source_id}  , 01/10/2026 , 01/10/2026 ,  INCENDIO  ,"
        f"  {unit_name}  ,  Campo Grande  \n"
    ).encode("utf-8")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/imports",
                files={"file": ("rastreio.csv", content, "text/csv")},
            )

        assert response.status_code == 200
        result = response.json()
        assert result["inserted_rows"] == 1

        db = SessionLocal()
        try:
            row = db.scalar(
                select(Occurrence).where(
                    Occurrence.source == "RELATORIO_SEJUSP",
                    Occurrence.source_id == source_id,
                )
            )
            assert row is not None
            assert row.type_name == "INCENDIO"
            assert row.municipality == "Campo Grande"
            assert row.unit and row.unit.name == unit_name
            payload = json.loads(row.source_payload or "{}")
            assert payload["Nº/ANO"] == f"  {source_id}  "
            assert payload["FATO"] == "  INCENDIO  "
            assert payload["MUNICÍPIO"] == "  Campo Grande  "
        finally:
            db.close()
    finally:
        batch_ids = [result["id_lote_importacao"]] if result else []
        _cleanup_imported_test_data([source_id], [unit_name], batch_ids)


def test_import_commit_persists_batch_and_rejected_rows():
    result = None
    source_id = f"LOTE-{uuid4()}"
    content = (
        "Nº/ANO,DATA DO REGISTRO,HORA DO REGISTRO,DATA DO FATO,HORA DO FATO,FATO,UNIDADE DE ORIGEM,MUNICÍPIO,LATITUDE,LONGITUDE\n"
        f"{source_id},01/02/2025,08:10,01/02/2025,08:20,REMOCAO AO PS,1º GBM,Campo Grande,-20.45,-54.62\n"
        "SEM-DATA,01/02/2025,08:10,,08:20,REMOCAO AO PS,1º GBM,Campo Grande,-20.45,-54.62\n"
    ).encode("utf-8")
    try:
        with TestClient(app) as client:
            result = client.post(
                "/api/v1/imports",
                files={"file": ("sejusp-lote.csv", content, "text/csv")},
            ).json()

        assert result["id_lote_importacao"] > 0
        assert result["inserted_rows"] == 1
        assert result["invalid_rows"] == 1

        id_lote = result["id_lote_importacao"]
        with TestClient(app) as client:
            list_response = client.get("/api/v1/imports/lotes", params={"limite": 5}).json()
            detail_response = client.get(f"/api/v1/imports/lotes/{id_lote}").json()
            rejected_response = client.get(f"/api/v1/imports/lotes/{id_lote}/rejeicoes").json()
            missing_response = client.get("/api/v1/imports/lotes/999999999")

        assert any(item["id_lote_importacao"] == id_lote for item in list_response["items"])
        assert detail_response["nome_arquivo"] == "sejusp-lote.csv"
        assert detail_response["linhas_invalidas"] == 1
        assert rejected_response["total"] == 1
        assert rejected_response["items"][0]["numero_linha"] == 3
        assert "abertura_em inválido" in rejected_response["items"][0]["motivos"]
        assert rejected_response["items"][0]["dados_origem"]["Nº/ANO"] == "SEM-DATA"
        assert missing_response.status_code == 404

        db = SessionLocal()
        try:
            batch = db.get(ImportBatch, result["id_lote_importacao"])
            assert batch is not None
            assert batch.filename == "sejusp-lote.csv"
            assert batch.file_hash
            assert batch.source_system == "RELATORIO_SEJUSP"
            assert batch.total_rows == 2
            assert batch.valid_rows == 1
            assert batch.invalid_rows == 1
            assert batch.inserted_rows == 1
            assert batch.status == "concluido"
            rejected = db.scalar(select(RejectedImportLine).where(RejectedImportLine.import_batch_id == batch.id))
            assert rejected is not None
            assert rejected.row_number == 3
            assert "abertura_em inválido" in json.loads(rejected.reasons)
            row = db.scalar(select(Occurrence).where(Occurrence.source_id == source_id))
            assert row is not None
            assert row.import_batch_id == batch.id
        finally:
            db.close()
    finally:
        batch_ids = [result["id_lote_importacao"]] if result else []
        _cleanup_imported_test_data([source_id], [], batch_ids)


def test_legacy_sejusp_occurrences_receive_import_batch():
    source_id = f"LEGADO-{uuid4()}"
    db = SessionLocal()
    batch_id = None
    try:
        db.add(
            Occurrence(
                source="RELATORIO_SEJUSP",
                source_id=source_id,
                opened_at=datetime(2025, 2, 1, 8, 20, tzinfo=timezone.utc),
                registered_at=datetime(2025, 2, 1, 8, 10, tzinfo=timezone.utc),
                type_name="REMOCAO AO PS",
                municipality="Campo Grande",
                status="importada",
                judicial_secret=False,
            )
        )
        db.commit()

        import_audit_service.ensure_legacy_import_batches(db)
        row = db.scalar(select(Occurrence).where(Occurrence.source_id == source_id))
        assert row is not None
        assert row.import_batch_id is not None
        batch_id = row.import_batch_id
        batch = db.get(ImportBatch, batch_id)
        assert batch is not None
        assert batch.filename == "importacao-legada-sejusp"
        assert batch.status == "legado"
        assert batch.total_rows >= 1
    finally:
        db.close()
        _cleanup_imported_test_data([source_id], [], [batch_id] if batch_id else [])


def test_analytics_sejusp_source_applies_cross_filters():
    source_id = f"ANALYTICS-{uuid4()}"
    source_id_outro = f"ANALYTICS-OUTRO-{uuid4()}"
    unit_name = f"UNIDADE ANALYTICS {uuid4()}"
    other_unit_name = f"UNIDADE ANALYTICS OUTRA {uuid4()}"
    type_name = f"TIPO ANALYTICS {uuid4()}"
    other_type_name = f"TIPO ANALYTICS OUTRO {uuid4()}"
    subtype_name = f"SUBTIPO ANALYTICS {uuid4()}"
    other_subtype_name = f"SUBTIPO ANALYTICS OUTRO {uuid4()}"
    municipality = f"Municipio Analytics {uuid4()}"
    other_municipality = f"Municipio Analytics Outro {uuid4()}"
    db = SessionLocal()
    try:
        unit = Unit(name=unit_name, command="TESTE", active=True)
        other_unit = Unit(name=other_unit_name, command="TESTE", active=True)
        db.add_all([unit, other_unit])
        db.flush()
        db.add_all([
            Occurrence(
                source="RELATORIO_SEJUSP",
                source_id=source_id,
                opened_at=datetime(2025, 1, 15, 14, 30, tzinfo=FUSO_LOCAL),
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
            ),
            Occurrence(
                source="RELATORIO_SEJUSP",
                source_id=source_id_outro,
                opened_at=datetime(2025, 1, 16, 8, 30, tzinfo=FUSO_LOCAL),
                type_name=other_type_name,
                group_name="GRUPO ANALYTICS",
                subtype_name=other_subtype_name,
                municipality=other_municipality,
                neighborhood="Centro",
                latitude=-21.45,
                longitude=-55.62,
                unit_id=other_unit.id,
                status="importada",
                judicial_secret=False,
            ),
        ])
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

            scoped_filters = client.get("/api/v1/analytics/filters", params={"source": "sejusp", "municipality": municipality}).json()
            assert type_name in scoped_filters["types"]
            assert other_type_name not in scoped_filters["types"]
            assert unit_name in scoped_filters["units"]
            assert other_unit_name not in scoped_filters["units"]
            assert subtype_name in scoped_filters["subtypes"]
            assert other_subtype_name not in scoped_filters["subtypes"]
            assert {"Madrugada", "Manhã", "Tarde", "Noite"}.issuperset(scoped_filters["shifts"])

            params = {
                "source": "sejusp",
                "period": "2025-01",
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
        _cleanup_imported_test_data([source_id, source_id_outro], [unit_name, other_unit_name])

def test_sejusp_analytics_uses_registration_date_year_instead_of_filename():
    source_id = f"ANO-REG-{uuid4()}/2025"
    unit_name = f"UNIDADE ANO REGISTRO {uuid4()}"
    type_name = f"TIPO ANO REGISTRO {uuid4()}"
    municipality = f"Municipio Ano Registro {uuid4()}"
    content = (
        "Nº/ANO,DATA DO REGISTRO,HORA DO REGISTRO,DATA DO FATO,HORA DO FATO,FATO,UNIDADE DE ORIGEM,MUNICÍPIO\n"
        f"{source_id},03/08/2026,19:15,31/12/2025,23:50,{type_name},{unit_name},{municipality}\n"
    ).encode("utf-8")

    try:
        with TestClient(app) as client:
            preview = client.post(
                "/api/v1/imports/preview",
                files={"file": ("relatorio_2025.csv", content, "text/csv")},
            ).json()
            commit = client.post(
                "/api/v1/imports",
                files={"file": ("relatorio_2025.csv", content, "text/csv")},
            ).json()
            batch = client.get(f"/api/v1/imports/lotes/{commit['id_lote_importacao']}").json()
            filters = client.get("/api/v1/analytics/filters", params={"source": "sejusp"}).json()
            params = {"source": "sejusp", "period": "2026-08", "type": type_name, "municipality": municipality}
            overview = client.get("/api/v1/analytics/overview", params=params).json()
            monthly = client.get("/api/v1/analytics/monthly", params=params).json()
            hours = client.get("/api/v1/analytics/hours", params=params).json()

        period_by_key = {item["key"]: item for item in filters["periods"]}
        assert preview["registration_years"] == [2026]
        assert preview["registration_periods"] == ["2026-08"]
        assert preview["valid_rows_without_registration_date"] == 0
        assert commit["registration_years"] == [2026]
        assert commit["registration_periods"] == ["2026-08"]
        assert commit["valid_rows_without_registration_date"] == 0
        assert commit["inserted_rows"] == 1
        assert batch["periodos_registro"] == ["2026-08"]
        assert batch["linhas_validas_sem_data_registro"] == 0
        assert "ano-2026" in period_by_key
        assert period_by_key["2026-08"]["label"] == "Ago/2026"
        assert overview["total"] == 1
        assert overview["applied_filters"]["period"] == "Ago/2026"
        assert overview["coverage"]["months"] == ["Ago/2026"]
        assert [item["mes"] for item in monthly["items"]] == ["Ago/2026"]
        assert monthly["items"][0]["total"] == 1
        assert hours["items"][19] == 1
        assert hours["items"][23] == 0
    finally:
        _cleanup_imported_test_data([source_id], [unit_name])


def test_sejusp_compares_selected_period_with_same_period_from_previous_year():
    previous_year_id = f"COMPARACAO-FEV-ANTERIOR-{uuid4()}"
    january_id = f"COMPARACAO-JAN-{uuid4()}"
    february_id = f"COMPARACAO-FEV-{uuid4()}"
    unit_name = f"UNIDADE COMPARACAO {uuid4()}"
    type_name = f"TIPO COMPARACAO {uuid4()}"
    municipality = f"Municipio Comparacao {uuid4()}"
    batch_id = None
    content = (
        "Nº/ANO,DATA DO REGISTRO,HORA DO REGISTRO,DATA DO FATO,HORA DO FATO,FATO,UNIDADE DE ORIGEM,MUNICÍPIO\n"
        f"{previous_year_id},15/02/2024,10:00,15/02/2024,10:00,{type_name},{unit_name},{municipality}\n"
        f"{january_id},15/01/2025,10:00,15/01/2025,10:00,{type_name},{unit_name},{municipality}\n"
        f"{february_id},15/02/2025,10:00,15/02/2025,10:00,{type_name},{unit_name},{municipality}\n"
    ).encode("utf-8")

    try:
        with TestClient(app) as client:
            commit = client.post(
                "/api/v1/imports",
                files={"file": ("comparacao_2025.csv", content, "text/csv")},
            ).json()
            batch_id = commit["id_lote_importacao"]
            params = {
                "source": "sejusp",
                "period": "2025-02",
                "type": type_name,
                "municipality": municipality,
            }
            overview = client.get("/api/v1/analytics/overview", params=params).json()
            monthly = client.get("/api/v1/analytics/monthly", params=params).json()

        comparison = overview["comparison"]
        assert commit["inserted_rows"] == 3
        assert comparison["available"] is True
        assert comparison["current_label"] == "Fev/2025"
        assert comparison["baseline_label"] == "Fev/2024"
        assert comparison["current_total"] == 1
        assert comparison["baseline_total"] == 1
        assert comparison["delta_abs"] == 0
        assert comparison["delta_pct"] == 0
        assert overview["delta_pct"] == 0
        assert monthly["comparison"] == [{
            "current_month": "Fev/2025",
            "baseline_month": "Fev/2024",
            "current": 1,
            "baseline": 1,
            "delta": 0,
        }]
    finally:
        _cleanup_imported_test_data(
            [previous_year_id, january_id, february_id],
            [unit_name],
            [batch_id] if batch_id else [],
        )


def test_analytics_exposes_only_sejusp_source():
    with TestClient(app) as client:
        filters = client.get("/api/v1/analytics/filters").json()
        overview = client.get("/api/v1/analytics/overview").json()
        assert filters["sources"] == [{"key": "sejusp", "label": "SEJUSP importado"}]
        assert filters["source_scope"] == "sejusp_importado"
        assert overview["source_scope"] == "sejusp_importado"


def test_analytics_rejects_removed_historical_source():
    with TestClient(app) as client:
        r = client.get("/api/v1/analytics/overview?source=historico")
        data = r.json()
        assert r.status_code == 400
        assert data["detail"]["code"] == "INVALID_FILTER"
        assert data["detail"]["errors"][0]["allowed"] == ["sejusp"]


def test_sejusp_comparison_is_explicitly_unavailable():
    with SessionLocal() as db:
        db.add(Occurrence(
            source="RELATORIO_SEJUSP",
            source_id="COMPARACAO-SEM-BASE",
            opened_at=datetime(2025, 2, 15, 10, tzinfo=FUSO_LOCAL),
            type_name="TIPO TESTE",
            municipality="MUNICIPIO TESTE",
        ))
        db.commit()
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/overview").json()
        comparison = data["comparison"]
        assert comparison["available"] is False
        assert comparison["baseline_total"] is None
        assert comparison["reason"] == "Não há cobertura completa para o período imediatamente anterior."


def test_empty_database_returns_empty_dashboard():
    with TestClient(app) as client:
        data = client.get("/api/v1/analytics/overview").json()
        assert data["total"] == 0
        assert data["comparison"]["available"] is False
        assert data["comparison"]["reason"] == "O recorte atual não possui meses válidos para comparação."


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


def test_csv_preview_rejects_filename_larger_than_database_limit():
    filename = f"{'a' * 252}.csv"
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": (filename, b"id_origem\nEX-001\n", "text/csv")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Nome de arquivo inválido"


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


def test_import_upload_limit_cannot_exceed_512_mb():
    try:
        Settings(limite_importacao_mb=513, _env_file=None)
    except ValidationError:
        return
    raise AssertionError("limite acima de 512 MB deveria ser rejeitado")


def test_import_routes_run_outside_event_loop():
    assert inspect.iscoroutinefunction(imports_endpoint.import_preview) is False
    assert inspect.iscoroutinefunction(imports_endpoint.csv_preview) is False
    assert inspect.iscoroutinefunction(imports_endpoint.create_import) is False


def test_import_rejects_known_oversized_file_without_reading(monkeypatch):
    class UnreadableFile:
        def seek(self, *_):
            raise AssertionError("arquivo acima do limite não deveria ser aberto")

        def read(self, *_):
            raise AssertionError("arquivo acima do limite não deveria ser lido")

    class OversizedUpload:
        filename = "grande.csv"
        content_type = "text/csv"
        size = 65
        file = UnreadableFile()

    monkeypatch.setattr(imports_endpoint, "MAX_IMPORT_MEGABYTES", 1)
    monkeypatch.setattr(imports_endpoint, "MAX_IMPORT_BYTES", 64)
    try:
        imports_endpoint._prepare_upload(OversizedUpload())
    except HTTPException as exc:
        assert exc.status_code == 413
        assert exc.detail == "Arquivo excede o limite de 1 MB"
        return
    raise AssertionError("arquivo acima do limite deveria ser rejeitado")


def test_prepare_upload_reads_in_chunks_and_calculates_hash():
    content = b"id_origem,abertura_em,municipio,tipo\nEX-1,2026-01-01,CG,TESTE\n"

    class ChunkOnlyFile(BytesIO):
        def read(self, size=-1):
            assert size == imports_endpoint.UPLOAD_READ_CHUNK_BYTES
            return super().read(size)

    class Upload:
        filename = "arquivo.csv"
        content_type = "text/csv"
        size = None
        file = ChunkOnlyFile(content)

    filename, source, file_hash = imports_endpoint._prepare_upload(Upload())

    assert filename == "arquivo.csv"
    assert source.tell() == 0
    assert file_hash == hashlib.sha256(content).hexdigest()


def test_prepare_upload_rejects_unknown_size_when_stream_exceeds_limit(monkeypatch):
    class Upload:
        filename = "grande.csv"
        content_type = "text/csv"
        size = None
        file = BytesIO(b"x" * 65)

    monkeypatch.setattr(imports_endpoint, "MAX_IMPORT_MEGABYTES", 1)
    monkeypatch.setattr(imports_endpoint, "MAX_IMPORT_BYTES", 64)
    monkeypatch.setattr(imports_endpoint, "UPLOAD_READ_CHUNK_BYTES", 16)

    try:
        imports_endpoint._prepare_upload(Upload())
    except HTTPException as exc:
        assert exc.status_code == 413
        assert exc.detail == "Arquivo excede o limite de 1 MB"
        return
    raise AssertionError("fluxo sem tamanho conhecido deveria respeitar o limite")


def test_csv_stream_preview_matches_legacy_parser_without_unbounded_read():
    content = (
        "titulo do relatorio\n"
        "Nº/ANO;DATA DO REGISTRO;HORA DO REGISTRO;DATA DO FATO;HORA DO FATO;"
        "FATO;UNIDADE DE ORIGEM;MUNICÍPIO\n"
        "200/2026;01/10/2026;08:10;01/10/2026;08:00;INCÊNDIO;1º GBM;Campo Grande\n"
    ).encode("cp1252")

    class ChunkOnlyFile(BytesIO):
        def read(self, size=-1):
            assert size >= 0, "CSV incremental não deve executar leitura ilimitada"
            return super().read(size)

    legacy = import_service.preview_import(content, "comparacao.csv")
    streamed = import_service.preview_import_stream(
        ChunkOnlyFile(content), "comparacao.csv"
    )

    assert streamed == legacy
    assert streamed["total_rows"] == 1
    assert streamed["valid_rows"] == 1
    assert streamed["registration_years"] == [2026]


def test_csv_preview_light_mode_preserves_result_without_retaining_records():
    header = "Nº/ANO,DATA DO REGISTRO,DATA DO FATO,FATO,MUNICÍPIO\n"
    invalid_rows = "".join(
        f"INVALIDA-{index},01/10/2025,01/10/2025,INCENDIO,\n"
        for index in range(60)
    )
    valid_row = "VALIDA-2026,01/10/2026,01/10/2026,INCENDIO,Campo Grande\n"
    content = (header + invalid_rows + valid_row).encode("utf-8")

    complete = import_service._parsed_import_stream(
        BytesIO(content),
        "memoria.csv",
        retain_records=True,
    )
    lightweight = import_service._parsed_import_stream(
        BytesIO(content),
        "memoria.csv",
        retain_records=False,
    )

    assert import_service._public_preview(lightweight) == import_service._public_preview(
        complete
    )
    assert len(complete["_records"]) == 61
    assert lightweight["_records"] == []
    assert lightweight["_valid_source_ids"] == ["VALIDA-2026"]
    assert len(lightweight["issues"]) == 50
    assert lightweight["registration_years"] == [2026]
    assert lightweight["registration_periods"] == ["2026-10"]
    assert "A prévia exibe 50 de 60 linha(s) inválida(s)" in lightweight["warnings"]


def test_preview_nao_inventa_periodo_quando_data_de_registro_esta_ausente():
    content = (
        "Nº/ANO,DATA DO REGISTRO,DATA DO FATO,FATO,MUNICÍPIO\n"
        "SEM-REGISTRO,,01/10/2025,INCENDIO,Campo Grande\n"
    ).encode("utf-8")

    preview = import_service.preview_import(content, "relatorio_2025.csv")

    assert preview["registration_years"] == []
    assert preview["registration_periods"] == []
    assert preview["valid_rows_without_registration_date"] == 1
    assert any("fora da cobertura temporal" in warning for warning in preview["warnings"])


def test_historico_preserva_cobertura_desconhecida_e_tolera_json_invalido():
    lote = ImportBatch(
        filename="legado.csv",
        file_hash="a" * 64,
        file_format="csv",
        source_profile="RELATORIO_SEJUSP",
        source_system="RELATORIO_SEJUSP",
        status="legado",
        registration_periods=None,
        valid_rows_without_registration_date=None,
    )

    assert import_audit_service._batch_item(lote)["periodos_registro"] is None
    lote.registration_periods = "nao-json"
    assert import_audit_service._batch_item(lote)["periodos_registro"] == []


def test_import_preview_rejects_parallel_processing(monkeypatch):
    class OccupiedSemaphore:
        def acquire(self, blocking=False):
            assert blocking is False
            return False

        def release(self):
            raise AssertionError("semáforo não adquirido não pode ser liberado")

    monkeypatch.setattr(
        imports_endpoint, "_IMPORT_PROCESSING_SEMAPHORE", OccupiedSemaphore()
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports/preview",
            files={"file": ("ocupada.csv", b"id_origem\nEX-001\n", "text/csv")},
        )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "2"
    assert "Outra importação" in response.json()["detail"]


def test_import_commit_returns_503_when_database_lock_is_busy(monkeypatch):
    def busy_commit(*_args, **_kwargs):
        raise import_service.ImportInProgressError("confirmação concorrente")

    monkeypatch.setattr(imports_endpoint, "commit_import_stream", busy_commit)
    content = (
        "id_origem,abertura_em,municipio,tipo\n"
        "LOCK-1,2026-10-01,Campo Grande,INCENDIO\n"
    ).encode("utf-8")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/imports",
            files={"file": ("concorrente.csv", content, "text/csv")},
        )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "2"
    assert response.json()["detail"] == "confirmação concorrente"


def test_import_transaction_lock_rolls_back_when_postgres_is_busy():
    class Dialect:
        name = "postgresql"

    class Bind:
        dialect = Dialect()

    class BusyDatabase:
        rolled_back = False

        def get_bind(self):
            return Bind()

        def scalar(self, statement):
            assert "pg_try_advisory_xact_lock" in str(statement)
            return False

        def rollback(self):
            self.rolled_back = True

    database = BusyDatabase()
    try:
        import_service._acquire_import_transaction_lock(database)
    except import_service.ImportInProgressError:
        assert database.rolled_back is True
        return
    raise AssertionError("lock PostgreSQL ocupado deveria impedir a confirmação")


def test_import_transaction_lock_is_not_required_outside_postgres():
    class Dialect:
        name = "sqlite"

    class Bind:
        dialect = Dialect()

    class SQLiteDatabase:
        def get_bind(self):
            return Bind()

        def scalar(self, _statement):
            raise AssertionError("SQLite não deve executar advisory lock")

    import_service._acquire_import_transaction_lock(SQLiteDatabase())


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
