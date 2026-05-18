"""
reports/csv_report.py
Geração de relatório CSV com exportação geral de todas as consultas.

Conceito de SO: Operações de I/O / Sistema de Arquivos
  - Escrita sequencial em arquivo de texto via csv.writer (bufferizado).
  - Encoding definido conforme o SO (utf-8-sig no Windows para compatibilidade
    com Excel; utf-8 no Linux/macOS) — detectado em settings.ENCODING.
  - newline='' é exigido pelo módulo csv no Python para evitar dupla quebra
    de linha no Windows (diferença de filesystem entre \n e \r\n).
  - O arquivo é salvo em data/relatorios/ com timestamp único.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from config.logger import setup_logger
from config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()
TZ = ZoneInfo("America/Fortaleza")


def _fmt_dt(dt_str: str) -> str:
    """Converte ISO datetime string para formato local legível."""
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return dt_str


def generate_full_csv(appointments: list[dict]) -> Path:
    """
    Gera um CSV com todas as consultas do sistema.

    Parâmetros:
        appointments : lista de dicts com campos completos da consulta

    Retorna o Path do arquivo gerado.

    Conceito de SO: encoding específico por plataforma + newline handling
    do filesystem (\\r\\n no Windows, \\n no Unix).
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"relatorio_geral_{ts}.csv"
    filepath = settings.RELATORIOS_DIR / filename

    # newline='' é obrigatório para csv.writer no Python (evita \r\r\n no Windows)
    # encoding=settings.ENCODING → utf-8-sig no Windows (BOM p/ Excel), utf-8 no Linux
    with open(filepath, "w", newline="", encoding=settings.ENCODING) as f:
        writer = csv.writer(f)

        # ── Metadados do relatório ────────────────────────────────────────────
        writer.writerow(["# Sistema de Agendamento de Consultas Médicas"])
        writer.writerow(["# Relatório Geral de Consultas"])
        writer.writerow([f"# Gerado em: {_fmt_dt(datetime.now(timezone.utc).isoformat())}"])
        writer.writerow([f"# Total de registros: {len(appointments)}"])
        writer.writerow([f"# SO: {settings.OS_NAME} | Encoding: {settings.ENCODING}"])
        writer.writerow([])

        # ── Cabeçalho ────────────────────────────────────────────────────────
        writer.writerow([
            "ID", "Data/Hora", "Status",
            "Paciente", "CPF", "Médico", "CRM", "Especialidade", "Observações",
        ])

        # ── Dados ─────────────────────────────────────────────────────────────
        for apt in appointments:
            writer.writerow([
                apt["id"],
                _fmt_dt(apt["scheduled_at"]),
                apt["status"],
                apt["patient_name"],
                apt["patient_cpf"],
                apt["doctor_name"],
                apt["doctor_crm"],
                apt["doctor_specialty"],
                apt.get("notes") or "",
            ])

    size_kb = filepath.stat().st_size
    logger.info(f"[CSV] Gerado: {filename} ({size_kb} bytes, {len(appointments)} registros)")
    return filepath
