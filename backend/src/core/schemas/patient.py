"""
core/schemas/patient.py
Schemas Pydantic para validação de entrada e serialização de saída — Paciente.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class PatientBase(BaseModel):
    name:       str = Field(..., min_length=3, max_length=120, examples=["Maria Silva"])
    cpf:        str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", examples=["123.456.789-00"])
    phone:      str = Field(..., min_length=8, max_length=20, examples=["(85) 91234-5678"])
    email:      str | None = Field(None, examples=["maria@email.com"])
    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["1990-05-20"])


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name:       str | None = Field(None, min_length=3, max_length=120)
    phone:      str | None = Field(None, min_length=8, max_length=20)
    email:      str | None = None
    birth_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class PatientOut(PatientBase):
    id:         int
    created_at: datetime

    model_config = {"from_attributes": True}
