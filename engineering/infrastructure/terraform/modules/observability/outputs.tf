# Observability Module Outputs

output "cloudwatch_log_groups" {
  description = "Map of CloudWatch log group names"
  value = {
    eks_cluster       = aws_cloudwatch_log_group.eks_cluster.name
    eks_irsa          = aws_cloudwatch_log_group.eks_irsa.name
    application       = aws_cloudwatch_log_group.application.name
    audit             = aws_cloudwatch_log_group.audit.name
    security          = aws_cloudwatch_log_group.security.name
    synthetic         = aws_cloudwatch_log_group.synthetic.name
  }
}

output "cloudwatch_metric_alarms" {
  description = "Map of CloudWatch metric alarm ARNs"
  value = {
    high_cpu              = aws_cloudwatch_metric_alarm.high_cpu.arn
    high_memory           = aws_cloudwatch_metric_alarm.high_memory.arn
    high_disk             = aws_cloudwatch_metric_alarm.high_disk.arn
    alb_5xx               = aws_cloudwatch_metric_alarm.alb_5xx.arn
    alb_latency           = aws_cloudwatch_metric_alarm.alb_latency.arn
    rds_cpu               = aws_cloudwatch_metric_alarm.rds_cpu.arn
    rds_connections       = aws_cloudwatch_metric_alarm.rds_connections.arn
    rds_storage           = aws_cloudwatch_metric_alarm.rds_storage.arn
    redis_cpu             = aws_cloudwatch_metric_alarm.redis_cpu.arn
    redis_memory          = aws_cloudwatch_metric_alarm.redis_memory.arn
    redis_evictions       = aws_cloudwatch_metric_alarm.redis_evictions.arn
  }
}

output "xray_sampling_rule_arn" {
  description = "X-Ray sampling rule ARN"
  value       = aws_xray_sampling_rule.main.arn
}

output "xray_encryption_config" {
  description = "X-Ray encryption configuration"
  value       = aws_xray_encryption_config.main
}

output "synthetics_canary_arns" {
  description = "Map of Synthetics canary ARNs"
  value = {
    api_health      = aws_synthetics_canary.api_health.arn
    frontend_health = aws_synthetics_canary.frontend_health.arn
    auth_health     = aws_synthetics_canary.auth_health.arn
  }
}

output "synthetics_canary_names" {
  description = "Map of Synthetics canary names"
  value = {
    api_health      = aws_synthetics_canary.api_health.name
    frontend_health = aws_synthetics_canary.frontend_health.name
    auth_health     = aws_synthetics_canary.auth_health.name
  }
}

output "datadog_monitors" {
  description = "Map of Datadog monitor IDs"
  value = {
    api_health       = datadog_monitor.api_health.id
    api_latency      = datadog_monitor.api_latency.id
    api_error_rate   = datadog_monitor.api_error_rate.id
    kubernetes_nodes = datadog_monitor.kubernetes_nodes.id
    kubernetes_pods  = datadog_monitor.kubernetes_pods.id
    rds_cpu          = datadog_monitor.rds_cpu.id
    rds_storage      = datadog_monitor.rds_storage.id
    redis_memory     = datadog_monitor.redis_memory.id
  }
}

output "slo_dashboard_urls" {
  description = "Map of SLO dashboard URLs"
  value = {
    api_slo  = datadog_dashboard.api_slo.url
    infra_slo = datadog_dashboard.infra_slo.url
  }
}

output "sns_topic_arns" {
  description = "Map of SNS topic ARNs for notifications"
  value = {
    critical = aws_sns_topic.critical.arn
    warning  = aws_sns_topic.warning.arn
    info     = aws_sns_topic.info.arn
  }
}