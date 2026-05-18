"""
core/routers/reports.py
Endpoints de relatórios — geração assíncrona e download direto.

POST /reports/pdf/doctor/{id}  → gera PDF das consultas de um médico (202)
POST /reports/csv              → gera CSV geral de todas as consultas (202)
GET  /reports/task/{task_id}   → consulta resultado da geração
GET  /reports/download/{filename} → download do arquivo gerado
GET  /reports/list             → lista arquivos de relatórios disponíveis
"""

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from config.database import get_session
from config.settings import get_settings
from concorrencia.workers import get_result
from reports.report_service import enqueue_doctor_pdf, enqueue_full_csv
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/reports", tags=["Relatórios"])
settings = get_settings()


@router.post("/pdf/doctor/{doctor_id}", status_code=202)
async def generate_doctor_pdf(
    doctor_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Gera PDF com as consultas de um médico.
    Retorna 202 + task_id imediatamente — geração ocorre em thread separada.
    Conceito de SO: I/O assíncrono via thread de background.
    """
    task_id, erro = await enqueue_doctor_pdf(session, doctor_id)
    if erro:
        raise HTTPException(status_code=404, detail=erro)
    return {
        "status":  "processing",
        "task_id": task_id,
        "msg":     f"PDF sendo gerado. Consulte /reports/task/{task_id} para o resultado.",
    }


@router.post("/csv", status_code=202)
async def generate_full_csv(session: AsyncSession = Depends(get_session)):
    """
    Gera CSV com exportação geral de todas as consultas.
    Conceito de SO: encoding específico por plataforma (utf-8-sig / utf-8).
    """
    task_id = await enqueue_full_csv(session)
    return {
        "status":  "processing",
        "task_id": task_id,
        "msg":     f"CSV sendo gerado. Consulte /reports/task/{task_id} para o resultado.",
    }


@router.get("/task/{task_id}")
async def get_report_task(task_id: str):
    """Consulta o resultado de uma tarefa de geração de relatório."""
    result = get_result(task_id)
    if result is None:
        return {"status": "pending", "task_id": task_id}

    # Adiciona URL de download quando disponível
    if result.get("status") == "ok" and result.get("arquivo"):
        filename = Path(result["arquivo"]).name
        result = {**result, "download_url": f"/reports/download/{filename}"}

    return {"status": "done", "task_id": task_id, "result": result}


@router.get("/download/{filename}")
async def download_report(filename: str):
    """
    Faz o download do arquivo de relatório gerado.
    Conceito de SO: FileResponse usa sendfile() internamente — transferência
    de dados diretamente do filesystem para o socket sem copiar para userspace.
    """
    # Segurança: impede path traversal (ex: ../../etc/passwd)
    safe_name = Path(filename).name
    filepath = settings.RELATORIOS_DIR / safe_name

    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo '{safe_name}' não encontrado.")

    if not filepath.is_file():
        raise HTTPException(status_code=400, detail="Caminho inválido.")

    media_type = "application/pdf" if safe_name.endswith(".pdf") else "text/csv"
    return FileResponse(
        path=str(filepath),
        filename=safe_name,
        media_type=media_type,
    )


@router.get("/list")
async def list_reports():
    """
    Lista todos os relatórios gerados disponíveis para download.
    Conceito de SO: leitura de metadados do inode (stat) para tamanho e data.
    """
    files = []
    for f in sorted(settings.RELATORIOS_DIR.iterdir(), reverse=True):
        if f.is_file() and f.suffix in (".pdf", ".csv"):
            stat = f.stat()
            files.append({
                "nome":         f.name,
                "tipo":         f.suffix.lstrip(".").upper(),
                "tamanho_kb":   round(stat.st_size / 1024, 1),
                "criado_em":    stat.st_mtime,
                "download_url": f"/reports/download/{f.name}",
            })
    return {"total": len(files), "arquivos": files}
