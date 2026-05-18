"""
core/routers/patients.py
Endpoints REST para Paciente — CRUD completo.

POST   /patients/         → cria paciente
GET    /patients/         → lista pacientes (paginado)
GET    /patients/{id}     → busca por ID
GET    /patients/cpf/{cpf}→ busca por CPF
PUT    /patients/{id}     → atualiza paciente
DELETE /patients/{id}     → remove paciente
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from config.logger import setup_logger
from core.repositories.patient_repository import PatientRepository
from core.schemas.patient import PatientCreate, PatientUpdate, PatientOut

router = APIRouter(prefix="/patients", tags=["Pacientes"])
logger = setup_logger(__name__)


def _repo(session: AsyncSession = Depends(get_session)) -> PatientRepository:
    return PatientRepository(session)


# ── POST /patients/ ──────────────────────────────────────────────────────────
@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, repo: PatientRepository = Depends(_repo)):
    if await repo.get_by_cpf(data.cpf):
        raise HTTPException(status_code=409, detail="CPF já cadastrado.")
    patient = await repo.create(data)
    logger.info(f"Paciente criado: id={patient.id} cpf={patient.cpf}")
    return patient


# ── GET /patients/ ───────────────────────────────────────────────────────────
@router.get("/", response_model=list[PatientOut])
async def list_patients(
    skip:  int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    repo: PatientRepository = Depends(_repo),
):
    return await repo.get_all(skip=skip, limit=limit)


# ── GET /patients/{id} ───────────────────────────────────────────────────────
@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: int, repo: PatientRepository = Depends(_repo)):
    patient = await repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return patient


# ── GET /patients/cpf/{cpf} ──────────────────────────────────────────────────
@router.get("/cpf/{cpf}", response_model=PatientOut)
async def get_patient_by_cpf(cpf: str, repo: PatientRepository = Depends(_repo)):
    patient = await repo.get_by_cpf(cpf)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return patient


# ── PUT /patients/{id} ───────────────────────────────────────────────────────
@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    repo: PatientRepository = Depends(_repo),
):
    patient = await repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    patient = await repo.update(patient, data)
    logger.info(f"Paciente atualizado: id={patient_id}")
    return patient


# ── DELETE /patients/{id} ────────────────────────────────────────────────────
@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: int, repo: PatientRepository = Depends(_repo)):
    patient = await repo.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    await repo.delete(patient)
    logger.info(f"Paciente removido: id={patient_id}")
