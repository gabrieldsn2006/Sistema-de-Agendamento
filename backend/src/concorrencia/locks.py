"""
concorrencia/locks.py
Lock de agendamento — evita race condition quando duas requisições tentam
criar consultas para o mesmo médico simultaneamente.

Conceito de SO: Sincronização / Exclusão Mútua
  - asyncio.Lock é o equivalente ao mutex do kernel para código assíncrono:
    garante que apenas uma corrotina por vez execute a seção crítica
    (verificação de conflito + inserção), sem bloquear o event loop.
  - threading.Lock bloquearia a thread do event loop durante a espera,
    impedindo que outras requisições fossem processadas — por isso usamos
    asyncio.Lock, que cede o controle ao event loop enquanto aguarda.
  - Em produção com múltiplos workers (Gunicorn multiprocess), cada processo
    teria seu próprio lock; coordenação entre processos exigiria lock
    distribuído (ex: Redis SETNX / Redlock). Documentamos essa limitação.

Analogia com SO: semáforos binários do kernel, implementados aqui no
espaço do usuário usando primitivas do asyncio.
"""

import asyncio
import threading
from contextlib import asynccontextmanager

from config.logger import setup_logger

logger = setup_logger(__name__)

# Lock assíncrono — pertence ao event loop do processo.
# Instância criada no primeiro uso (dentro do loop ativo).
_appointment_lock: asyncio.Lock | None = None
_lock_init_mutex = threading.Lock()   # protege a inicialização do lock assíncrono


def _get_lock() -> asyncio.Lock:
    """Retorna (ou cria) o lock assíncrono de forma thread-safe."""
    global _appointment_lock
    if _appointment_lock is None:
        with _lock_init_mutex:
            if _appointment_lock is None:
                _appointment_lock = asyncio.Lock()
    return _appointment_lock


@asynccontextmanager
async def appointment_lock():
    """
    Context manager assíncrono que adquire o lock antes de verificar +
    criar uma consulta e o libera ao sair do bloco (mesmo em caso de exceção).

    Uso:
        async with appointment_lock():
            # seção crítica: check conflict → create appointment
    """
    lock = _get_lock()
    tid = threading.current_thread().name
    coro = asyncio.current_task().get_name() if asyncio.current_task() else "?"
    logger.debug(f"[LOCK] Task '{coro}' aguardando o lock de agendamento...")
    async with lock:
        logger.debug(f"[LOCK] Task '{coro}' adquiriu o lock.")
        try:
            yield
        finally:
            logger.debug(f"[LOCK] Task '{coro}' liberou o lock.")


def lock_status() -> dict:
    """Retorna o estado atual do lock (para debug e relatório técnico)."""
    lock = _get_lock()
    return {
        "lock_type":     "asyncio.Lock",
        "locked":        lock.locked(),
        "thread_count":  threading.active_count(),
        "current_thread": threading.current_thread().name,
        "nota": (
            "asyncio.Lock: exclusão mútua dentro do event loop (single-process). "
            "Multi-process requer lock distribuído (ex: Redis)."
        ),
    }
