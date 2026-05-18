"""
Sistema de Agendamento de Consultas Médicas
Ponto de entrada da aplicação FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import get_settings
from config.logger import setup_logger
from config.database import init_db
from concorrencia.workers import start_worker, stop_worker
import core.models  # garante que todos os models são registrados no Base.metadata
from core.routers import appointments, doctors, patients, reports, system

settings = get_settings()
logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação (startup / shutdown)."""
    logger.info("Iniciando sistema de agendamento...")
    logger.info(f"SO detectado   : {settings.OS_NAME}")
    logger.info(f"Diretório base : {settings.BASE_DIR}")
    logger.info(f"Banco de dados : {settings.DATABASE_URL}")
    await init_db()
    logger.info("Tabelas criadas/verificadas com sucesso.")
    start_worker()
    logger.info("Worker de background iniciado.")
    yield
    logger.info("Encerrando sistema de agendamento.")
    stop_worker()


app = FastAPI(
    title="Sistema de Agendamento de Consultas Médicas",
    version="1.0.0",
    description="API REST para agendamento de consultas médicas com conceitos de SO",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registrar routers ────────────────────────────────────────────────────────
app.include_router(appointments.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(reports.router)
app.include_router(system.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "online",
        "sistema": "Agendamento de Consultas Médicas",
        "versao": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.get("/info", tags=["health"])
async def system_info():
    """Expõe informações do SO e ambiente (útil para o relatório técnico)."""
    return settings.info()
