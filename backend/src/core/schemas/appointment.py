"""
core/schemas/appointment.py
Schemas Pydantic para validação de entrada e serialização de saída — Consulta.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from core.models.appointment import AppointmentStatus
from core.schemas.patient import PatientOut
from core.schemas.doctor import DoctorOut


class AppointmentBase(BaseModel):
    patient_id:   int      = Field(..., examples=[1])
    doctor_id:    int      = Field(..., examples=[1])
    scheduled_at: datetime = Field(..., examples=["2025-07-10T14:30:00-03:00"])
    notes:        str | None = Field(None, max_length=500)


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    notes:        str | None      = Field(None, max_length=500)
    status:       AppointmentStatus | None = None


class AppointmentOut(AppointmentBase):
    id:         int
    status:     AppointmentStatus
    created_at: datetime
    patient:    PatientOut
    doctor:     DoctorOut

    model_config = {"from_attributes": True}
