"""
core/schemas/doctor.py
Schemas Pydantic para validação de entrada e serialização de saída — Médico.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class DoctorBase(BaseModel):
    name:      str = Field(..., min_length=3, max_length=120, examples=["Dr. João Costa"])
    crm:       str = Field(..., min_length=4, max_length=20,  examples=["CRM/CE 12345"])
    specialty: str = Field(..., min_length=3, max_length=80,  examples=["Cardiologia"])
    phone:     str = Field(..., min_length=8, max_length=20,  examples=["(85) 3200-0000"])
    email:     str | None = Field(None, examples=["joao@clinica.com"])


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    name:      str | None = Field(None, min_length=3, max_length=120)
    specialty: str | None = Field(None, min_length=3, max_length=80)
    phone:     str | None = Field(None, min_length=8, max_length=20)
    email:     str | None = None


class DoctorOut(DoctorBase):
    id:         int
    created_at: datetime

    model_config = {"from_attributes": True}
