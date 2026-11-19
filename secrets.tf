# Рядок підключення до бази зберігається в SSM Parameter Store (SecureString, шифрування
# ключем AWS). У визначенні ECS-задачі його немає: задача отримує значення при старті
# через `secrets`, тому пароль не видно ні в консолі ECS, ні в JSON визначення задачі.

resource "aws_ssm_parameter" "database_url" {
  name  = "/todo-api/database-url"
  type  = "SecureString"
  value = "postgresql+asyncpg://postgres:${var.db_password}@${aws_db_instance.postgres.endpoint}/todo_db"
}

data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

# Роль виконання (яка запускає задачу) має право лише прочитати цей параметр і розшифрувати його.
resource "aws_iam_role_policy" "ecs_execution_read_secret" {
  name = "read-database-url"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameters"]
        Resource = [aws_ssm_parameter.database_url.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = [data.aws_kms_alias.ssm.target_key_arn]
      }
    ]
  })
}
