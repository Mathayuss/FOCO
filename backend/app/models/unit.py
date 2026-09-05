from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Unit(Base):
    __tablename__ = "unidade_operacional"

    id: Mapped[int] = mapped_column("id_unidade_operacional", primary_key=True)
    name: Mapped[str] = mapped_column("nome", String(160), unique=True, index=True)
    command: Mapped[str | None] = mapped_column("comando", String(80), nullable=True, index=True)
    active: Mapped[bool] = mapped_column("ativo", default=True)

    vehicles = relationship("Vehicle", back_populates="unit")
    occurrences = relationship("Occurrence", back_populates="unit")
