"""
reports/pdf_report.py
Geração de relatório PDF por médico — lista todas as consultas agendadas.

Conceito de SO: Operações de I/O
  - Escrita sequencial em arquivo binário via sistema de arquivos do SO.
  - reportlab usa buffers internos e faz flush() ao fechar o arquivo,
    garantindo que todos os bytes chegaram ao disco antes de retornar.
  - O arquivo é salvo em data/relatorios/ com timestamp no nome,
    seguindo as convenções de path do SO atual (pathlib).
  - A geração é delegada ao worker thread para não bloquear o event loop.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from config.logger import setup_logger
from config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()
TZ = ZoneInfo("America/Fortaleza")


def _fmt_dt(dt: datetime) -> str:
    """Formata datetime para exibição local."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ).strftime("%d/%m/%Y %H:%M")


def generate_doctor_pdf(doctor_data: dict, appointments: list[dict]) -> Path:
    """
    Gera um PDF com as consultas de um médico específico.

    Parâmetros:
        doctor_data  : dict com campos do médico (name, crm, specialty)
        appointments : lista de dicts com campos da consulta

    Retorna o Path do arquivo gerado.

    Conceito de SO: I/O — criação de arquivo binário no filesystem,
    com nome único baseado em timestamp para evitar colisões.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = doctor_data["name"].replace(" ", "_").replace(".", "")
    filename = f"relatorio_medico_{safe_name}_{ts}.pdf"
    filepath = settings.RELATORIOS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=16, textColor=colors.HexColor("#1a3c5e"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#555555"),
        spaceAfter=2,
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#333333"),
    )

    story = []

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    story.append(Paragraph("Sistema de Agendamento de Consultas Médicas", title_style))
    story.append(Paragraph("Relatório de Consultas por Médico", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3c5e")))
    story.append(Spacer(1, 0.4 * cm))

    # ── Dados do médico ───────────────────────────────────────────────────────
    info_data = [
        ["Médico:", doctor_data["name"]],
        ["CRM:", doctor_data["crm"]],
        ["Especialidade:", doctor_data["specialty"]],
        ["Gerado em:", _fmt_dt(datetime.now(timezone.utc))],
        ["Total de consultas:", str(len(appointments))],
        ["SO:", f"{settings.OS_NAME} | PID {__import__('os').getpid()}"],
    ]
    info_table = Table(info_data, colWidths=[4 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.HexColor("#1a3c5e")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.3 * cm))

    # ── Tabela de consultas ───────────────────────────────────────────────────
    if not appointments:
        story.append(Paragraph("Nenhuma consulta encontrada para este médico.", label_style))
    else:
        headers = ["#", "Data/Hora", "Paciente", "Status", "Observações"]
        rows = [headers]
        for i, apt in enumerate(appointments, 1):
            rows.append([
                str(i),
                _fmt_dt(datetime.fromisoformat(apt["scheduled_at"])),
                apt["patient_name"],
                apt["status"].upper(),
                (apt.get("notes") or "—")[:40],
            ])

        col_widths = [1 * cm, 4 * cm, 5 * cm, 3 * cm, 4 * cm]
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Cabeçalho
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 9),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            # Corpo
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("GRID",         (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    doc.build(story)

    size_kb = filepath.stat().st_size // 1024
    logger.info(f"[PDF] Gerado: {filename} ({size_kb} KB, {len(appointments)} consultas)")
    return filepath
