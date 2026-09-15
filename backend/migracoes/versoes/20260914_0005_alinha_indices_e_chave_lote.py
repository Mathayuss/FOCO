"""alinha indices relacionais e chave estrangeira do lote

Revisao: 20260914_0005
Revisao anterior: 20260914_0004
Data: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260914_0005"
down_revision: Union[str, Sequence[str], None] = "20260914_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_ocorrencia_id_lote_importacao",
        "ocorrencia",
        ["id_lote_importacao"],
    )
    op.create_index(
        "ix_ocorrencia_id_unidade_operacional",
        "ocorrencia",
        ["id_unidade_operacional"],
    )
    op.create_index(
        "ix_viatura_id_unidade_operacional",
        "viatura",
        ["id_unidade_operacional"],
    )
    op.create_foreign_key(
        "fk_ocorrencia_lote_importacao",
        "ocorrencia",
        "lote_importacao",
        ["id_lote_importacao"],
        ["id_lote_importacao"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_ocorrencia_lote_importacao",
        "ocorrencia",
        type_="foreignkey",
    )
    op.drop_index("ix_viatura_id_unidade_operacional", table_name="viatura")
    op.drop_index("ix_ocorrencia_id_unidade_operacional", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_id_lote_importacao", table_name="ocorrencia")
