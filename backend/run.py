"""
run.py — inicia o servidor Uvicorn a partir da raiz do projeto.
Execute com:  python run.py
"""

import sys
from pathlib import Path

# Garante que src/ está no PYTHONPATH independente de onde o script é chamado
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"[SO] Sistema Operacional: {settings.OS_NAME} {settings.OS_VERSION}")
    print(f"[SO] Encoding padrão:     {settings.ENCODING}")
    print(f"[SO] Diretório base:      {settings.BASE_DIR}")
    print(f"[DB] Banco de dados:      {settings.DATABASE_URL}")
    print(f"[API] Iniciando em http://{settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        app_dir=str(Path(__file__).parent / "src"),
        log_level=settings.LOG_LEVEL.lower(),
    )
