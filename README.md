# 📝 To-Do API

Простий REST API для управління завданнями, створений на FastAPI з використанням PostgreSQL та SQLAlchemy.

---

## Можливості

- Створення нового завдання
- Отримання списку всіх завдань
- Отримання завдання за ID
- Оновлення завдання
- Видалення завдання

---

## Технології

- Python 3.x
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL

---

## Встановлення

```bash
git clone https://github.com/YuriyTroian/to-do-app-api.git
cd to-do-app-api
python -m venv venv
source venv/bin/activate  # або .\venv\Scripts\activate на Windows
pip install -r requirements.txt
```

---

## Налаштування DB

database.py

`DATABASE_URL = "postgresql://username:password@localhost/dbname"`

`DATABASE_URL = "postgresql+asyncpg://postgres:47911974@localhost:5432/to-do-app-api"`

---

## Запуск app


_.\to-do-app-api_

_uvicorn main:app --reload_

_з якимось конкретним портом ---> uvicorn main:app --reload --port 8080_



