from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Engine


def configuracao_migracoes() -> Config:
    raiz = Path(__file__).resolve().parents[2]
    config = Config(str(raiz / "alembic.ini"))
    config.set_main_option("script_location", str(raiz / "migracoes"))
    return config


def validar_migracoes(engine: Engine) -> None:
    esperadas = set(ScriptDirectory.from_config(configuracao_migracoes()).get_heads())
    with engine.connect() as conexao:
        atuais = set(MigrationContext.configure(conexao).get_current_heads())
    if atuais != esperadas:
        raise RuntimeError(
            "Banco desatualizado. Execute 'python -m alembic upgrade head' "
            "na pasta backend antes de iniciar a API. "
            f"Revisao atual: {', '.join(sorted(atuais)) or 'sem revisao'}; "
            f"esperada: {', '.join(sorted(esperadas))}."
        )
