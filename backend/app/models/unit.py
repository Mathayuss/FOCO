from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    command: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    active: Mapped[bool] = mapped_column(default=True)

    vehicles = relationship("Vehicle", back_populates="unit")
    occurrences = relationship("Occurrence", back_populates="unit")
