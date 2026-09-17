from datetime import datetime, timezone

from alembic import command
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import MetaData, Table, event, inspect, select

from app.db.base import Base
from app.db.migrations import configuracao_migracoes, validar_migracoes
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.occurrence import Occurrence


def test_cadeia_de_migracoes_corresponde_aos_modelos():
    with engine.begin() as conexao:
        config = configuracao_migracoes()
        config.attributes["connection"] = conexao
        command.upgrade(config, "head")
        command.check(config)
    validar_migracoes(engine)


def test_migracao_0005_preserva_campos_e_dados_ao_reparar_chave():
    with SessionLocal() as db:
        db.add(Occurrence(
            source="RELATORIO_SEJUSP",
            source_id="MIGRACAO-PRESERVAR-DADOS",
            opened_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            registered_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            type_name="TIPO A PRESERVAR",
            municipality="MUNICIPIO A PRESERVAR",
            source_payload='{"original":"preservado"}',
        ))
        db.commit()

    with engine.begin() as conexao:
        operacoes = Operations(MigrationContext.configure(conexao))
        with operacoes.batch_alter_table("ocorrencia") as lote:
            lote.drop_constraint("fk_ocorrencia_lote_importacao", type_="foreignkey")
        config = configuracao_migracoes()
        config.attributes["connection"] = conexao
        command.stamp(config, "20260914_0004")
        command.upgrade(config, "head")
        command.check(config)
        command.downgrade(config, "20260914_0004")
        command.upgrade(config, "head")
        command.check(config)

    colunas = {coluna["name"] for coluna in inspect(engine).get_columns("ocorrencia")}
    assert colunas == set(Base.metadata.tables["ocorrencia"].columns.keys())
    with SessionLocal() as db:
        row = db.scalar(select(Occurrence).where(Occurrence.source_id == "MIGRACAO-PRESERVAR-DADOS"))
        assert row is not None
        assert row.type_name == "TIPO A PRESERVAR"
        assert row.municipality == "MUNICIPIO A PRESERVAR"
        assert row.source_payload == '{"original":"preservado"}'


def test_startup_recusa_banco_sem_revisao():
    Table("alembic_version", MetaData()).drop(engine)
    with pytest.raises(RuntimeError, match="Banco desatualizado"):
        with TestClient(app):
            pass


def test_startup_recusa_revisao_anterior():
    with engine.begin() as conexao:
        config = configuracao_migracoes()
        config.attributes["connection"] = conexao
        command.stamp(config, "20260914_0004")
    with pytest.raises(RuntimeError, match="Banco desatualizado"):
        with TestClient(app):
            pass


def test_startup_nao_executa_alteracoes_de_schema():
    comandos = []

    def registrar(_conexao, _cursor, comando, _parametros, _contexto, _executemany):
        comandos.append(comando.lstrip().split()[0].upper())

    event.listen(engine, "before_cursor_execute", registrar)
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/health").status_code == 200
    finally:
        event.remove(engine, "before_cursor_execute", registrar)
    assert not {"CREATE", "ALTER", "DROP"}.intersection(comandos)
