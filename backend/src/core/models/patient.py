"""
core/models/patient.py
Model SQLAlchemy para a entidade Paciente.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    birth_date: Mapped[str] = mapped_column(String(10), nullable=False)   # YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relacionamento reverso — usado nas etapas de CRUD de consultas
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.name!r} cpf={self.cpf!r}>"
