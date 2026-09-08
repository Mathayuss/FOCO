"""estrutura inicial do FOCO

Revisão: 20260907_0001
Revisão anterior: None
Data: 2026-09-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260907_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "unidade_operacional",
        sa.Column("id_unidade_operacional", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=160), nullable=False),
        sa.Column("comando", sa.String(length=80), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id_unidade_operacional"),
    )
    op.create_index("ix_unidade_operacional_nome", "unidade_operacional", ["nome"], unique=True)
    op.create_index("ix_unidade_operacional_comando", "unidade_operacional", ["comando"], unique=False)

    op.create_table(
        "viatura",
        sa.Column("id_viatura", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=60), nullable=False),
        sa.Column("tipo_viatura", sa.String(length=60), nullable=False),
        sa.Column("id_unidade_operacional", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["id_unidade_operacional"], ["unidade_operacional.id_unidade_operacional"]),
        sa.PrimaryKeyConstraint("id_viatura"),
    )
    op.create_index("ix_viatura_codigo", "viatura", ["codigo"], unique=True)
    op.create_index("ix_viatura_tipo_viatura", "viatura", ["tipo_viatura"], unique=False)
    op.create_index("ix_viatura_id_unidade_operacional", "viatura", ["id_unidade_operacional"], unique=False)

    op.create_table(
        "ocorrencia",
        sa.Column("id_ocorrencia", sa.Integer(), nullable=False),
        sa.Column("sistema_origem", sa.String(length=80), nullable=False),
        sa.Column("id_origem", sa.String(length=120), nullable=False),
        sa.Column("numero_externo", sa.String(length=120), nullable=True),
        sa.Column("abertura_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("despacho_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("saida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chegada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("liberacao_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retorno_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disponibilidade_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grupo", sa.String(length=120), nullable=True),
        sa.Column("tipo", sa.String(length=500), nullable=False),
        sa.Column("subtipo", sa.String(length=500), nullable=True),
        sa.Column("prioridade", sa.String(length=40), nullable=True),
        sa.Column("municipio", sa.String(length=160), nullable=False),
        sa.Column("bairro", sa.String(length=160), nullable=True),
        sa.Column("endereco", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("id_unidade_operacional", sa.Integer(), nullable=True),
        sa.Column("situacao", sa.String(length=40), nullable=False),
        sa.Column("pontuacao_qualidade", sa.Float(), nullable=True),
        sa.Column("registro_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("codigo_ibge", sa.String(length=20), nullable=True),
        sa.Column("segredo_de_justica", sa.Boolean(), nullable=False),
        sa.Column("dados_origem", sa.Text(), nullable=True),
        sa.Column("importado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["id_unidade_operacional"], ["unidade_operacional.id_unidade_operacional"]),
        sa.PrimaryKeyConstraint("id_ocorrencia"),
        sa.UniqueConstraint("sistema_origem", "id_origem", name="uq_ocorrencia_origem"),
    )
    op.create_index("ix_ocorrencia_sistema_origem", "ocorrencia", ["sistema_origem"], unique=False)
    op.create_index("ix_ocorrencia_id_origem", "ocorrencia", ["id_origem"], unique=False)
    op.create_index("ix_ocorrencia_numero_externo", "ocorrencia", ["numero_externo"], unique=False)
    op.create_index("ix_ocorrencia_abertura_em", "ocorrencia", ["abertura_em"], unique=False)
    op.create_index("ix_ocorrencia_grupo", "ocorrencia", ["grupo"], unique=False)
    op.create_index("ix_ocorrencia_tipo", "ocorrencia", ["tipo"], unique=False)
    op.create_index("ix_ocorrencia_subtipo", "ocorrencia", ["subtipo"], unique=False)
    op.create_index("ix_ocorrencia_prioridade", "ocorrencia", ["prioridade"], unique=False)
    op.create_index("ix_ocorrencia_municipio", "ocorrencia", ["municipio"], unique=False)
    op.create_index("ix_ocorrencia_bairro", "ocorrencia", ["bairro"], unique=False)
    op.create_index("ix_ocorrencia_id_unidade_operacional", "ocorrencia", ["id_unidade_operacional"], unique=False)
    op.create_index("ix_ocorrencia_situacao", "ocorrencia", ["situacao"], unique=False)
    op.create_index("ix_ocorrencia_codigo_ibge", "ocorrencia", ["codigo_ibge"], unique=False)
    op.create_index("ix_ocorrencia_segredo_de_justica", "ocorrencia", ["segredo_de_justica"], unique=False)

    op.create_table(
        "ocorrencia_viatura",
        sa.Column("id_ocorrencia_viatura", sa.Integer(), nullable=False),
        sa.Column("id_ocorrencia", sa.Integer(), nullable=False),
        sa.Column("id_viatura", sa.Integer(), nullable=False),
        sa.Column("despacho_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("saida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chegada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("liberacao_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retorno_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disponibilidade_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["id_ocorrencia"], ["ocorrencia.id_ocorrencia"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_viatura"], ["viatura.id_viatura"]),
        sa.PrimaryKeyConstraint("id_ocorrencia_viatura"),
    )
    op.create_index("ix_ocorrencia_viatura_id_ocorrencia", "ocorrencia_viatura", ["id_ocorrencia"], unique=False)
    op.create_index("ix_ocorrencia_viatura_id_viatura", "ocorrencia_viatura", ["id_viatura"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ocorrencia_viatura_id_viatura", table_name="ocorrencia_viatura")
    op.drop_index("ix_ocorrencia_viatura_id_ocorrencia", table_name="ocorrencia_viatura")
    op.drop_table("ocorrencia_viatura")

    op.drop_index("ix_ocorrencia_segredo_de_justica", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_codigo_ibge", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_situacao", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_id_unidade_operacional", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_bairro", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_municipio", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_prioridade", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_subtipo", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_tipo", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_grupo", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_abertura_em", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_numero_externo", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_id_origem", table_name="ocorrencia")
    op.drop_index("ix_ocorrencia_sistema_origem", table_name="ocorrencia")
    op.drop_table("ocorrencia")

    op.drop_index("ix_viatura_id_unidade_operacional", table_name="viatura")
    op.drop_index("ix_viatura_tipo_viatura", table_name="viatura")
    op.drop_index("ix_viatura_codigo", table_name="viatura")
    op.drop_table("viatura")

    op.drop_index("ix_unidade_operacional_comando", table_name="unidade_operacional")
    op.drop_index("ix_unidade_operacional_nome", table_name="unidade_operacional")
    op.drop_table("unidade_operacional")
