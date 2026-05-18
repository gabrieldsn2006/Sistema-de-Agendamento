"""
config/platform_info.py
Detecção de plataforma e paths específicos por SO.

Conceito de SO: Chamadas de Sistema
  - platform.system() / platform.uname() → syscall uname(2) no Linux
  - os.getpid() → syscall getpid(2)
  - os.cpu_count() → lê /proc/cpuinfo (Linux) ou Registry (Windows)
  - pathlib resolve caminhos conforme as regras do filesystem do SO atual
    (separador '/' no Unix, '\\' no Windows; case-sensitive vs insensitive)
  - Permissões de arquivo são gerenciadas via os.chmod (POSIX) —
    no Windows essa chamada é ignorada silenciosamente pelo Python.
"""

import os
import platform
import sys
from pathlib import Path

from config.logger import setup_logger

logger = setup_logger(__name__)


def get_platform_info() -> dict:
    """
    Coleta informações do SO via chamadas de sistema.
    Retorna um dict rico para o relatório técnico.
    """
    uname = platform.uname()
    return {
        # Identificação do SO
        "so_nome":       uname.system,           # 'Linux', 'Windows', 'Darwin'
        "so_release":    uname.release,
        "so_versao":     uname.version,
        "so_maquina":    uname.machine,          # 'x86_64', 'arm64', ...
        "so_hostname":   uname.node,

        # Processo atual
        "pid":           os.getpid(),            # syscall getpid(2)
        "ppid":          os.getppid(),           # syscall getppid(2)
        "cpu_count":     os.cpu_count(),         # núcleos lógicos disponíveis
        "python_version": sys.version,
        "python_impl":   platform.python_implementation(),  # CPython, PyPy...

        # Filesystem
        "separador_path": os.sep,               # '/' ou '\\'
        "separador_lista": os.pathsep,          # ':' ou ';'
        "encoding_fs":   sys.getfilesystemencoding(),  # encoding do filesystem do SO
        "cwd":           str(Path.cwd()),

        # Paths específicos por SO
        "paths_dados":   _get_data_paths(),
    }


def _get_data_paths() -> dict:
    """
    Retorna paths de dados conforme as convenções de cada SO.
    Conceito de SO: cada sistema tem convenções diferentes para onde
    armazenar dados de aplicação.
    """
    so = platform.system()

    if so == "Windows":
        # Windows: %APPDATA%\sistema_agendamento
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return {
            "so": "Windows",
            "dados_app": str(base / "SistemaAgendamento"),
            "logs":      str(base / "SistemaAgendamento" / "logs"),
            "temp":      str(Path(os.environ.get("TEMP", "C:\\Temp"))),
            "convencao": "%APPDATA%\\SistemaAgendamento",
        }
    elif so == "Darwin":
        # macOS: ~/Library/Application Support/sistema_agendamento
        base = Path.home() / "Library" / "Application Support"
        return {
            "so": "macOS",
            "dados_app": str(base / "SistemaAgendamento"),
            "logs":      str(base / "SistemaAgendamento" / "logs"),
            "temp":      "/tmp",
            "convencao": "~/Library/Application Support/SistemaAgendamento",
        }
    else:
        # Linux/Unix: ~/.local/share/sistema_agendamento (XDG Base Dir Spec)
        xdg = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return {
            "so": "Linux/Unix",
            "dados_app": str(xdg / "sistema_agendamento"),
            "logs":      str(xdg / "sistema_agendamento" / "logs"),
            "temp":      "/tmp",
            "convencao": "~/.local/share/sistema_agendamento (XDG Base Dir Spec)",
        }


def check_permissions(path: Path) -> dict:
    """
    Verifica permissões de leitura/escrita em um diretório.
    Conceito de SO: os.access() usa a syscall access(2) para checar
    permissões reais do processo (considera UID/GID efetivos).
    """
    return {
        "path":      str(path),
        "existe":    path.exists(),
        "leitura":   os.access(path, os.R_OK),  # syscall access(2) com R_OK
        "escrita":   os.access(path, os.W_OK),  # syscall access(2) com W_OK
        "execucao":  os.access(path, os.X_OK),
    }


def log_platform_startup():
    """Loga informações da plataforma na inicialização (para o relatório técnico)."""
    info = get_platform_info()
    logger.info(f"[SO] Sistema  : {info['so_nome']} {info['so_release']}")
    logger.info(f"[SO] Máquina  : {info['so_maquina']}")
    logger.info(f"[SO] PID      : {info['pid']} (PPID={info['ppid']})")
    logger.info(f"[SO] CPUs     : {info['cpu_count']}")
    logger.info(f"[SO] Encoding : {info['encoding_fs']}")
    logger.info(f"[SO] Sep path : '{info['separador_path']}'")
