# Root Module Variables for PAO Infrastructure

variable "environment" {
  type        = string
  description = "Environment name (e.g., dev, staging, prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "domain_name" {
  type        = string
  description = "Primary domain name for the application"
  default     = "pao.ai"
}

variable "hosted_zone_id" {
  type        = string
  description = "Route53 Hosted Zone ID for the domain"
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM Certificate ARN for the domain (us-east-1)"
}

variable "gcp_project_id" {
  type        = string
  description = "GCP Project ID for multi-cloud resources"
  default     = ""
}

variable "azure_subscription_id" {
  type        = string
  description = "Azure Subscription ID for multi-cloud resources"
  default     = ""
}

variable "datadog_api_key" {
  type        = string
  description = "Datadog API Key for observability"
  sensitive   = true
}

variable "github_org" {
  type        = string
  description = "GitHub organization name"
  default     = "adminberitakarya-Aji"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
  default     = "Pao"
}

# Region-specific CIDR blocks (optional overrides)
variable "vpc_cidr_blocks" {
  type = map(string)
  default = {
    "us-east-1"       = "10.0.0.0/16"
    "eu-west-1"       = "10.1.0.0/16"
    "ap-southeast-1"  = "10.2.0.0/16"
  }
  description = "VPC CIDR blocks per region"
}

# EKS Node Group configurations per region
variable "eks_node_groups" {
  type = map(object({
    general = list(object({
      name           = string
      instance_types = list(string)
      min_size       = number
      max_size       = number
      desired_size   = number
    }))
    gpu = list(object({
      name           = string
      instance_types = list(string)
      min_size       = number
      max_size       = number
      desired_size   = number
    }))
    memory = list(object({
      name           = string
      instance_types = list(string)
      min_size       = number
      max_size       = number
      desired_size   = number
    }))
  }))
  default = {
    "us-east-1" = {
      general = [{
        name           = "general"
        instance_types = ["m7i.large", "m7i.xlarge"]
        min_size       = 2
        max_size       = 10
        desired_size   = 3
      }]
      gpu = [{
        name           = "gpu"
        instance_types = ["g5.xlarge", "g5.2xlarge"]
        min_size       = 0
        max_size       = 4
        desired_size   = 0
      }]
      memory = [{
        name           = "memory"
        instance_types = ["r7i.large", "r7i.xlarge"]
        min_size       = 0
        max_size       = 4
        desired_size   = 0
      }]
    }
    "eu-west-1" = {
      general = [{
        name           = "general"
        instance_types = ["m7i.large", "m7i.xlarge"]
        min_size       = 1
        max_size       = 5
        desired_size   = 2
      }]
      gpu = [{
        name           = "gpu"
        instance_types = ["g5.xlarge", "g5.2xlarge"]
        min_size       = 0
        max_size       = 2
        desired_size   = 0
      }]
      memory = [{
        name           = "memory"
        instance_types = ["r7i.large", "r7i.xlarge"]
        min_size       = 0
        max_size       = 2
        desired_size   = 0
      }]
    }
    "ap-southeast-1" = {
      general = [{
        name           = "general"
        instance_types = ["m7i.large", "m7i.xlarge"]
        min_size       = 1
        max_size       = 5
        desired_size   = 2
      }]
      gpu = [{
        name           = "gpu"
        instance_types = ["g5.xlarge", "g5.2xlarge"]
        min_size       = 0
        max_size       = 2
        desired_size   = 0
      }]
      memory = [{
        name           = "memory"
        instance_types = ["r7i.large", "r7i.xlarge"]
        min_size       = 0
        max_size       = 2
        desired_size   = 0
      }]
    }
  }
  description = "EKS node group configurations per region"
}

# Database configurations
variable "database_config" {
  type = object({
    postgres = object({
      instance_class    = string
      allocated_storage = number
      max_allocated_storage = number
      engine_version    = string
      multi_az          = bool
      backup_retention  = number
    })
    redis = object({
      node_type      = string
      num_cache_nodes = number
      engine_version  = string
      automatic_failover = bool
    })
  })
  default = {
    postgres = {
      instance_class         = "db.r6g.large"
      allocated_storage      = 100
      max_allocated_storage  = 500
      engine_version         = "16.3"
      multi_az               = true
      backup_retention       = 30
    }
    redis = {
      node_type            = "cache.r7g.large"
      num_cache_nodes      = 2
      engine_version       = "7.1"
      automatic_failover   = true
    }
  }
  description = "Database instance configurations"
}

# Common tags
variable "common_tags" {
  type = map(string)
  default = {
    Project     = "pao"
    ManagedBy   = "terraform"
    Owner       = "platform"
    Repository  = "github.com/adminberitakarya-Aji/Pao"
  }
  description = "Common tags applied to all resources"
}