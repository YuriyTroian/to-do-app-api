# Розгортання REST-сервісу в AWS (лабораторні роботи 1 і 2)

### Публічна адреса застосунку
- **Base URL:** http://todo-api-alb-725788838.eu-north-1.elb.amazonaws.com
- **Swagger UI:** http://todo-api-alb-725788838.eu-north-1.elb.amazonaws.com/docs
- **Health Check:** http://todo-api-alb-725788838.eu-north-1.elb.amazonaws.com/health

### Структура проєкту
```text
.
├── .github/workflows/deploy.yml # CI/CD пайплайн (збірка образу і пуш в ECR)
├── Dockerfile                   # Docker-образ
├── requirements.txt             # Залежності Python
├── requirements-dev.txt         # Залежності для тестів
├── main.py                      # Точка входу (FastAPI)
├── app/                         # Код застосунку: crud, кеш (cache.py), ідемпотентність (idempotency.py)
├── tests/                       # Тести (pytest)
├── main.tf                      # Лаба 1: VPC, RDS, ECR, ECS, ALB, IAM
├── autoscaling.tf               # Лаба 2: автомасштабування і розклад
├── monitoring.tf                # Лаба 2: панель CloudWatch і сповіщення на пошту
├── cache.tf                     # Лаба 2: Redis (ElastiCache)
├── loadtest/                    # Лаба 2: сценарій навантаження k6 і результати прогонів
├── docs/                        # Лаба 2: документація і знімки
├── docker-compose.yml           # Локальний запуск застосунку з БД
└── README.md
```

## Лабораторна робота 2: автоскейлінг, моніторинг, кешування

| Завдання | Документ |
|---|---|
| Автоматичне масштабування | [docs/AUTOSCALING.md](docs/AUTOSCALING.md) |
| Навантажувальне тестування | [docs/LOADTEST.md](docs/LOADTEST.md), [loadtest/README.md](loadtest/README.md) |
| Сповіщення | [docs/ALERTS.md](docs/ALERTS.md) |
| Кешування | [docs/CACHE.md](docs/CACHE.md) |
| Ідемпотентність (бонус) | [docs/IDEMPOTENCY.md](docs/IDEMPOTENCY.md) |
| Масштабування за розкладом (бонус) | [docs/SCHEDULE.md](docs/SCHEDULE.md) |

Запуск навантаження: `k6 run loadtest/script.js`. Тести: `pip install -r requirements.txt -r requirements-dev.txt && pytest -v tests`.
