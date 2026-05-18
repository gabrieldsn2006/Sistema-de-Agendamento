"""
core/repositories/patient_repository.py
Camada de acesso a dados — Paciente.
Toda query ao banco passa por aqui, mantendo os routers limpos.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.patient import Patient
from core.schemas.patient import PatientCreate, PatientUpdate


class PatientRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Patient]:
        result = await self.session.execute(
            select(Patient).order_by(Patient.name).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_id(self, patient_id: int) -> Patient | None:
        return await self.session.get(Patient, patient_id)

    async def get_by_cpf(self, cpf: str) -> Patient | None:
        result = await self.session.execute(
            select(Patient).where(Patient.cpf == cpf)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Patient))
        return result.scalar_one()

    async def create(self, data: PatientCreate) -> Patient:
        patient = Patient(**data.model_dump())
        self.session.add(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def update(self, patient: Patient, data: PatientUpdate) -> Patient:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def delete(self, patient: Patient) -> None:
        await self.session.delete(patient)
        await self.session.commit()
