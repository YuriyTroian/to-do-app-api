"""Ідемпотентність POST /tasks/ через заголовок Idempotency-Key (Redis).

Схема:
1. Перший запит із ключем "захоплює" ключ у Redis (SET NX) зі станом "processing".
2. Після успішного виконання результат зберігається під цим ключем на 24 години.
3. Повторний запит із тим самим ключем не виконується: повертається збережена відповідь.
4. Той самий ключ з іншим тілом запиту — 422, ключ, що ще виконується, — 409.
5. Якщо виконання впало, ключ видаляється, щоб клієнт міг повторити запит.
"""
import hashlib
import json
import logging

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app import cache

log = logging.getLogger("idempotency")

RESULT_TTL = 24 * 3600   # результат зберігається 24 години
LOCK_TTL = 60            # стан "processing" живе недовго: якщо сервер впав посеред запиту


def fingerprint(body: dict) -> str:
    """Відбиток тіла запиту: щоб виявити повторне використання ключа з іншими даними."""
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _redis_key(key: str) -> str:
    return f"idem:{key}"


async def begin(key: str, fp: str):
    """None — запит треба виконувати; JSONResponse — це повтор, віддати збережену відповідь."""
    rk = _redis_key(key)
    try:
        r = cache._get_client()
        claimed = await r.set(rk, json.dumps({"status": "processing", "fp": fp}), nx=True, ex=LOCK_TTL)
        if claimed:
            return None
        raw = await r.get(rk)
    except Exception as e:
        # Без Redis гарантувати ідемпотентність не можна — краще відмовити, ніж створити дубль.
        log.warning("idempotency store failed: %r", e)
        raise HTTPException(status_code=503, detail="Idempotency store unavailable")

    if raw is None:  # ключ щойно сплив між SET і GET
        raise HTTPException(status_code=409, detail="Retry the request")

    state = json.loads(raw)
    if state["fp"] != fp:
        raise HTTPException(status_code=422, detail="Idempotency-Key was already used with a different request body")
    if state["status"] == "processing":
        raise HTTPException(status_code=409, detail="A request with this Idempotency-Key is still being processed")

    return JSONResponse(
        content=state["response"],
        status_code=state["status_code"],
        headers={"Idempotent-Replayed": "true"},
    )


async def complete(key: str, fp: str, response: dict, status_code: int = 200):
    try:
        await cache._get_client().set(
            _redis_key(key),
            json.dumps({"status": "done", "fp": fp, "response": response, "status_code": status_code}),
            ex=RESULT_TTL,
        )
    except Exception as e:
        log.warning("idempotency complete failed: %r", e)


async def abort(key: str):
    try:
        await cache._get_client().delete(_redis_key(key))
    except Exception as e:
        log.warning("idempotency abort failed: %r", e)
