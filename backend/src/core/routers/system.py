"""
core/routers/system.py
Endpoints para monitoramento e administração do sistema operacional.

Conceitos de SO implementados:
- GET  /system/info          → Informações do SO (uname, PID, CPUs, paths)
- GET  /system/threads       → Estado das threads e lock de agendamento
- GET  /system/cache         → Estatísticas do cache em memória
- GET  /system/permissions   → Permissões nos diretórios de dados
- POST /system/backup        → Dispara backup do banco em background
- POST /system/cleanup       → Limpeza de cache expirado em background
- GET  /system/task/{id}     → Resultado de tarefa assíncrona
"""

from fastapi import APIRouter, HTTPException, status
from config.settings import get_settings
from concorrencia.workers import enqueue, get_result, worker_status
from concorrencia.locks import lock_status
from storage.cache import all_cache_stats
import os

router = APIRouter(prefix="/system", tags=["Sistema (SO)"])
settings = get_settings()


@router.get("/info", tags=["Sistema (SO)"])
async def system_info_full():
    """
    Expõe informações completas do SO e ambiente.
    Chamadas de sistema: uname(2), getpid(2), os.cpu_count(), sysconf('SC_PHYS_PAGES').
    """
    return settings.info()


@router.get("/threads", tags=["Sistema (SO)"])
async def system_threads():
    """
    Estado das threads em execução e locks de sincronização.
    Conceito de SO: Threads e Sincronização.
    """
    return {
        "sistema": "Threads e Sincronização",
        "worker": worker_status(),
        "lock_agendamento": lock_status(),
    }


@router.get("/cache", tags=["Sistema (SO)"])
async def system_cache_stats():
    """
    Estatísticas do cache em memória (hits, misses, TTL).
    Conceito de SO: Gerência de Memória.
    """
    return {
        "sistema": "Cache em Memória",
        "caches": all_cache_stats(),
    }


@router.get("/permissions", tags=["Sistema (SO)"])
async def system_permissions():
    """
    Verifica permissões nos diretórios de dados do sistema.
    Chamadas de sistema: access(2) — verifica R/W/X.
    """
    dirs = {
        "base_dir": str(settings.BASE_DIR),
        "data_dir": str(settings.DATA_DIR),
        "logs_dir": str(settings.LOGS_DIR),
        "backups_dir": str(settings.BACKUPS_DIR),
        "reports_dir": str(settings.RELATORIOS_DIR),
        "cache_dir": str(settings.CACHE_DIR),
    }

    perms = {}
    for name, path in dirs.items():
        p = os.path.exists(path)
        r = os.access(path, os.R_OK) if p else False
        w = os.access(path, os.W_OK) if p else False
        x = os.access(path, os.X_OK) if p else False
        perms[name] = {
            "path": path,
            "existe": p,
            "readable": r,
            "writable": w,
            "executable": x,
        }

    return {
        "sistema": "Permissões do Filesystem",
        "diretórios": perms,
    }


@router.post("/backup", status_code=status.HTTP_202_ACCEPTED, tags=["Sistema (SO)"])
async def system_backup():
    """
    Dispara backup do banco de dados em background.
    Retorna 202 + task_id imediatamente.
    Conceito de SO: I/O assíncrono em thread separada.
    """
    task_id = enqueue("backup")
    return {
        "status": "processing",
        "task_id": task_id,
        "msg": f"Backup sendo executado. Consulte /system/task/{task_id} para o resultado.",
    }


@router.post("/cleanup", status_code=status.HTTP_202_ACCEPTED, tags=["Sistema (SO)"])
async def system_cleanup():
    """
    Dispara limpeza de cache expirado em background.
    Retorna 202 + task_id imediatamente.
    Conceito de SO: Limpeza de página expirada (page reclaim).
    """
    task_id = enqueue("cleanup_cache")
    return {
        "status": "processing",
        "task_id": task_id,
        "msg": f"Limpeza sendo executada. Consulte /system/task/{task_id} para o resultado.",
    }


@router.get("/task/{task_id}", tags=["Sistema (SO)"])
async def system_task_result(task_id: str):
    """
    Consulta o resultado de uma tarefa de sistema (backup, cleanup, etc).
    """
    result = get_result(task_id)

    if result is None:
        return {
            "status": "pending",
            "task_id": task_id,
            "msg": "Tarefa ainda está em processamento.",
        }

    return {
        "status": "done",
        "task_id": task_id,
        "resultado": result,
    }
