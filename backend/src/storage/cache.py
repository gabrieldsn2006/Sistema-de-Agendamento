"""
storage/cache.py
Cache em memória com TTL e limpeza automática em thread separada.

Conceito de SO: Gerência de Memória
  - Estrutura de dados alocada dinamicamente no heap do processo Python.
  - TTL (Time-To-Live) controla o tempo de vida de cada entrada —
    análogo ao page aging em algoritmos de substituição de páginas.
  - Thread de limpeza (daemon) percorre o cache periodicamente e descarta
    entradas expiradas, liberando referências para o GC do Python
    (equivalente funcional do page reclaim do SO).
  - threading.RLock garante acesso exclusivo durante leitura/escrita
    (evita leitura de entrada parcialmente atualizada por outra thread).

Conceito de SO: Concorrência
  - RLock (reentrant lock) permite que a mesma thread adquira o lock
    múltiplas vezes sem deadlock — útil quando métodos internos se chamam.
"""

import threading
import time
from typing import Any

from config.logger import setup_logger

logger = setup_logger(__name__)

# TTL padrão: 5 minutos
DEFAULT_TTL = 300


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expires_at = time.monotonic() + ttl   # monotonic: imune a mudanças de relógio do SO

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class MemoryCache:
    """
    Cache em memória thread-safe com TTL por entrada.
    Limpeza automática em thread daemon.
    """

    def __init__(self, name: str = "default", cleanup_interval: int = 60):
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.RLock()
        self._name = name
        self._hits = 0
        self._misses = 0

        # Thread de limpeza automática
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            args=(cleanup_interval,),
            name=f"CacheCleanup-{name}",
            daemon=True,
        )
        self._cleanup_thread.start()
        logger.debug(f"[CACHE] Cache '{name}' iniciado (limpeza a cada {cleanup_interval}s)")

    # ── Interface pública ────────────────────────────────────────────────────

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                if entry:
                    del self._store[key]   # remove entrada expirada imediatamente
                self._misses += 1
                return None
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        with self._lock:
            self._store[key] = _CacheEntry(value, ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove todas as entradas cujas chaves começam com prefix."""
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            if keys:
                logger.debug(f"[CACHE] Invalidadas {len(keys)} entradas com prefixo '{prefix}'")
            return len(keys)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "nome":        self._name,
                "entradas":    len(self._store),
                "hits":        self._hits,
                "misses":      self._misses,
                "hit_rate":    round(self._hits / total, 3) if total else 0.0,
                "thread_viva": self._cleanup_thread.is_alive(),
            }

    # ── Loop de limpeza (roda em thread daemon) ──────────────────────────────

    def _cleanup_loop(self, interval: int):
        """
        Percorre o cache e remove entradas expiradas a cada `interval` segundos.
        Conceito de SO: o SO suspende esta thread durante o sleep e a acorda
        após o intervalo (via SIGALRM interno do scheduler).
        """
        while True:
            time.sleep(interval)
            self._evict_expired()

    def _evict_expired(self):
        with self._lock:
            expired = [k for k, e in self._store.items() if e.is_expired()]
            for k in expired:
                del self._store[k]
            if expired:
                logger.debug(f"[CACHE] Evicted {len(expired)} entradas expiradas do cache '{self._name}'")


# ── Instâncias singleton por domínio ─────────────────────────────────────────
# Cada domínio tem seu próprio cache para facilitar invalidação seletiva.

appointment_cache = MemoryCache(name="appointments", cleanup_interval=60)
doctor_cache      = MemoryCache(name="doctors",      cleanup_interval=120)
patient_cache     = MemoryCache(name="patients",     cleanup_interval=120)


def all_cache_stats() -> list[dict]:
    return [
        appointment_cache.stats(),
        doctor_cache.stats(),
        patient_cache.stats(),
    ]
