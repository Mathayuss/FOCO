from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(60), index=True)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    active: Mapped[bool] = mapped_column(default=True)

    unit = relationship("Unit", back_populates="vehicles")
    occurrence_links = relationship("OccurrenceVehicle", back_populates="vehicle")
