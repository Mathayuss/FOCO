"""alinha indices relacionais e chave estrangeira do lote

Revisao: 20260914_0005
Revisao anterior: 20260914_0004
Data: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Index, MetaData, Table, inspect


revision: str = "20260914_0005"
down_revision: Union[str, Sequence[str], None] = "20260914_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    return index_name in {item["name"] for item in inspect(bind).get_indexes(table_name)}


def _ensure_index(bind, table_name: str, index_name: str, columns: list[str]) -> None:
    if _index_exists(bind, table_name, index_name):
        return
    table = Table(table_name, MetaData(), autoload_with=bind)
    Index(index_name, *(table.c[column] for column in columns)).create(bind)


def _foreign_key_exists(bind, table_name: str, constraint_name: str) -> bool:
    return any(
        fk.get("name") == constraint_name
        or (
            fk.get("constrained_columns") == ["id_lote_importacao"]
            and fk.get("referred_table") == "lote_importacao"
            and fk.get("referred_columns") == ["id_lote_importacao"]
        )
        for fk in inspect(bind).get_foreign_keys(table_name)
    )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_index(bind, "ocorrencia", "ix_ocorrencia_id_lote_importacao", ["id_lote_importacao"])
    _ensure_index(bind, "ocorrencia", "ix_ocorrencia_id_unidade_operacional", ["id_unidade_operacional"])
    _ensure_index(bind, "viatura", "ix_viatura_id_unidade_operacional", ["id_unidade_operacional"])

    if not _foreign_key_exists(bind, "ocorrencia", "fk_ocorrencia_lote_importacao"):
        # O batch do Alembic preserva colunas, registros e indices no SQLite.
        with op.batch_alter_table("ocorrencia") as batch_op:
            batch_op.create_foreign_key(
                "fk_ocorrencia_lote_importacao",
                "lote_importacao",
                ["id_lote_importacao"],
                ["id_lote_importacao"],
            )


def downgrade() -> None:
    # Estes indices e a chave ja pertencem as revisoes 0001 e 0002.
    # O downgrade da reparacao nao deve remover o schema dessas revisoes.
    pass
