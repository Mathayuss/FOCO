from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

COLUNAS_OCORRENCIA_INCREMENTAIS = {
    "registro_em": {
        "sqlite": "DATETIME",
        "postgresql": "TIMESTAMP WITH TIME ZONE",
    },
    "codigo_ibge": {
        "sqlite": "VARCHAR(20)",
        "postgresql": "VARCHAR(20)",
    },
    "segredo_de_justica": {
        "sqlite": "BOOLEAN NOT NULL DEFAULT 0",
        "postgresql": "BOOLEAN NOT NULL DEFAULT false",
    },
    "dados_origem": {
        "sqlite": "TEXT",
        "postgresql": "TEXT",
    },
}


def garantir_colunas_incrementais(engine: Engine) -> None:
    with engine.begin() as conn:
        inspetor = inspect(conn)
        if not inspetor.has_table("ocorrencia"):
            return
        existentes = {coluna["name"] for coluna in inspetor.get_columns("ocorrencia")}
        dialeto = conn.dialect.name
        for nome, definicoes in COLUNAS_OCORRENCIA_INCREMENTAIS.items():
            if nome in existentes:
                continue
            definicao = definicoes.get(dialeto)
            if not definicao:
                continue
            conn.execute(text(f'alter table ocorrencia add column {nome} {definicao}'))
