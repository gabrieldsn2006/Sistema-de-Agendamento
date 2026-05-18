"""
core/models/doctor.py
Model SQLAlchemy para a entidade Médico.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    crm: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(80), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} name={self.name!r} crm={self.crm!r}>"
