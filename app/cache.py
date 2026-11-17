import os
import logging
import redis.asyncio as redis

log = logging.getLogger("cache")

CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TTL = int(os.getenv("CACHE_TTL_SECONDS", "30"))

VERSION_KEY = "tasks:version"   # збільшується при кожному записі -> інвалідація
HITS_KEY = "cache:hits"
MISSES_KEY = "cache:misses"

_client = None
_errors = 0  # помилки Redis у цьому процесі (видно в /cache/stats)


def _get_client():
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True,
            # 2 с, а не 0.5: під повним навантаженням CPU event loop затримується,
            # і короткі таймаути перетворювали кожне читання на промах + втрату 0.5 с.
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
        version = await r.get(VERSION_KEY) or "0"
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
    """Після POST/PUT/DELETE: нова версія -> усі старі ключі списку стають недосяжними."""
    if not CACHE_ENABLED:
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
    return {"enabled": True, "hits": hits, "misses": misses,
            "hit_ratio": round(hits / total, 4) if total else None,
            "errors_this_instance": _errors}
