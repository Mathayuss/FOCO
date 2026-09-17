from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401


config = context.config
settings = get_settings()

config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
TABELAS_FOCO = set(target_metadata.tables)


def incluir_nome(
    nome: str | None,
    tipo: str,
    nomes_pais: dict[str, str | None],
) -> bool:
    """Ignora tabelas gerenciadas pelas extensoes PostGIS durante autogeracao."""
    if tipo == "schema":
        return nome in {None, "public"}
    if tipo == "table":
        return (
            nomes_pais.get("schema_name") in {None, "public"}
            and nome in TABELAS_FOCO
        )
    return True


def executar_migracoes_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_name=incluir_nome,
    )

    with context.begin_transaction():
        context.run_migrations()


def executar_migracoes_conexao(conexao) -> None:
    context.configure(
        connection=conexao,
        target_metadata=target_metadata,
        compare_type=True,
        include_name=incluir_nome,
    )

    with context.begin_transaction():
        context.run_migrations()


def executar_migracoes_online() -> None:
    conexao = config.attributes.get("connection")
    if conexao is not None:
        executar_migracoes_conexao(conexao)
        return

    conectavel = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with conectavel.connect() as conexao:
        executar_migracoes_conexao(conexao)


if context.is_offline_mode():
    executar_migracoes_offline()
else:
    executar_migracoes_online()
