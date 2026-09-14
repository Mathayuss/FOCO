"""remove dados demonstrativos

Revisão: 20260914_0004
Revisão anterior: 20260908_0003
Data: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260914_0004"
down_revision: Union[str, Sequence[str], None] = "20260908_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORIGEM_DEMO = "DADO_DEMO"


def upgrade() -> None:
    bind = op.get_bind()
    parametros = {"origem_demo": ORIGEM_DEMO}
    ids_viaturas = bind.execute(
        sa.text("""
            select distinct ov.id_viatura
            from ocorrencia_viatura ov
            join ocorrencia o on o.id_ocorrencia = ov.id_ocorrencia
            where o.sistema_origem = :origem_demo
              and not exists (
                  select 1
                  from ocorrencia_viatura outro_vinculo
                  join ocorrencia outra on outra.id_ocorrencia = outro_vinculo.id_ocorrencia
                  where outro_vinculo.id_viatura = ov.id_viatura
                    and outra.sistema_origem <> :origem_demo
              )
        """),
        parametros,
    ).scalars().all()

    bind.execute(sa.text("""
        delete from ocorrencia_viatura
        where id_ocorrencia in (
            select id_ocorrencia from ocorrencia where sistema_origem = :origem_demo
        )
    """), parametros)
    bind.execute(
        sa.text("delete from ocorrencia where sistema_origem = :origem_demo"),
        parametros,
    )

    for id_viatura in ids_viaturas:
        bind.execute(sa.text("""
            delete from viatura
            where id_viatura = :id_viatura
              and not exists (
                  select 1 from ocorrencia_viatura where id_viatura = :id_viatura
              )
        """), {"id_viatura": id_viatura})


def downgrade() -> None:
    # Dados fictícios removidos não devem ser recriados por downgrade.
    pass
