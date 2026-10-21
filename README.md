# Лабораторна робота 1: Розгортання застосунку в AWS

### Публічна адреса застосунку
- **Base URL:** http://todo-api-alb-1289293129.eu-north-1.elb.amazonaws.com
- **Swagger UI:** http://todo-api-alb-1289293129.eu-north-1.elb.amazonaws.com/docs
- **Health Check:** http://todo-api-alb-1289293129.eu-north-1.elb.amazonaws.com/health

### Структура проєкту
```text
.
├── .github/workflows/deploy.yml # CI/CD пайплайн
├── Dockerfile                   # Docker-образ
├── requirements.txt             # Залежності Python
├── main.py                      # REST API (FastAPI)
├── main.tf                      # Опис інфраструктури (IaC) AWS (VPC, RDS, ECR, ECS, ALB, IAM)
├── docker-compose.yml           # Локальний запуск застосунку з БД
└── README.md
```