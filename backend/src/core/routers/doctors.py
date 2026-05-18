"""
core/routers/doctors.py
Endpoints REST para Médico — CRUD completo.

POST   /doctors/                    → cria médico
GET    /doctors/                    → lista médicos (paginado)
GET    /doctors/{id}                → busca por ID
GET    /doctors/crm/{crm}           → busca por CRM
GET    /doctors/specialty/{name}    → filtra por especialidade
PUT    /doctors/{id}                → atualiza médico
DELETE /doctors/{id}                → remove médico
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_session
from config.logger import setup_logger
from core.repositories.doctor_repository import DoctorRepository
from core.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorOut

router = APIRouter(prefix="/doctors", tags=["Médicos"])
logger = setup_logger(__name__)


def _repo(session: AsyncSession = Depends(get_session)) -> DoctorRepository:
    return DoctorRepository(session)


# ── POST /doctors/ ───────────────────────────────────────────────────────────
@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
async def create_doctor(data: DoctorCreate, repo: DoctorRepository = Depends(_repo)):
    if await repo.get_by_crm(data.crm):
        raise HTTPException(status_code=409, detail="CRM já cadastrado.")
    doctor = await repo.create(data)
    logger.info(f"Médico criado: id={doctor.id} crm={doctor.crm}")
    return doctor


# ── GET /doctors/ ────────────────────────────────────────────────────────────
@router.get("/", response_model=list[DoctorOut])
async def list_doctors(
    skip:  int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    repo: DoctorRepository = Depends(_repo),
):
    return await repo.get_all(skip=skip, limit=limit)


# ── GET /doctors/{id} ────────────────────────────────────────────────────────
@router.get("/{doctor_id}", response_model=DoctorOut)
async def get_doctor(doctor_id: int, repo: DoctorRepository = Depends(_repo)):
    doctor = await repo.get_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    return doctor


# ── GET /doctors/crm/{crm} ───────────────────────────────────────────────────
@router.get("/crm/{crm}", response_model=DoctorOut)
async def get_doctor_by_crm(crm: str, repo: DoctorRepository = Depends(_repo)):
    doctor = await repo.get_by_crm(crm)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    return doctor


# ── GET /doctors/specialty/{name} ────────────────────────────────────────────
@router.get("/specialty/{specialty}", response_model=list[DoctorOut])
async def get_doctors_by_specialty(specialty: str, repo: DoctorRepository = Depends(_repo)):
    return await repo.get_by_specialty(specialty)


# ── PUT /doctors/{id} ────────────────────────────────────────────────────────
@router.put("/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    repo: DoctorRepository = Depends(_repo),
):
    doctor = await repo.get_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    doctor = await repo.update(doctor, data)
    logger.info(f"Médico atualizado: id={doctor_id}")
    return doctor


# ── DELETE /doctors/{id} ─────────────────────────────────────────────────────
@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(doctor_id: int, repo: DoctorRepository = Depends(_repo)):
    doctor = await repo.get_by_id(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado.")
    await repo.delete(doctor)
    logger.info(f"Médico removido: id={doctor_id}")
