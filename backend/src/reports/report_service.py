"""
reports/report_service.py
Serviço de relatórios — busca dados do banco e enfileira a geração
de arquivos na thread de background.

Conceito de SO: Threads para operações de I/O
  - A geração de PDF/CSV é CPU + I/O intensiva; delegá-la ao worker thread
    libera o event loop para continuar atendendo outras requisições.
  - O endpoint retorna 202 Accepted + task_id imediatamente;
    o cliente consulta /system/task/{id} para verificar o resultado.
  - Dados são serializados em dicts simples antes de cruzar a fronteira
    entre o event loop (async) e a thread de background (sync).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import timezone

from core.models.appointment import Appointment, AppointmentStatus
from core.models.doctor import Doctor
from config.logger import setup_logger

logger = setup_logger(__name__)


async def _fetch_doctor_appointments(session: AsyncSession, doctor_id: int) -> tuple[dict, list[dict]]:
    """Busca médico e suas consultas (não canceladas) do banco."""
    doctor = await session.get(Doctor, doctor_id)
    if not doctor:
        return None, []

    result = await session.execute(
        select(Appointment)
        .options(selectinload(Appointment.patient))
        .where(Appointment.doctor_id == doctor_id)
        .order_by(Appointment.scheduled_at)
    )
    appointments = result.scalars().all()

    doctor_data = {
        "name":      doctor.name,
        "crm":       doctor.crm,
        "specialty": doctor.specialty,
    }
    apts_data = [
        {
            "id":           apt.id,
            "scheduled_at": apt.scheduled_at.replace(tzinfo=timezone.utc).isoformat(),
            "status":       apt.status.value,
            "patient_name": apt.patient.name,
            "notes":        apt.notes,
        }
        for apt in appointments
    ]
    return doctor_data, apts_data


async def _fetch_all_appointments(session: AsyncSession) -> list[dict]:
    """Busca todas as consultas do sistema com dados relacionados."""
    result = await session.execute(
        select(Appointment)
        .options(
            selectinload(Appointment.patient),
            selectinload(Appointment.doctor),
        )
        .order_by(Appointment.scheduled_at)
    )
    appointments = result.scalars().all()

    return [
        {
            "id":              apt.id,
            "scheduled_at":   apt.scheduled_at.replace(tzinfo=timezone.utc).isoformat(),
            "status":         apt.status.value,
            "patient_name":   apt.patient.name,
            "patient_cpf":    apt.patient.cpf,
            "doctor_name":    apt.doctor.name,
            "doctor_crm":     apt.doctor.crm,
            "doctor_specialty": apt.doctor.specialty,
            "notes":          apt.notes,
        }
        for apt in appointments
    ]


async def enqueue_doctor_pdf(session: AsyncSession, doctor_id: int) -> tuple[str | None, str]:
    """
    Busca os dados do médico e enfileira a geração do PDF.
    Retorna (task_id, erro). Se erro != None, task_id é None.
    """
    from concorrencia.workers import enqueue as worker_enqueue, _task_queue
    import queue as q_module

    doctor_data, apts_data = await _fetch_doctor_appointments(session, doctor_id)
    if doctor_data is None:
        return None, "Médico não encontrado."

    # Enfileira tarefa com payload embutido no nome (via closure na workers)
    # Usamos a fila diretamente com um payload rico
    import uuid, threading
    from concorrencia.workers import _task_queue, _results, _results_lock

    task_id = str(uuid.uuid4())[:8]

    def _run():
        from reports.pdf_report import generate_doctor_pdf
        try:
            path = generate_doctor_pdf(doctor_data, apts_data)
            with _results_lock:
                _results[task_id] = {
                    "status": "ok",
                    "task": "pdf_medico",
                    "arquivo": str(path),
                    "medico": doctor_data["name"],
                    "consultas": len(apts_data),
                }
        except Exception as e:
            logger.error(f"[PDF] Erro ao gerar: {e}", exc_info=True)
            with _results_lock:
                _results[task_id] = {"status": "error", "task": "pdf_medico", "erro": str(e)}

    t = threading.Thread(target=_run, name=f"PDFWorker-{task_id}", daemon=True)
    t.start()
    logger.info(f"[RELATÓRIO] PDF enfileirado: task_id={task_id} médico='{doctor_data['name']}'")
    return task_id, None


async def enqueue_full_csv(session: AsyncSession) -> str:
    """
    Busca todos os dados e enfileira a geração do CSV.
    Retorna task_id.
    """
    import uuid, threading
    from concorrencia.workers import _results, _results_lock

    apts_data = await _fetch_all_appointments(session)
    task_id = str(uuid.uuid4())[:8]

    def _run():
        from reports.csv_report import generate_full_csv
        try:
            path = generate_full_csv(apts_data)
            with _results_lock:
                _results[task_id] = {
                    "status": "ok",
                    "task": "csv_geral",
                    "arquivo": str(path),
                    "registros": len(apts_data),
                }
        except Exception as e:
            logger.error(f"[CSV] Erro ao gerar: {e}", exc_info=True)
            with _results_lock:
                _results[task_id] = {"status": "error", "task": "csv_geral", "erro": str(e)}

    t = threading.Thread(target=_run, name=f"CSVWorker-{task_id}", daemon=True)
    t.start()
    logger.info(f"[RELATÓRIO] CSV enfileirado: task_id={task_id}, {len(apts_data)} registros")
    return task_id
