"""Seleciona o banco descartavel antes de importar a aplicacao."""

import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--postgres-testes",
        action="store_true",
        help="Usa exclusivamente o PostGIS descartavel de compose.testes.yml.",
    )


def pytest_configure(config):
    if "app.db.session" in sys.modules or "app.main" in sys.modules:
        raise pytest.UsageError("A aplicacao foi importada antes do isolamento do banco.")

    config._foco_env_anterior = {
        chave: os.environ.get(chave) for chave in ("DATABASE_URL", "AMBIENTE")
    }
    config._foco_temporario = TemporaryDirectory(prefix="foco-testes-")
    if config.getoption("--postgres-testes"):
        url = "postgresql+psycopg://foco_testes@bd-testes:5432/foco_testes"
    else:
        caminho = Path(config._foco_temporario.name) / "testes.db"
        url = f"sqlite:///{caminho}"

    # Nunca herdar DATABASE_URL ou o arquivo .env da aplicacao operacional.
    config._foco_database_url = url
    os.environ["DATABASE_URL"] = url
    os.environ["AMBIENTE"] = "teste"
    from app.core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def banco_isolado(request):
    from alembic import command
    from sqlalchemy import MetaData, Table, event
    from app.db.base import Base
    from app.db.migrations import configuracao_migracoes
    from app.db.session import engine
    from app.services import sejusp_analytics_service
    import app.models  # noqa: F401

    if engine.url.render_as_string(hide_password=False) != request.config._foco_database_url:
        pytest.fail("Conexao fora do banco de testes; operacao cancelada.")

    def ativar_chaves_estrangeiras(conexao, _registro):
        conexao.execute("PRAGMA foreign_keys=ON")

    if engine.dialect.name == "sqlite":
        engine.dispose()
        event.listen(engine, "connect", ativar_chaves_estrangeiras)

    sejusp_analytics_service.clear_cache()
    try:
        with engine.begin() as conexao:
            config = configuracao_migracoes()
            config.attributes["connection"] = conexao
            command.upgrade(config, "head")
        yield
    finally:
        sejusp_analytics_service.clear_cache()
        Base.metadata.drop_all(engine)
        Table("alembic_version", MetaData()).drop(engine, checkfirst=True)
        engine.dispose()
        if engine.dialect.name == "sqlite":
            event.remove(engine, "connect", ativar_chaves_estrangeiras)


def pytest_unconfigure(config):
    sessao = sys.modules.get("app.db.session")
    if sessao is not None:
        sessao.engine.dispose()
    temporario = getattr(config, "_foco_temporario", None)
    if temporario is not None:
        temporario.cleanup()
    for chave, valor in getattr(config, "_foco_env_anterior", {}).items():
        if valor is None:
            os.environ.pop(chave, None)
        else:
            os.environ[chave] = valor
    configuracao = sys.modules.get("app.core.config")
    if configuracao is not None:
        configuracao.get_settings.cache_clear()
