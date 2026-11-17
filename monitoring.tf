# Лаба 2, завдання 3 (панель моніторингу) і 4 (сповіщення).
# Імена ресурсів відповідають main.tf: api_cluster, api_service, api_alb.

locals {
  cluster_name = aws_ecs_cluster.api_cluster.name
  service_name = aws_ecs_service.api_service.name
  alb_suffix   = aws_lb.api_alb.arn_suffix
}

# ---------------------------------------------------------------------------
# Завдання 3: панель з п'ятьма графіками
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "api" {
  dashboard_name = "todo-api-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric", x = 0, y = 0, width = 12, height = 6
        properties = {
          title  = "Екземпляри (бажана і фактична кількість)"
          region = "eu-north-1"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["ECS/ContainerInsights", "DesiredTaskCount", "ClusterName", local.cluster_name, "ServiceName", local.service_name, { label = "Desired" }],
            ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", local.cluster_name, "ServiceName", local.service_name, { label = "Running" }]
          ]
        }
      },
      {
        type = "metric", x = 12, y = 0, width = 12, height = 6
        properties = {
          title  = "Завантаження CPU, %"
          region = "eu-north-1"
          view   = "timeSeries"
          stat   = "Average"
          period = 60
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", local.cluster_name, "ServiceName", local.service_name]
          ]
          annotations = {
            horizontal = [
              { label = "Ціль масштабування 60%", value = 60 },
              { label = "Поріг сповіщення 70%", value = 70 }
            ]
          }
          yAxis = { left = { min = 0, max = 100 } }
        }
      },
      {
        type = "metric", x = 0, y = 6, width = 12, height = 6
        properties = {
          title  = "Запити за хвилину"
          region = "eu-north-1"
          view   = "timeSeries"
          stat   = "Sum"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", local.alb_suffix]
          ]
        }
      },
      {
        type = "metric", x = 12, y = 6, width = 12, height = 6
        properties = {
          title  = "Латентність p95, с"
          region = "eu-north-1"
          view   = "timeSeries"
          stat   = "p95"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", local.alb_suffix]
          ]
        }
      },
      {
        type = "metric", x = 0, y = 12, width = 12, height = 6
        properties = {
          title  = "Відповіді 5xx"
          region = "eu-north-1"
          view   = "timeSeries"
          stat   = "Sum"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", local.alb_suffix]
          ]
        }
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# Завдання 4: сповіщення на пошту (CPU > 70% протягом 2 хвилин + лист про норму)
# ---------------------------------------------------------------------------
variable "alert_email" {
  description = "Email для сповіщень"
  type        = string
}

resource "aws_sns_topic" "alerts" {
  name = "todo-api-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "todo-api-cpu-high"
  alarm_description   = "Середнє завантаження CPU сервісу > 70% протягом 2 хвилин"
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 60
  evaluation_periods  = 2
  threshold           = 70
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = local.cluster_name
    ServiceName = local.service_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn] # лист при тривозі
  ok_actions    = [aws_sns_topic.alerts.arn] # лист при поверненні до норми
}
