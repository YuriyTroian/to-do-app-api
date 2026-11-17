# Лаба 2, завдання 1: автоматичне горизонтальне масштабування ECS-сервісу.
# Імена ресурсів підставлено з твого main.tf (api_cluster, api_service).

resource "aws_appautoscaling_target" "ecs" {
  service_namespace  = "ecs"
  scalable_dimension = "ecs:service:DesiredCount"
  resource_id        = "service/${aws_ecs_cluster.api_cluster.name}/${aws_ecs_service.api_service.name}"

  min_capacity = 1
  max_capacity = 3 # за умовою не більше 4
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-target-tracking"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  resource_id        = aws_appautoscaling_target.ecs.resource_id

  target_tracking_scaling_policy_configuration {
    target_value       = 60  # цільове середнє завантаження CPU, %
    scale_out_cooldown = 60  # додаємо екземпляри швидко
    scale_in_cooldown  = 300 # вилучаємо повільно, щоб не гойдатися

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# ---------------------------------------------------------------------------
# ДОДАЙ у наявні ресурси з лаби 1 (не створюй нові):
#
# 1) В aws_ecs_service.api_service, щоб Terraform не скидав кількість екземплярів,
#    яку змінює автомасштабування:
#
#    lifecycle {
#      ignore_changes = [desired_count]
#    }
#
# 2) В aws_ecs_cluster.api_cluster, щоб для завдання 3 з'явилися метрики
#    RunningTaskCount / DesiredTaskCount:
#
#    setting {
#      name  = "containerInsights"
#      value = "enabled"
#    }
# ---------------------------------------------------------------------------
