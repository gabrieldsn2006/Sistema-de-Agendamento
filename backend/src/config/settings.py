"""
config/settings.py
Configurações da aplicação — detecta SO e define paths adequados.
Conceito de SO: Chamadas de Sistema (platform API, paths, permissões)
"""

import os
import platform
from pathlib import Path
from functools import lru_cache


class Settings:
    # ── Identificação do SO ──────────────────────────────────────────────────
    OS_NAME: str = platform.system()          # 'Windows', 'Linux', 'Darwin'
    OS_VERSION: str = platform.version()
    ENCODING: str = "utf-8-sig" if platform.system() == "Windows" else "utf-8"

    # ── Diretório raiz do projeto ────────────────────────────────────────────
    # Resolve o path absoluto independente de onde o processo é iniciado
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # ── Diretórios de dados (estrutura de arquivos do SO) ───────────────────
    DATA_DIR: Path        = BASE_DIR / "data"
    CONSULTAS_DIR: Path   = DATA_DIR / "consultas"
    RELATORIOS_DIR: Path  = DATA_DIR / "relatorios"
    LOGS_DIR: Path        = DATA_DIR / "logs"
    BACKUPS_DIR: Path     = DATA_DIR / "backups"
    CACHE_DIR: Path       = DATA_DIR / "cache"

    # ── Banco de dados SQLite ────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'agendamento.db'}"

    # ── API ──────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["*"]

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str    = "DEBUG"
    LOG_MAX_BYTES: int  = 5 * 1024 * 1024   # 5 MB por arquivo de log
    LOG_BACKUP_COUNT: int = 3               # mantém até 3 arquivos rotacionados

    def __init__(self):
        self._ensure_directories()

    def _ensure_directories(self):
        """
        Cria os diretórios necessários com permissões adequadas por SO.
        Conceito de SO: criação de estrutura de diretórios + permissões.
        """
        dirs = [
            self.CONSULTAS_DIR,
            self.RELATORIOS_DIR,
            self.LOGS_DIR,
            self.BACKUPS_DIR,
            self.CACHE_DIR,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            # Em sistemas Unix, garante permissão 755 para os diretórios
            if self.OS_NAME != "Windows":
                os.chmod(d, 0o755)

    def info(self) -> dict:
        """Retorna informações do ambiente atual (útil para debug e relatório)."""
        return {
            "os": self.OS_NAME,
            "os_version": self.OS_VERSION,
            "encoding": self.ENCODING,
            "base_dir": str(self.BASE_DIR),
            "data_dir": str(self.DATA_DIR),
            "database": self.DATABASE_URL,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton das configurações — instanciado uma única vez."""
    return Settings()
