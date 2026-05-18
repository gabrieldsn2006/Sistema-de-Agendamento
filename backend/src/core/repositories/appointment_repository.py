"""
core/repositories/appointment_repository.py
Camada de acesso a dados — Consulta.
Inclui queries de verificação de conflito de horário (usadas na etapa 4).
"""

from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.appointment import Appointment, AppointmentStatus
from core.schemas.appointment import AppointmentCreate, AppointmentUpdate

# Janela de conflito: consultas com menos de 30 min de diferença são conflitantes
SLOT_MINUTES = 30


class AppointmentRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Helpers internos ─────────────────────────────────────────────────────

    def _with_relations(self):
        """Carrega patient e doctor junto para evitar N+1 queries."""
        return select(Appointment).options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor),
        )

    def _slot_window(self, dt: datetime):
        """Retorna o intervalo [dt - 30min, dt + 30min] para checagem de conflito."""
        delta = timedelta(minutes=SLOT_MINUTES)
        return dt - delta, dt + delta

    # ── Queries públicas ─────────────────────────────────────────────────────

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Appointment]:
        result = await self.session.execute(
            self._with_relations()
            .order_by(Appointment.scheduled_at.desc())
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_id(self, appointment_id: int) -> Appointment | None:
        result = await self.session.execute(
            self._with_relations().where(Appointment.id == appointment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_doctor(self, doctor_id: int) -> list[Appointment]:
        result = await self.session.execute(
            self._with_relations()
            .where(Appointment.doctor_id == doctor_id)
            .order_by(Appointment.scheduled_at)
        )
        return result.scalars().all()

    async def get_by_patient(self, patient_id: int) -> list[Appointment]:
        result = await self.session.execute(
            self._with_relations()
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.scheduled_at)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Appointment)
        )
        return result.scalar_one()

    # ── Verificações de conflito (pré-condições das regras de negócio) ───────

    async def doctor_has_conflict(
        self,
        doctor_id: int,
        scheduled_at: datetime,
        exclude_id: int | None = None,
    ) -> bool:
        """
        Verifica se o médico já tem consulta no mesmo slot de 30 min.
        Conceito de SO: controle de concorrência — esta query é a base
        do lock de agendamento que será implementado na etapa 5.
        """
        low, high = self._slot_window(scheduled_at)
        stmt = select(func.count()).select_from(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_at >= low,
                Appointment.scheduled_at <= high,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        )
        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def patient_has_conflict(
        self,
        patient_id: int,
        scheduled_at: datetime,
        exclude_id: int | None = None,
    ) -> bool:
        """Verifica se o paciente já tem consulta no mesmo slot."""
        low, high = self._slot_window(scheduled_at)
        stmt = select(func.count()).select_from(Appointment).where(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.scheduled_at >= low,
                Appointment.scheduled_at <= high,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        )
        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    # ── Escrita ──────────────────────────────────────────────────────────────

    async def create(self, data: AppointmentCreate) -> Appointment:
        appointment = Appointment(**data.model_dump())
        self.session.add(appointment)
        await self.session.commit()
        # Recarrega com relações para a resposta
        return await self.get_by_id(appointment.id)

    async def update(self, appointment: Appointment, data: AppointmentUpdate) -> Appointment:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(appointment, field, value)
        await self.session.commit()
        return await self.get_by_id(appointment.id)

    async def delete(self, appointment: Appointment) -> None:
        await self.session.delete(appointment)
        await self.session.commit()
