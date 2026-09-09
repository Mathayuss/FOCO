from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ImportBatch(Base):
    __tablename__ = "lote_importacao"

    id: Mapped[int] = mapped_column("id_lote_importacao", primary_key=True)
    filename: Mapped[str] = mapped_column("nome_arquivo", String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column("hash_arquivo", String(64), nullable=False, index=True)
    file_format: Mapped[str] = mapped_column("formato_arquivo", String(20), nullable=False, index=True)
    source_profile: Mapped[str] = mapped_column("perfil_origem", String(80), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column("sistema_origem", String(80), nullable=False, index=True)
    total_rows: Mapped[int] = mapped_column("total_linhas", Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column("linhas_validas", Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column("linhas_invalidas", Integer, nullable=False, default=0)
    inserted_rows: Mapped[int] = mapped_column("linhas_inseridas", Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column("linhas_duplicadas", Integer, nullable=False, default=0)
    sensitive_rows: Mapped[int] = mapped_column("linhas_sensiveis", Integer, nullable=False, default=0)
    invalid_coordinate_rows: Mapped[int] = mapped_column("linhas_coordenada_invalida", Integer, nullable=False, default=0)
    missing_coordinate_rows: Mapped[int] = mapped_column("linhas_sem_coordenada", Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column("situacao", String(40), nullable=False, default="processando", index=True)
    warnings: Mapped[str | None] = mapped_column("avisos", Text, nullable=True)
    error: Mapped[str | None] = mapped_column("erro", Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column("iniciado_em", DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    finished_at: Mapped[datetime | None] = mapped_column("concluido_em", DateTime(timezone=True), nullable=True)

    occurrences = relationship("Occurrence", back_populates="import_batch")
    rejected_rows = relationship("RejectedImportLine", back_populates="import_batch", cascade="all, delete-orphan")


class RejectedImportLine(Base):
    __tablename__ = "linha_importacao_rejeitada"

    id: Mapped[int] = mapped_column("id_linha_importacao_rejeitada", primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(
        "id_lote_importacao",
        ForeignKey("lote_importacao.id_lote_importacao", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column("numero_linha", Integer, nullable=False, index=True)
    reasons: Mapped[str] = mapped_column("motivos", Text, nullable=False)
    source_payload: Mapped[str | None] = mapped_column("dados_origem", Text, nullable=True)

    import_batch = relationship("ImportBatch", back_populates="rejected_rows")
