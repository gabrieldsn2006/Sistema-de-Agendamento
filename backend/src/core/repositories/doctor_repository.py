"""
core/repositories/doctor_repository.py
Camada de acesso a dados — Médico.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.doctor import Doctor
from core.schemas.doctor import DoctorCreate, DoctorUpdate


class DoctorRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Doctor]:
        result = await self.session.execute(
            select(Doctor).order_by(Doctor.name).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_id(self, doctor_id: int) -> Doctor | None:
        return await self.session.get(Doctor, doctor_id)

    async def get_by_crm(self, crm: str) -> Doctor | None:
        result = await self.session.execute(
            select(Doctor).where(Doctor.crm == crm)
        )
        return result.scalar_one_or_none()

    async def get_by_specialty(self, specialty: str) -> list[Doctor]:
        result = await self.session.execute(
            select(Doctor)
            .where(Doctor.specialty.ilike(f"%{specialty}%"))
            .order_by(Doctor.name)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(Doctor))
        return result.scalar_one()

    async def create(self, data: DoctorCreate) -> Doctor:
        doctor = Doctor(**data.model_dump())
        self.session.add(doctor)
        await self.session.commit()
        await self.session.refresh(doctor)
        return doctor

    async def update(self, doctor: Doctor, data: DoctorUpdate) -> Doctor:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(doctor, field, value)
        await self.session.commit()
        await self.session.refresh(doctor)
        return doctor

    async def delete(self, doctor: Doctor) -> None:
        await self.session.delete(doctor)
        await self.session.commit()
