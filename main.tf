terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"
}

resource "aws_ecr_repository" "api_repo" {
  name                 = "to-do-app-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_security_group" "rds_sg" {
  name        = "todo-rds-sg"
  description = "Allow PostgreSQL inbound traffic"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Відкриваємо доступ, щоб ти міг підключитися з комп'ютера
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "postgres" {
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t3.micro"
  identifier             = "todo-db"
  db_name                = "todo_db"
  username               = "postgres"
  password               = "SuperSecretPassword123" # Пароль для бази
  skip_final_snapshot    = true
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api_repo.repository_url
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}