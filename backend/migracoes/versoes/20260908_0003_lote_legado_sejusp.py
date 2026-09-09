"""cria lote legado para ocorrencias sejusp existentes

Revisão: 20260908_0003
Revisão anterior: 20260908_0002
Data: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260908_0003"
down_revision: Union[str, Sequence[str], None] = "20260908_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    total = bind.execute(sa.text("""
        select count(*)
        from ocorrencia
        where sistema_origem = :sistema_origem
          and id_lote_importacao is null
    """), {"sistema_origem": "RELATORIO_SEJUSP"}).scalar()
    if not total:
        return

    lote = sa.table(
        "lote_importacao",
        sa.column("nome_arquivo"),
        sa.column("hash_arquivo"),
        sa.column("formato_arquivo"),
        sa.column("perfil_origem"),
        sa.column("sistema_origem"),
        sa.column("total_linhas"),
        sa.column("linhas_validas"),
        sa.column("linhas_invalidas"),
        sa.column("linhas_inseridas"),
        sa.column("linhas_duplicadas"),
        sa.column("linhas_sensiveis"),
        sa.column("linhas_coordenada_invalida"),
        sa.column("linhas_sem_coordenada"),
        sa.column("situacao"),
        sa.column("avisos"),
        sa.column("erro"),
        sa.column("iniciado_em"),
        sa.column("concluido_em"),
    )
    now = sa.func.now() if bind.dialect.name == "postgresql" else sa.text("CURRENT_TIMESTAMP")
    result = bind.execute(
        sa.insert(lote).values(
            nome_arquivo="importacao-legada-sejusp",
            hash_arquivo="legado".ljust(64, "0"),
            formato_arquivo="desconhecido",
            perfil_origem="RELATORIO_SEJUSP",
            sistema_origem="RELATORIO_SEJUSP",
            total_linhas=int(total),
            linhas_validas=int(total),
            linhas_invalidas=0,
            linhas_inseridas=int(total),
            linhas_duplicadas=0,
            linhas_sensiveis=0,
            linhas_coordenada_invalida=0,
            linhas_sem_coordenada=0,
            situacao="legado",
            avisos="[\"Lote criado automaticamente para ocorrências anteriores à rastreabilidade por lote.\"]",
            erro=None,
            iniciado_em=now,
            concluido_em=now,
        )
    )
    batch_id = result.inserted_primary_key[0] if result.inserted_primary_key else None
    if batch_id is None:
        batch_id = bind.execute(sa.text("select max(id_lote_importacao) from lote_importacao")).scalar()
    bind.execute(sa.text("""
        update ocorrencia
        set id_lote_importacao = :id_lote_importacao
        where sistema_origem = :sistema_origem
          and id_lote_importacao is null
    """), {"id_lote_importacao": batch_id, "sistema_origem": "RELATORIO_SEJUSP"})


def downgrade() -> None:
    bind = op.get_bind()
    ids = bind.execute(sa.text("""
        select id_lote_importacao
        from lote_importacao
        where nome_arquivo = :nome_arquivo
          and hash_arquivo = :hash_arquivo
          and situacao = :situacao
    """), {"nome_arquivo": "importacao-legada-sejusp", "hash_arquivo": "legado".ljust(64, "0"), "situacao": "legado"}).scalars().all()
    for batch_id in ids:
        bind.execute(sa.text("update ocorrencia set id_lote_importacao = null where id_lote_importacao = :id"), {"id": batch_id})
        bind.execute(sa.text("delete from lote_importacao where id_lote_importacao = :id"), {"id": batch_id})
