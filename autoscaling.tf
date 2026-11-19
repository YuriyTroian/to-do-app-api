# Автоматичне горизонтальне масштабування ECS-сервісу (Application Auto Scaling).
#
# Структура:
#   1. aws_appautoscaling_target        — діапазон кількості екземплярів (мін / макс);
#   2. політики step scaling + два сигнали CloudWatch — додавання й вилучення екземплярів
#      за кількістю запитів на екземпляр;
#   3. заплановані дії                  — різний мінімум удень і вночі.

resource "aws_appautoscaling_target" "ecs" {
  service_namespace  = "ecs"
  scalable_dimension = "ecs:service:DesiredCount"
  resource_id        = "service/${aws_ecs_cluster.api_cluster.name}/${aws_ecs_service.api_service.name}"

  min_capacity = 1
  max_capacity = 3 # за умовою не більше 4

  # Мінімум змінюють заплановані дії нижче (день/ніч), тож Terraform не повинен
  # повертати min_capacity до значення з коду при наступному apply.
  lifecycle {
    ignore_changes = [min_capacity, max_capacity]
  }
}

# ---------------------------------------------------------------------------
# Додавання екземплярів
#
# Метрика — кількість запитів за хвилину на один екземпляр (ALB RequestCountPerTarget).
# Вона росте разом із навантаженням із самого початку, тому сигнал спрацьовує раніше, ніж
# за CPU, який зростає ступінчасто.
#
# Сигнал за одну хвилинну точку — швидка реакція; кількість доданих екземплярів залежить
# від того, наскільки перевищено поріг.
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_policy" "scale_out" {
  name               = "requests-step-scale-out"
  policy_type        = "StepScaling"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  resource_id        = aws_appautoscaling_target.ecs.resource_id

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    metric_aggregation_type = "Average"
    cooldown                = 60 # після додавання чекаємо хвилину, поки нові екземпляри вплинуть на метрику

    # Межі кроків відраховуються від порога сигналу (1500 запитів/хв на екземпляр):
    step_adjustment {
      metric_interval_lower_bound = 0 # 1500–2500 запитів/хв -> +1 екземпляр
      metric_interval_upper_bound = 1000
      scaling_adjustment          = 1
    }
    step_adjustment {
      metric_interval_lower_bound = 1000 # від 2500 запитів/хв -> +2 екземпляри
      scaling_adjustment          = 2
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "scale_out" {
  alarm_name          = "todo-api-scale-out-requests"
  alarm_description   = "Запитів на екземпляр >= 1500 за хвилину — додати екземпляри"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "RequestCountPerTarget"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1 # одна хвилинна точка: швидка реакція
  threshold           = 1500
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TargetGroup  = aws_lb_target_group.api_tg.arn_suffix
    LoadBalancer = aws_lb.api_alb.arn_suffix
  }

  alarm_actions = [aws_appautoscaling_policy.scale_out.arn]
}

# ---------------------------------------------------------------------------
# Вилучення екземплярів
#
# Повільніше за додавання: навантаження має бути низьким три хвилини поспіль, а після кожного
# вилучення діє cooldown. Недобір ресурсів шкодить користувачам, зайвий екземпляр —
# лише коштує, тож обережність на вилученні виправдана.
# Коли запитів немає зовсім, ALB не публікує метрику, тому відсутні дані
# вважаємо порушенням (treat_missing_data = breaching), інакше сигнал ніколи б не спрацював.
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_policy" "scale_in" {
  name               = "requests-step-scale-in"
  policy_type        = "StepScaling"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  resource_id        = aws_appautoscaling_target.ecs.resource_id

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    metric_aggregation_type = "Average"
    cooldown                = 120

    step_adjustment {
      metric_interval_upper_bound = 0 # нижче порога сигналу -> -1 екземпляр
      scaling_adjustment          = -1
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "scale_in" {
  alarm_name          = "todo-api-scale-in-requests"
  alarm_description   = "Запитів на екземпляр < 600 за хвилину три хвилини поспіль — вилучити екземпляр"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "RequestCountPerTarget"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 3 # три хвилини поспіль: захист від гойдалки (flapping)
  threshold           = 600
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"

  dimensions = {
    TargetGroup  = aws_lb_target_group.api_tg.arn_suffix
    LoadBalancer = aws_lb.api_alb.arn_suffix
  }

  alarm_actions = [aws_appautoscaling_policy.scale_in.arn]
}

# ---------------------------------------------------------------------------
# Масштабування за розкладом (різний мінімум удень і вночі)
# Удень (08:00–22:00 за київським часом) мінімум 2 екземпляри, вночі — 1.
# До нуля не масштабуємо: сервіс стоїть за ALB, а ECS не запускає задачі з нуля
# за вхідним запитом, тож перший запит після простою отримав би 503.
# ---------------------------------------------------------------------------
resource "aws_appautoscaling_scheduled_action" "day" {
  name               = "day-min-2"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  schedule           = "cron(0 8 * * ? *)"
  timezone           = "Europe/Kyiv"

  scalable_target_action {
    min_capacity = 2
    max_capacity = 3
  }
}

resource "aws_appautoscaling_scheduled_action" "night" {
  name               = "night-min-1"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  schedule           = "cron(0 22 * * ? *)"
  timezone           = "Europe/Kyiv"

  scalable_target_action {
    min_capacity = 1
    max_capacity = 3
  }
}
