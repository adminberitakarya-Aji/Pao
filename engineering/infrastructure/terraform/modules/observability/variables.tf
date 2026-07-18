# Observability Module Variables

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for CloudWatch endpoints"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for VPC endpoints"
}

variable "datadog_api_key" {
  type        = string
  description = "Datadog API Key"
  sensitive   = true
}

variable "datadog_app_key" {
  type        = string
  description = "Datadog Application Key"
  sensitive   = true
}

variable "enable_datadog" {
  type        = bool
  description = "Enable Datadog integration"
  default     = true
}

variable "enable_cloudwatch" {
  type        = bool
  description = "Enable CloudWatch logs/metrics/alarms"
  default     = true
}

variable "enable_xray" {
  type        = bool
  description = "Enable X-Ray tracing"
  default     = true
}

variable "enable_synthetics" {
  type        = bool
  description = "Enable Synthetics canaries"
  default     = true
}

variable "synthetics_runtime_version" {
  type        = string
  description = "Synthetics runtime version"
  default     = "syn-nodejs-puppeteer-3.10"
}

variable "synthetics_schedule" {
  type        = string
  description = "Synthetics canary schedule (cron expression or rate)"
  default     = "rate(5 minutes)"
}

variable "synthetics_retention_days" {
  type        = number
  description = "Synthetics results retention in days"
  default     = 30
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 30
}

variable "enable_slo_dashboards" {
  type        = bool
  description = "Create SLO dashboards"
  default     = true
}

variable "slo_targets" {
  type = map(object({
    service_level_indicator = string
    target                  = number
    time_window             = string
  }))
  default = {
    "api_availability" = {
      service_level_indicator = "availability"
      target                  = 99.9
      time_window             = "30d"
    }
    "api_latency_p99" = {
      service_level_indicator = "latency"
      target                  = 500
      time_window             = "30d"
    }
    "error_rate" = {
      service_level_indicator = "error_rate"
      target                  = 0.1
      time_window             = "30d"
    }
  }
}

variable "notification_channels" {
  type = map(object({
    type    = string
    config  = map(string)
  }))
  default = {}
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}