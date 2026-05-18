"""
core/errors.py
Handler global de exceções — padroniza todos os erros da API no formato:
  { "erro": "...", "detalhe": "...", "status": 422 }

Conceito de SO: tratamento de sinais/exceções — centraliza o fluxo de erro
               assim como um SO centraliza o tratamento de interrupções.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from config.logger import setup_logger

logger = setup_logger(__name__)


def _error_body(status: int, erro: str, detalhe: str | list) -> dict:
    return {"status": status, "erro": erro, "detalhe": detalhe}


def register_error_handlers(app: FastAPI) -> None:
    """Registra handlers globais de erro no app FastAPI."""

    # ── Erros de negócio / HTTP explícitos ───────────────────────────────────
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP {exc.status_code} em {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                status=exc.status_code,
                erro=_http_label(exc.status_code),
                detalhe=exc.detail,
            ),
        )

    # ── Erros de validação Pydantic (body inválido) ───────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        erros = []
        for e in exc.errors():
            campo = " → ".join(str(loc) for loc in e["loc"] if loc != "body")
            erros.append(f"{campo}: {e['msg']}" if campo else e["msg"])
        logger.warning(f"Validação falhou em {request.url.path}: {erros}")
        return JSONResponse(
            status_code=422,
            content=_error_body(
                status=422,
                erro="Dados inválidos",
                detalhe=erros,
            ),
        )

    # ── Erros inesperados ─────────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Erro interno em {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=_error_body(
                status=500,
                erro="Erro interno do servidor",
                detalhe="Ocorreu um erro inesperado. Consulte os logs para detalhes.",
            ),
        )


def _http_label(status: int) -> str:
    labels = {
        400: "Requisição inválida",
        404: "Não encontrado",
        409: "Conflito",
        422: "Dados inválidos",
        500: "Erro interno",
    }
    return labels.get(status, "Erro")
