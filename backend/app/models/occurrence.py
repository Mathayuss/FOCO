from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Occurrence(Base):
    __tablename__ = "occurrences"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_occurrence_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str] = mapped_column(String(120), index=True)
    external_number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    group_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    type_name: Mapped[str] = mapped_column(String(180), index=True)
    subtype_name: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    priority: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    municipality: Mapped[str] = mapped_column(String(160), index=True)
    neighborhood: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="closed", index=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    unit = relationship("Unit", back_populates="occurrences")
    vehicle_links = relationship("OccurrenceVehicle", back_populates="occurrence", cascade="all, delete-orphan")

class OccurrenceVehicle(Base):
    __tablename__ = "occurrence_vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    occurrence_id: Mapped[int] = mapped_column(ForeignKey("occurrences.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    occurrence = relationship("Occurrence", back_populates="vehicle_links")
    vehicle = relationship("Vehicle", back_populates="occurrence_links")
