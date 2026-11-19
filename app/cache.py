import os
import logging
import redis.asyncio as redis

log = logging.getLogger("cache")

CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TTL = int(os.getenv("CACHE_TTL_SECONDS", "30"))
# За замовчуванням кеш списку живе лише TTL (30 с): клієнт може бачити застарілий список
# до 30 с після запису, зате частка влучань висока. З CACHE_INVALIDATE_ON_WRITE=true кожен
# запис скидає всі кешовані списки (дані свіжі, але при частих записах кеш майже не працює).
INVALIDATE_ON_WRITE = os.getenv("CACHE_INVALIDATE_ON_WRITE", "false").lower() == "true"

VERSION_KEY = "tasks:version"   # збільшується при кожному записі, якщо INVALIDATE_ON_WRITE
HITS_KEY = "cache:hits"
MISSES_KEY = "cache:misses"

_client = None
_errors = 0  # помилки Redis у цьому процесі (видно в /cache/stats)


def _get_client():
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True,
            # Таймаут 2 с: під повним навантаженням CPU event loop затримується,
            # і коротший таймаут перетворював би читання на промахи.
            socket_connect_timeout=2, socket_timeout=2,
        )
    return _client


def _count_error(what: str, e: Exception):
    global _errors
    _errors += 1
    log.warning("redis %s failed: %r", what, e)


async def cache_get(offset: int, limit: int):
    """Повертає (json_str | None, key | None). Помилки Redis не ламають сервіс."""
    if not CACHE_ENABLED:
        return None, None
    try:
        r = _get_client()
        # Версію читаємо лише якщо увімкнена інвалідація: це зайве звернення до Redis.
        version = (await r.get(VERSION_KEY) or "0") if INVALIDATE_ON_WRITE else "0"
        key = f"tasks:list:v{version}:{offset}:{limit}"
        data = await r.get(key)
        await r.incr(HITS_KEY if data else MISSES_KEY)
        return data, key
    except Exception as e:
        _count_error("get", e)
        return None, None


async def cache_set(key: str | None, payload: str):
    if not CACHE_ENABLED or key is None:
        return
    try:
        await _get_client().set(key, payload, ex=TTL)
    except Exception as e:
        _count_error("set", e)


async def cache_invalidate():
    """Після POST/PUT/DELETE (якщо INVALIDATE_ON_WRITE): нова версія -> старі ключі списку недосяжні."""
    if not CACHE_ENABLED or not INVALIDATE_ON_WRITE:
        return
    try:
        await _get_client().incr(VERSION_KEY)
    except Exception as e:
        _count_error("invalidate", e)


async def cache_stats():
    if not CACHE_ENABLED:
        return {"enabled": False}
    r = _get_client()
    hits = int(await r.get(HITS_KEY) or 0)
    misses = int(await r.get(MISSES_KEY) or 0)
    total = hits + misses
    return {"enabled": True, "invalidate_on_write": INVALIDATE_ON_WRITE, "ttl": TTL,
            "hits": hits, "misses": misses,
            "hit_ratio": round(hits / total, 4) if total else None,
            "errors_this_instance": _errors}
