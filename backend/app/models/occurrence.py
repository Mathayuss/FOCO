from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Occurrence(Base):
    __tablename__ = "ocorrencia"
    __table_args__ = (UniqueConstraint("sistema_origem", "id_origem", name="uq_ocorrencia_origem"),)

    id: Mapped[int] = mapped_column("id_ocorrencia", primary_key=True)
    source: Mapped[str] = mapped_column("sistema_origem", String(80), index=True)
    source_id: Mapped[str] = mapped_column("id_origem", String(120), index=True)
    external_number: Mapped[str | None] = mapped_column("numero_externo", String(120), nullable=True, index=True)

    opened_at: Mapped[datetime] = mapped_column("abertura_em", DateTime(timezone=True), index=True)
    dispatched_at: Mapped[datetime | None] = mapped_column("despacho_em", DateTime(timezone=True), nullable=True)
    departure_at: Mapped[datetime | None] = mapped_column("saida_em", DateTime(timezone=True), nullable=True)
    arrival_at: Mapped[datetime | None] = mapped_column("chegada_em", DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column("liberacao_em", DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column("retorno_em", DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime | None] = mapped_column("disponibilidade_em", DateTime(timezone=True), nullable=True)

    group_name: Mapped[str | None] = mapped_column("grupo", String(120), nullable=True, index=True)
    type_name: Mapped[str] = mapped_column("tipo", String(180), index=True)
    subtype_name: Mapped[str | None] = mapped_column("subtipo", String(180), nullable=True, index=True)
    priority: Mapped[str | None] = mapped_column("prioridade", String(40), nullable=True, index=True)

    municipality: Mapped[str] = mapped_column("municipio", String(160), index=True)
    neighborhood: Mapped[str | None] = mapped_column("bairro", String(160), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column("endereco", Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    unit_id: Mapped[int | None] = mapped_column("id_unidade_operacional", ForeignKey("unidade_operacional.id_unidade_operacional"), nullable=True)
    status: Mapped[str] = mapped_column("situacao", String(40), default="fechada", index=True)
    quality_score: Mapped[float | None] = mapped_column("pontuacao_qualidade", Float, nullable=True)
    imported_at: Mapped[datetime] = mapped_column("importado_em", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    unit = relationship("Unit", back_populates="occurrences")
    vehicle_links = relationship("OccurrenceVehicle", back_populates="occurrence", cascade="all, delete-orphan")

class OccurrenceVehicle(Base):
    __tablename__ = "ocorrencia_viatura"

    id: Mapped[int] = mapped_column("id_ocorrencia_viatura", primary_key=True)
    occurrence_id: Mapped[int] = mapped_column("id_ocorrencia", ForeignKey("ocorrencia.id_ocorrencia", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int] = mapped_column("id_viatura", ForeignKey("viatura.id_viatura"), index=True)

    dispatched_at: Mapped[datetime | None] = mapped_column("despacho_em", DateTime(timezone=True), nullable=True)
    departure_at: Mapped[datetime | None] = mapped_column("saida_em", DateTime(timezone=True), nullable=True)
    arrival_at: Mapped[datetime | None] = mapped_column("chegada_em", DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column("liberacao_em", DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column("retorno_em", DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime | None] = mapped_column("disponibilidade_em", DateTime(timezone=True), nullable=True)

    occurrence = relationship("Occurrence", back_populates="vehicle_links")
    vehicle = relationship("Vehicle", back_populates="occurrence_links")
