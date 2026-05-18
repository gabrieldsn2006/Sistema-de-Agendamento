"""
core/services/appointment_service.py
Camada de serviço — encapsula todas as regras de negócio de agendamento.

Regras implementadas:
  1. Horário dentro do expediente (08:00–18:00, seg–sab)
  2. Agendamento mínimo com 1h de antecedência
  3. Médico sem conflito de slot (±30 min)
  4. Paciente sem conflito de slot (±30 min)
  5. Consulta não pode ser reagendada se já concluída/cancelada
"""

from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from config.logger import setup_logger
from core.repositories.appointment_repository import AppointmentRepository
from core.repositories.patient_repository import PatientRepository
from core.repositories.doctor_repository import DoctorRepository
from core.schemas.appointment import AppointmentCreate, AppointmentUpdate
from core.models.appointment import Appointment, AppointmentStatus

logger = setup_logger(__name__)

# ── Constantes de regras de negócio ─────────────────────────────────────────
BUSINESS_START = time(8, 0)    # 08:00
BUSINESS_END   = time(18, 0)   # 18:00
VALID_WEEKDAYS = range(0, 6)   # segunda (0) a sábado (5); domingo (6) bloqueado
MIN_ADVANCE_HOURS = 1          # agendamento com pelo menos 1h de antecedência
SYSTEM_TZ = ZoneInfo("America/Fortaleza")  # fuso do SO — detectado via config


def _to_local(dt: datetime) -> datetime:
    """Converte datetime (possivelmente UTC) para o fuso local do sistema."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SYSTEM_TZ)


def _validate_schedule_time(scheduled_at: datetime) -> None:
    """
    Valida as regras de horário:
      - Dia da semana válido
      - Dentro do expediente
      - Antecedência mínima de 1h
    Lança HTTPException 422 com mensagem descritiva em caso de violação.
    """
    local_dt = _to_local(scheduled_at)
    now_local = datetime.now(SYSTEM_TZ)

    weekday = local_dt.weekday()
    if weekday not in VALID_WEEKDAYS:
        day_name = local_dt.strftime("%A")
        raise HTTPException(
            status_code=422,
            detail=f"Agendamentos não são permitidos aos domingos. "
                   f"Data informada: {local_dt.strftime('%d/%m/%Y')} ({day_name}).",
        )

    slot_time = local_dt.time()
    if slot_time < BUSINESS_START or slot_time >= BUSINESS_END:
        raise HTTPException(
            status_code=422,
            detail=f"Horário fora do expediente. "
                   f"Atendimento das {BUSINESS_START.strftime('%H:%M')} "
                   f"às {BUSINESS_END.strftime('%H:%M')}. "
                   f"Horário solicitado: {slot_time.strftime('%H:%M')}.",
        )

    diff_hours = (local_dt - now_local).total_seconds() / 3600
    if diff_hours < MIN_ADVANCE_HOURS:
        raise HTTPException(
            status_code=422,
            detail=f"Agendamento requer pelo menos {MIN_ADVANCE_HOURS}h de antecedência. "
                   f"Horário solicitado: {local_dt.strftime('%d/%m/%Y %H:%M')}.",
        )


class AppointmentService:
    """Orquestra validações e delega persistência ao repository."""

    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        patient_repo: PatientRepository,
        doctor_repo: DoctorRepository,
    ):
        self.appointments = appointment_repo
        self.patients = patient_repo
        self.doctors = doctor_repo

    # ── Criação ──────────────────────────────────────────────────────────────

    async def create(self, data: AppointmentCreate) -> Appointment:
        # 1. Referências existem
        patient = await self.patients.get_by_id(data.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente não encontrado.")

        doctor = await self.doctors.get_by_id(data.doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Médico não encontrado.")

        # 2. Regras de horário
        _validate_schedule_time(data.scheduled_at)

        # 3. Conflito de agenda do médico
        if await self.appointments.doctor_has_conflict(data.doctor_id, data.scheduled_at):
            raise HTTPException(
                status_code=409,
                detail=f"Dr(a). {doctor.name} já possui consulta próxima a este horário. "
                       f"Escolha um horário com intervalo mínimo de 30 minutos.",
            )

        # 4. Conflito de agenda do paciente
        if await self.appointments.patient_has_conflict(data.patient_id, data.scheduled_at):
            raise HTTPException(
                status_code=409,
                detail=f"{patient.name} já possui uma consulta próxima a este horário. "
                       f"Verifique a agenda do paciente.",
            )

        appointment = await self.appointments.create(data)
        logger.info(
            f"[NEGÓCIO] Consulta agendada: id={appointment.id} "
            f"médico='{doctor.name}' paciente='{patient.name}' "
            f"horário={_to_local(data.scheduled_at).strftime('%d/%m/%Y %H:%M')}"
        )
        return appointment

    # ── Atualização ──────────────────────────────────────────────────────────

    async def update(self, appointment_id: int, data: AppointmentUpdate) -> Appointment:
        appointment = await self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Consulta não encontrada.")

        # 5. Não permite reagendar consulta finalizada
        if appointment.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
            raise HTTPException(
                status_code=409,
                detail=f"Não é possível alterar uma consulta com status '{appointment.status.value}'. "
                       f"Cancele e crie uma nova consulta.",
            )

        if data.scheduled_at:
            _validate_schedule_time(data.scheduled_at)

            if await self.appointments.doctor_has_conflict(
                appointment.doctor_id, data.scheduled_at, exclude_id=appointment_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail=f"Dr(a). {appointment.doctor.name} já possui consulta próxima ao novo horário.",
                )

            if await self.appointments.patient_has_conflict(
                appointment.patient_id, data.scheduled_at, exclude_id=appointment_id
            ):
                raise HTTPException(
                    status_code=409,
                    detail=f"{appointment.patient.name} já possui consulta próxima ao novo horário.",
                )

        return await self.appointments.update(appointment, data)

    # ── Remoção ──────────────────────────────────────────────────────────────

    async def delete(self, appointment_id: int) -> None:
        appointment = await self.appointments.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Consulta não encontrada.")

        if appointment.status == AppointmentStatus.COMPLETED:
            raise HTTPException(
                status_code=409,
                detail="Consultas concluídas não podem ser removidas. Use o status 'cancelled'.",
            )

        await self.appointments.delete(appointment)
        logger.info(f"[NEGÓCIO] Consulta removida: id={appointment_id}")
