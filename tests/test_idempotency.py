"""Тести ідемпотентності POST /tasks/ (заголовок Idempotency-Key).

Запуск з кореня проєкту:
    pip install -r requirements.txt -r requirements-dev.txt
    pytest -v tests

Тести не потребують ані PostgreSQL, ані Redis: база — SQLite у тимчасовій теці,
Redis замінено простим in-memory об'єктом із тими самими методами.
"""
import os
import tempfile

# Має бути виставлено ДО імпорту застосунку: app.db читає DATABASE_URL при імпорті.
_DB_FILE = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_FILE}"
os.environ["CACHE_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

from app import cache
from app.app import app


class FakeRedis:
    """Мінімальна заміна redis.asyncio.Redis для методів, які використовує застосунок."""

    def __init__(self):
        self.data = {}

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        self.data.pop(key, None)

    async def incr(self, key):
        self.data[key] = int(self.data.get(key, 0)) + 1
        return self.data[key]


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(cache, "_get_client", lambda: fake)
    return fake


@pytest.fixture
def client():
    with TestClient(app) as c:  # with — щоб виконався lifespan (створення таблиць)
        yield c


def count_tasks(client, title):
    tasks = client.get("/tasks/").json()
    return sum(1 for t in tasks if t["title"] == title)


def test_same_key_twice_creates_one_row_and_returns_same_response(client):
    body = {"title": "idem-one", "description": "x", "priority": 1001}
    headers = {"Idempotency-Key": "key-aaa"}

    first = client.post("/tasks/", json=body, headers=headers)
    second = client.post("/tasks/", json=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()            # дві однакові відповіді (той самий id)
    assert "idempotent-replayed" not in first.headers
    assert second.headers["idempotent-replayed"] == "true"
    assert count_tasks(client, "idem-one") == 1      # один запис у базі


def test_without_key_the_duplicate_is_executed_again(client):
    """Контрольний тест: без ключа другий такий самий запит знову йде в базу
    і падає на унікальному priority — дубль не «ховається»."""
    body = {"title": "no-key", "description": "x", "priority": 1002}
    safe = TestClient(app, raise_server_exceptions=False)

    first = safe.post("/tasks/", json=body)
    second = safe.post("/tasks/", json=body)

    assert first.status_code == 200
    assert second.status_code == 500


def test_same_key_different_body_is_rejected(client):
    headers = {"Idempotency-Key": "key-bbb"}
    first = client.post("/tasks/", json={"title": "idem-two", "priority": 1003}, headers=headers)
    second = client.post("/tasks/", json={"title": "idem-two-other", "priority": 1004}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 422
    assert count_tasks(client, "idem-two-other") == 0


def test_different_keys_create_different_rows(client):
    a = client.post("/tasks/", json={"title": "idem-three-a", "priority": 1005}, headers={"Idempotency-Key": "k1"})
    b = client.post("/tasks/", json={"title": "idem-three-b", "priority": 1006}, headers={"Idempotency-Key": "k2"})

    assert a.json()["id"] != b.json()["id"]
    assert count_tasks(client, "idem-three-a") == 1
    assert count_tasks(client, "idem-three-b") == 1


def test_key_still_processing_returns_409(client, fake_redis):
    from app import idempotency
    from app.schemas import TaskCreate

    body = {"title": "idem-four", "priority": 1007}
    fp = idempotency.fingerprint(TaskCreate(**body).model_dump())  # так само, як у create_task
    fake_redis.data["idem:key-ccc"] = '{"status": "processing", "fp": "%s"}' % fp

    resp = client.post("/tasks/", json=body, headers={"Idempotency-Key": "key-ccc"})

    assert resp.status_code == 409
    assert count_tasks(client, "idem-four") == 0


def test_failed_request_releases_the_key(client):
    """Якщо виконання впало (тут — конфлікт унікального priority), ключ видаляється,
    і клієнт може повторити запит після виправлення."""
    client.post("/tasks/", json={"title": "idem-five-base", "priority": 1008})
    safe = TestClient(app, raise_server_exceptions=False)

    failed = safe.post("/tasks/", json={"title": "idem-five", "priority": 1008}, headers={"Idempotency-Key": "key-ddd"})
    assert failed.status_code == 500

    # Той самий ключ, але вже без конфлікту: тіло інше, проте ключ звільнено, тож запит виконується.
    retry = safe.post("/tasks/", json={"title": "idem-five", "priority": 1009}, headers={"Idempotency-Key": "key-ddd"})
    assert retry.status_code == 200
    assert count_tasks(client, "idem-five") == 1
