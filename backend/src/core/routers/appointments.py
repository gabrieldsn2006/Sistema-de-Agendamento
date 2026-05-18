"""
core/routers/appointments.py
Endpoints REST para Consulta — CRUD completo.

POST   /appointments/               → cria consulta
GET    /appointments/               → lista consultas (paginado)
GET    /appointments/{id}           → busca por ID
GET    /appointments/doctor/{id}    → consultas de um médico
GET    /appointments/patient/{id}   → consultas de um paciente
PUT    /appointments/{id}           → atualiza consulta
DELETE /appointments/{id}           → remove consulta
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from config.logger import setup_logger
from core.repositories.appointment_repository import AppointmentRepository
from core.repositories.patient_repository import PatientRepository
from core.repositories.doctor_repository import DoctorRepository
from core.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentOut

router = APIRouter(prefix="/appointments", tags=["Consultas"])
logger = setup_logger(__name__)


def _repo(session: AsyncSession = Depends(get_session)) -> AppointmentRepository:
    return AppointmentRepository(session)


async def _validate_references(data: AppointmentCreate | AppointmentUpdate, session: AsyncSession):
    """Verifica se patient_id e doctor_id existem no banco."""
    if hasattr(data, "patient_id") and data.patient_id:
        if not await PatientRepository(session).get_by_id(data.patient_id):
            raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    if hasattr(data, "doctor_id") and data.doctor_id:
        if not await DoctorRepository(session).get_by_id(data.doctor_id):
            raise HTTPException(status_code=404, detail="Médico não encontrado.")


# ── POST /appointments/ ──────────────────────────────────────────────────────
@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    data: AppointmentCreate,
    session: AsyncSession = Depends(get_session),
):
    await _validate_references(data, session)
    repo = AppointmentRepository(session)

    if await repo.doctor_has_conflict(data.doctor_id, data.scheduled_at):
        raise HTTPException(status_code=409, detail="Médico já possui consulta neste horário.")
    if await repo.patient_has_conflict(data.patient_id, data.scheduled_at):
        raise HTTPException(status_code=409, detail="Paciente já possui consulta neste horário.")

    appointment = await repo.create(data)
    logger.info(
        f"Consulta criada: id={appointment.id} "
        f"doctor={data.doctor_id} patient={data.patient_id} "
        f"at={data.scheduled_at}"
    )
    return appointment


# ── GET /appointments/ ───────────────────────────────────────────────────────
@router.get("/", response_model=list[AppointmentOut])
async def list_appointments(
    skip:  int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    repo: AppointmentRepository = Depends(_repo),
):
    return await repo.get_all(skip=skip, limit=limit)


# ── GET /appointments/doctor/{id} ────────────────────────────────────────────
@router.get("/doctor/{doctor_id}", response_model=list[AppointmentOut])
async def list_by_doctor(doctor_id: int, repo: AppointmentRepository = Depends(_repo)):
    return await repo.get_by_doctor(doctor_id)


# ── GET /appointments/patient/{id} ───────────────────────────────────────────
@router.get("/patient/{patient_id}", response_model=list[AppointmentOut])
async def list_by_patient(patient_id: int, repo: AppointmentRepository = Depends(_repo)):
    return await repo.get_by_patient(patient_id)


# ── GET /appointments/{id} ───────────────────────────────────────────────────
@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(appointment_id: int, repo: AppointmentRepository = Depends(_repo)):
    appointment = await repo.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    return appointment


# ── PUT /appointments/{id} ───────────────────────────────────────────────────
@router.put("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    session: AsyncSession = Depends(get_session),
):
    repo = AppointmentRepository(session)
    appointment = await repo.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")

    # Re-verifica conflitos se o horário está sendo alterado
    if data.scheduled_at:
        if await repo.doctor_has_conflict(
            appointment.doctor_id, data.scheduled_at, exclude_id=appointment_id
        ):
            raise HTTPException(status_code=409, detail="Médico já possui consulta neste horário.")
        if await repo.patient_has_conflict(
            appointment.patient_id, data.scheduled_at, exclude_id=appointment_id
        ):
            raise HTTPException(status_code=409, detail="Paciente já possui consulta neste horário.")

    appointment = await repo.update(appointment, data)
    logger.info(f"Consulta atualizada: id={appointment_id}")
    return appointment


# ── DELETE /appointments/{id} ────────────────────────────────────────────────
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(appointment_id: int, repo: AppointmentRepository = Depends(_repo)):
    appointment = await repo.get_by_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada.")
    await repo.delete(appointment)
    logger.info(f"Consulta removida: id={appointment_id}")
