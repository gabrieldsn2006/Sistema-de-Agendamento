"""
concorrencia/workers.py
Threads de background para operações de I/O pesadas:
  - Backup automático do banco de dados
  - Geração de relatórios (será expandido na etapa 6)

Conceito de SO: Threads e Escalonamento
  - Cada operação roda em uma thread separada (daemon=True), permitindo
    que o servidor continue respondendo requisições durante o I/O.
  - O escalonador do SO alterna entre as threads conforme disponibilidade
    de CPU e I/O (preemptivo no Linux, cooperativo no Windows com asyncio).
  - queue.Queue é usada para comunicação thread-safe entre o worker e o
    chamador (produtor/consumidor — padrão clássico de SO).

Conceito de SO: Sistema de Arquivos
  - Backup usa shutil.copy2 (preserva metadados do inode: timestamps).
  - Estrutura de diretórios criada via pathlib (agnóstico de plataforma).
"""

import threading
import queue
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from config.logger import setup_logger
from config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

# Fila de tarefas thread-safe — o servidor envia tarefas, o worker consome
_task_queue: queue.Queue = queue.Queue(maxsize=50)

# Resultados das tarefas — mapeados por task_id
_results: dict[str, dict] = {}
_results_lock = threading.Lock()


# ── Tipos de tarefa ───────────────────────────────────────────────────────────

def _task_backup() -> dict:
    """
    Copia o arquivo .db para data/backups/ com timestamp no nome.
    Conceito de SO: shutil.copy2 usa syscalls de leitura/escrita em bloco;
    preserva atime e mtime do inode original.
    """
    db_path = settings.BASE_DIR / "data" / "agendamento.db"
    if not db_path.exists():
        return {"status": "skipped", "motivo": "Banco ainda não criado."}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = settings.BACKUPS_DIR / f"agendamento_{ts}.db"

    shutil.copy2(db_path, dest)   # cópia com metadados preservados

    # Mantém apenas os 5 backups mais recentes (libera espaço em disco)
    backups = sorted(settings.BACKUPS_DIR.glob("agendamento_*.db"))
    for old in backups[:-5]:
        old.unlink()
        logger.debug(f"[BACKUP] Backup antigo removido: {old.name}")

    size_kb = dest.stat().st_size // 1024
    logger.info(f"[BACKUP] Backup criado: {dest.name} ({size_kb} KB)")
    return {"status": "ok", "arquivo": str(dest), "tamanho_kb": size_kb}


def _task_cleanup_cache() -> dict:
    """
    Remove arquivos de cache expirados (mais de 1h).
    Conceito de SO: acesso a metadados do inode via os.stat() (st_mtime).
    """
    now = time.time()
    removed = 0
    for f in settings.CACHE_DIR.iterdir():
        if f.is_file() and (now - f.stat().st_mtime) > 3600:
            f.unlink()
            removed += 1
    logger.info(f"[CACHE] Limpeza: {removed} arquivo(s) expirado(s) removidos.")
    return {"status": "ok", "removidos": removed}


# ── Worker loop ───────────────────────────────────────────────────────────────

_TASK_HANDLERS = {
    "backup":        _task_backup,
    "cleanup_cache": _task_cleanup_cache,
}


def _worker_loop():
    """
    Loop principal da thread de background.
    Bloqueia em _task_queue.get() (sem consumir CPU) até receber uma tarefa.
    Conceito de SO: bloqueio em I/O — o SO suspende a thread e a acorda
    quando há dados na fila (similar a wait() em semáforos).
    """
    logger.info(f"[WORKER] Thread de background iniciada: {threading.current_thread().name}")
    while True:
        try:
            task_id, task_name = _task_queue.get(timeout=1)
            if task_name == "__STOP__":
                logger.info("[WORKER] Thread de background encerrada.")
                break

            handler = _TASK_HANDLERS.get(task_name)
            if not handler:
                logger.warning(f"[WORKER] Tarefa desconhecida: '{task_name}'")
                _task_queue.task_done()
                continue

            logger.info(f"[WORKER] Executando tarefa '{task_name}' (id={task_id})")
            start = time.perf_counter()
            result = handler()
            elapsed = round(time.perf_counter() - start, 3)

            with _results_lock:
                _results[task_id] = {**result, "elapsed_s": elapsed, "task": task_name}

            _task_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"[WORKER] Erro na tarefa '{task_name}': {e}", exc_info=True)
            _task_queue.task_done()


# ── API pública ───────────────────────────────────────────────────────────────

_worker_thread: threading.Thread | None = None


def start_worker():
    """Inicia a thread de background (chamada no lifespan do FastAPI)."""
    global _worker_thread
    _worker_thread = threading.Thread(
        target=_worker_loop,
        name="BackgroundWorker",
        daemon=True,   # thread daemon: encerra junto com o processo principal
    )
    _worker_thread.start()
    logger.info(f"[WORKER] Thread daemon iniciada: {_worker_thread.name} (id={_worker_thread.ident})")


def stop_worker():
    """Envia sinal de parada para a thread (chamada no shutdown do lifespan)."""
    _task_queue.put(("__stop__", "__STOP__"))


def enqueue(task_name: str) -> str:
    """
    Enfileira uma tarefa e retorna o task_id para consulta posterior.
    Não bloqueia — retorna imediatamente (fire-and-forget).
    """
    import uuid
    task_id = str(uuid.uuid4())[:8]
    _task_queue.put_nowait((task_id, task_name))
    logger.debug(f"[WORKER] Tarefa enfileirada: '{task_name}' id={task_id}")
    return task_id


def get_result(task_id: str) -> dict | None:
    """Consulta o resultado de uma tarefa pelo task_id."""
    with _results_lock:
        return _results.get(task_id)


def worker_status() -> dict:
    """Estado atual do worker (para o endpoint /info e relatório técnico)."""
    return {
        "thread_name": _worker_thread.name if _worker_thread else None,
        "thread_alive": _worker_thread.is_alive() if _worker_thread else False,
        "thread_daemon": _worker_thread.daemon if _worker_thread else None,
        "queue_size": _task_queue.qsize(),
        "queue_maxsize": _task_queue.maxsize,
        "completed_tasks": len(_results),
        "active_threads_total": threading.active_count(),
    }
