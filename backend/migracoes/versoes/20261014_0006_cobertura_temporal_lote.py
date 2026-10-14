"""registra cobertura temporal declarada por lote

Revisao: 20261014_0006
Revisao anterior: 20260914_0005
Data: 2026-10-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261014_0006"
down_revision: Union[str, Sequence[str], None] = "20260914_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lote_importacao", sa.Column("periodos_registro", sa.Text(), nullable=True))
    op.add_column(
        "lote_importacao",
        sa.Column("linhas_validas_sem_data_registro", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lote_importacao", "linhas_validas_sem_data_registro")
    op.drop_column("lote_importacao", "periodos_registro")
