import pytest
from fastapi.testclient import TestClient

from app.app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_stats_counts_match_data(client):
    """/stats рахує агрегатним запитом у базі; результат має збігатися з реальними даними."""
    base = client.get("/stats").json()

    a = client.post("/tasks/", json={"title": "stats-a", "priority": 2001}).json()
    client.post("/tasks/", json={"title": "stats-b", "priority": 2002})
    client.put(f"/tasks/{a['id']}", json={"is_done": True})

    now = client.get("/stats").json()
    assert now["total"] == base["total"] + 2
    assert now["complete"] == base["complete"] + 1
    assert now["pending"] == base["pending"] + 1
