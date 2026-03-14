#  To-Do API

Простий REST API для управління завданнями, створений на FastAPI з використанням PostgreSQL та SQLAlchemy.

---

## Можливості

- Створення нового завдання
- Отримання списку всіх завдань
- Отримання завдання за ID
- Оновлення завдання
- Видалення завдання
- Отримання статистики по виконаних завданнях

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

`DATABASE_URL = "postgresql://username:password@localhost:5432/dbname"`

`DATABASE_URL = "postgresql+asyncpg://postgres:47911974@localhost:5432/to-do-app-api"`

---

## Запуск app


_.\to-do-app-api_
```bash
uvicorn main:app --reload_
```

_з якимось конкретним портом ---> uvicorn main:app --reload --port 8080_

---
## ⚙️ Конфігурація `.env`

Створи `.env` файл у корені проєкту:3

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=47911974
POSTGRES_DB=to-do-app-api
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

DATABASE_URL=postgresql+asyncpg://postgres:47911974@localhost:5432/to-do-app-api

```



---
##  API Ендпоінти
* **POST /tasks** — Створення завдань (приймає title, description та priority).
* **GET /tasks/** — Список усіх завдань.
* **GET /tasks/{task_id}** — Отримання конкретного завдання за id.
* **DELETE /tasks/{task_id}** — Видалення завдання.
* **PUT /tasks/{task_id}** — Редагування завдання.
* **GET /stats** — Статистика виконаних завдань.

---

##  Запуск через Docker
```powershell
# З кореня проекту виконайте:
docker-compose up --build
```
Після запуску сервіси будуть доступні за адресами:

* **Backend API**: <http://localhost:8000>

* **Swagger (Документація)**: <http://localhost:8000/docs>

* **Database (PostgreSQL)**: localhost:5432
---



