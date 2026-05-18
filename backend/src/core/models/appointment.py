"""
core/models/appointment.py
Model SQLAlchemy para a entidade Consulta.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from config.database import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED  = "scheduled"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Chaves estrangeiras
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id:  Mapped[int] = mapped_column(ForeignKey("doctors.id"),  nullable=False, index=True)

    # Data/hora da consulta — armazenada com timezone (chamada de sistema: hora do SO)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relacionamentos
    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    doctor:  Mapped["Doctor"]  = relationship(back_populates="appointments")

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.id} "
            f"patient_id={self.patient_id} "
            f"doctor_id={self.doctor_id} "
            f"at={self.scheduled_at}>"
        )
