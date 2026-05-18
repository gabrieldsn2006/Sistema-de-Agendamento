"""
config/logger.py
Configuração centralizada de logging com rotação de arquivos.
Conceito de SO: Gerência de Dispositivos — logs com timestamp do sistema,
                rotação automática (RotatingFileHandler).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name: str) -> logging.Logger:
    """
    Cria e retorna um logger configurado com:
      - Handler para console (stdout)
      - Handler para arquivo com rotação automática

    A rotação de logs é um conceito de SO: quando o arquivo atinge o tamanho
    máximo, o SO cria um novo arquivo e arquiva o anterior (até LOG_BACKUP_COUNT).
    O timestamp usa o fuso horário local do sistema operacional.
    """
    # Importação local para evitar ciclo circular com settings
    from config.settings import get_settings
    settings = get_settings()

    logger = logging.getLogger(name)

    # Evita adicionar handlers duplicados em reloads
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.DEBUG))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",   # timestamp do SO (hora local)
    )

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # ── File handler com rotação ─────────────────────────────────────────────
    log_file: Path = settings.LOGS_DIR / "agendamento.log"
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding=settings.ENCODING,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
