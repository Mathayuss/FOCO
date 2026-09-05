from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Vehicle(Base):
    __tablename__ = "viatura"

    id: Mapped[int] = mapped_column("id_viatura", primary_key=True)
    code: Mapped[str] = mapped_column("codigo", String(60), unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column("tipo_viatura", String(60), index=True)
    unit_id: Mapped[int | None] = mapped_column("id_unidade_operacional", ForeignKey("unidade_operacional.id_unidade_operacional"), nullable=True)
    active: Mapped[bool] = mapped_column("ativo", default=True)

    unit = relationship("Unit", back_populates="vehicles")
    occurrence_links = relationship("OccurrenceVehicle", back_populates="vehicle")
