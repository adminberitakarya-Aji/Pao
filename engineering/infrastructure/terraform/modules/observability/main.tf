# Observability Module for PAO

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    datadog = {
      source  = "datadog/datadog"
      version = "~> 3.0"
    }
  }
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "datadog_api_key" {
  type        = string
  description = "Datadog API key"
  sensitive   = true
}

variable "datadog_app_key" {
  type        = string
  description = "Datadog Application key"
  sensitive   = true
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for VPC endpoints"
  default     = ""
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs"
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/pao/${var.environment}/application"
  retention_in_days = var.environment == "prod" ? 90 : 30

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-app-logs"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "audit" {
  name              = "/aws/pao/${var.environment}/audit"
  retention_in_days = 365

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-audit-logs"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "security" {
  name              = "/aws/pao/${var.environment}/security"
  retention_in_days = 365

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-security-logs"
    Environment = var.environment
  })
}

# CloudWatch Metric Filters for Application Logs
resource "aws_cloudwatch_metric_filter" "error_rate" {
  name           = "pao-${var.environment}-error-rate"
  log_group_name = aws_cloudwatch_log_group.application.name
  pattern        = "[timestamp, level=ERROR, ...]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "PAO/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_filter" "latency_p99" {
  name           = "pao-${var.environment}-latency-p99"
  log_group_name = aws_cloudwatch_log_group.application.name
  pattern        = "[timestamp, level, request_id, latency=*, ...]"

  metric_transformation {
    name      = "RequestLatency"
    namespace = "PAO/Application"
    value     = "$latency"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "pao-${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorCount"
  namespace           = "PAO/Application"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "High error rate detected in application"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-high-error-rate"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "pao-${var.environment}-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "RequestLatency"
  namespace           = "PAO/Application"
  period              = 60
  statistic           = "Maximum"
  threshold           = 5000
  alarm_description   = "High latency detected (P99 > 5s)"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-high-latency"
    Environment = var.environment
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "pao-${var.environment}-alerts"

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-alerts"
    Environment = var.environment
  })
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "alerts@pao.ai"
}

# X-Ray Tracing
resource "aws_xray_sampling_rule" "default" {
  rule_name        = "pao-${var.environment}-default"
  priority         = 1000
  fixed_target     = 1
  rate             = 0.1
  service_name     = "*"
  service_type     = "*"
  host             = "*"
  http_method      = "*"
  url_path         = "*"
  resource_arn     = "*"
  attributes       = {}
}

# Datadog Integration (if API key provided)
resource "datadog_monitor" "high_error_rate" {
  count = var.datadog_api_key != "" ? 1 : 0

  name               = "[PAO ${upper(var.environment)}] High Error Rate"
  type               = "metric alert"
  message            = "High error rate detected in ${var.environment} environment. @slack-pao-alerts"
  query              = "avg(last_5m):sum:traces.${var.environment}.error.rate{*} > 0.05"
  tags               = ["environment:${var.environment}", "team:platform"]
  notify_no_data     = false
  renotify_interval  = 300
  timeout_h          = 1

  thresholds {
    critical = 0.05
    warning  = 0.01
  }
}

resource "datadog_monitor" "high_latency" {
  count = var.datadog_api_key != "" ? 1 : 0

  name               = "[PAO ${upper(var.environment)}] High Latency"
  type               = "metric alert"
  message            = "High latency detected in ${var.environment} environment. @slack-pao-alerts"
  query              = "avg(last_5m):percentile:traces.${var.environment}.duration{*} > 5000"
  tags               = ["environment:${var.environment}", "team:platform"]
  notify_no_data     = false
  renotify_interval  = 300
  timeout_h          = 1

  thresholds {
    critical = 5000
    warning  = 2000
  }
}

resource "datadog_monitor" "deployment_failure" {
  count = var.datadog_api_key != "" ? 1 : 0

  name               = "[PAO ${upper(var.environment)}] Deployment Failure"
  type               = "metric alert"
  message            = "Deployment failure detected in ${var.environment}. @slack-pao-alerts"
  query              = "sum(last_5m):count:ci.deployment.failure{environment:${var.environment}} > 0"
  tags               = ["environment:${var.environment}", "team:platform"]
  notify_no_data     = false
  renotify_interval  = 0
  timeout_h          = 1

  thresholds {
    critical = 1
  }
}

# Synthetic Monitoring
resource "aws_synthetics_canary" "api_health" {
  name = "pao-${var.environment}-api-health"
  code {
    s3_bucket = aws_s3_bucket.synthetics.bucket
    s3_key    = aws_s3_object.canary_code.key
    handler   = "index.handler"
  }
  execution_role_arn = aws_iam_role.synthetics.arn
  runtime_version    = "syn-nodejs-puppeteer-3.9"
  schedule {
    expression = "rate(5 minutes)"
  }
  vpc_config {
    subnet_ids        = var.private_subnet_ids
    security_group_ids = [aws_security_group.synthetics.id]
  }
  start_canary = true

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-api-health"
    Environment = var.environment
  })
}

resource "aws_s3_bucket" "synthetics" {
  bucket = "pao-${var.environment}-synthetics-${data.aws_caller_identity.current.account_id}-${var.region}"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-synthetics"
    Environment = var.environment
  })
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_s3_object" "canary_code" {
  bucket = aws_s3_bucket.synthetics.bucket
  key    = "canary/api-health.zip"
  source = "synthetics/api-health.zip"
  etag   = filemd5("synthetics/api-health.zip")
}

resource "aws_iam_role" "synthetics" {
  name = "pao-${var.environment}-synthetics-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "synthetics" {
  name = "pao-${var.environment}-synthetics-policy"
  role = aws_iam_role.synthetics.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords",
        "cloudwatch:PutMetricData"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_security_group" "synthetics" {
  count = length(var.private_subnet_ids) > 0 ? 1 : 0

  name        = "pao-${var.environment}-synthetics-sg"
  description = "Security group for Synthetics canaries"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-synthetics-sg"
    Environment = var.environment
  })
}

# Service Level Objectives (SLOs) - CloudWatch Dashboards
resource "aws_cloudwatch_dashboard" "slo" {
  dashboard_name = "PAO-${upper(var.environment)}-SLOs"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", "pao-${var.environment}-api", {stat: "p99"}],
            ["...", "pao-${var.environment}-worker", {stat: "p99"}]
          ]
          period = 300
          stat   = "p99"
          region = var.region
          title  = "API P99 Latency"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", "pao-${var.environment}-api"],
            ["...", "pao-${var.environment}-worker"]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "Error Rate"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiName", "pao-${var.environment}"],
            ["...", "5XXError"]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "API Gateway Latency & Errors"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "pao-${var.environment}-postgres"],
            ["...", "DatabaseConnections"],
            ["...", "FreeStorageSpace"]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "RDS Health"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-slo-dashboard"
    Environment = var.environment
  })
}

# Outputs
output "alerts_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "log_groups" {
  value = {
    application = aws_cloudwatch_log_group.application.name
    audit       = aws_cloudwatch_log_group.audit.name
    security    = aws_cloudwatch_log_group.security.name
  }
}