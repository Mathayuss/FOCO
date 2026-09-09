"""lote de importacao e linhas rejeitadas

Revisão: 20260908_0002
Revisão anterior: 20260907_0001
Data: 2026-09-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260908_0002"
down_revision: Union[str, Sequence[str], None] = "20260907_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lote_importacao",
        sa.Column("id_lote_importacao", sa.Integer(), nullable=False),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("hash_arquivo", sa.String(length=64), nullable=False),
        sa.Column("formato_arquivo", sa.String(length=20), nullable=False),
        sa.Column("perfil_origem", sa.String(length=80), nullable=False),
        sa.Column("sistema_origem", sa.String(length=80), nullable=False),
        sa.Column("total_linhas", sa.Integer(), nullable=False),
        sa.Column("linhas_validas", sa.Integer(), nullable=False),
        sa.Column("linhas_invalidas", sa.Integer(), nullable=False),
        sa.Column("linhas_inseridas", sa.Integer(), nullable=False),
        sa.Column("linhas_duplicadas", sa.Integer(), nullable=False),
        sa.Column("linhas_sensiveis", sa.Integer(), nullable=False),
        sa.Column("linhas_coordenada_invalida", sa.Integer(), nullable=False),
        sa.Column("linhas_sem_coordenada", sa.Integer(), nullable=False),
        sa.Column("situacao", sa.String(length=40), nullable=False),
        sa.Column("avisos", sa.Text(), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id_lote_importacao"),
    )
    op.create_index("ix_lote_importacao_hash_arquivo", "lote_importacao", ["hash_arquivo"], unique=False)
    op.create_index("ix_lote_importacao_formato_arquivo", "lote_importacao", ["formato_arquivo"], unique=False)
    op.create_index("ix_lote_importacao_perfil_origem", "lote_importacao", ["perfil_origem"], unique=False)
    op.create_index("ix_lote_importacao_sistema_origem", "lote_importacao", ["sistema_origem"], unique=False)
    op.create_index("ix_lote_importacao_situacao", "lote_importacao", ["situacao"], unique=False)
    op.create_index("ix_lote_importacao_iniciado_em", "lote_importacao", ["iniciado_em"], unique=False)

    op.create_table(
        "linha_importacao_rejeitada",
        sa.Column("id_linha_importacao_rejeitada", sa.Integer(), nullable=False),
        sa.Column("id_lote_importacao", sa.Integer(), nullable=False),
        sa.Column("numero_linha", sa.Integer(), nullable=False),
        sa.Column("motivos", sa.Text(), nullable=False),
        sa.Column("dados_origem", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["id_lote_importacao"], ["lote_importacao.id_lote_importacao"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_linha_importacao_rejeitada"),
    )
    op.create_index("ix_linha_importacao_rejeitada_id_lote_importacao", "linha_importacao_rejeitada", ["id_lote_importacao"], unique=False)
    op.create_index("ix_linha_importacao_rejeitada_numero_linha", "linha_importacao_rejeitada", ["numero_linha"], unique=False)

    with op.batch_alter_table("ocorrencia") as batch_op:
        batch_op.add_column(sa.Column("id_lote_importacao", sa.Integer(), nullable=True))
        batch_op.create_index("ix_ocorrencia_id_lote_importacao", ["id_lote_importacao"], unique=False)
        batch_op.create_foreign_key(
            "fk_ocorrencia_lote_importacao",
            "lote_importacao",
            ["id_lote_importacao"],
            ["id_lote_importacao"],
        )


def downgrade() -> None:
    with op.batch_alter_table("ocorrencia") as batch_op:
        batch_op.drop_constraint("fk_ocorrencia_lote_importacao", type_="foreignkey")
        batch_op.drop_index("ix_ocorrencia_id_lote_importacao")
        batch_op.drop_column("id_lote_importacao")

    op.drop_index("ix_linha_importacao_rejeitada_numero_linha", table_name="linha_importacao_rejeitada")
    op.drop_index("ix_linha_importacao_rejeitada_id_lote_importacao", table_name="linha_importacao_rejeitada")
    op.drop_table("linha_importacao_rejeitada")

    op.drop_index("ix_lote_importacao_iniciado_em", table_name="lote_importacao")
    op.drop_index("ix_lote_importacao_situacao", table_name="lote_importacao")
    op.drop_index("ix_lote_importacao_sistema_origem", table_name="lote_importacao")
    op.drop_index("ix_lote_importacao_perfil_origem", table_name="lote_importacao")
    op.drop_index("ix_lote_importacao_formato_arquivo", table_name="lote_importacao")
    op.drop_index("ix_lote_importacao_hash_arquivo", table_name="lote_importacao")
    op.drop_table("lote_importacao")
