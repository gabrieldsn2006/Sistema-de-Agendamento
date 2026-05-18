"""
config/database.py
Configuração do banco de dados SQLite com SQLAlchemy assíncrono.
Conceito de SO: I/O assíncrono — aiosqlite libera a thread enquanto aguarda
               operações de leitura/escrita no sistema de arquivos.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config.settings import get_settings

settings = get_settings()

# Converte a URL sqlite:/// para sqlite+aiosqlite:///
_async_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(
    _async_url,
    echo=settings.DEBUG,       # loga SQL no console em modo debug
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe base para todos os models SQLAlchemy."""
    pass


async def init_db() -> None:
    """Cria todas as tabelas no banco (idempotente)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependência FastAPI — fornece uma sessão por request."""
    async with AsyncSessionLocal() as session:
        yield session
