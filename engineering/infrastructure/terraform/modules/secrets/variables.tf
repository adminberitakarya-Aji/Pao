# Secrets Module Variables

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "kms_key_description" {
  type        = string
  description = "KMS key description"
  default     = "PAO secrets encryption key"
}

variable "kms_deletion_window_days" {
  type        = number
  description = "KMS key deletion window in days"
  default     = 30
}

variable "enable_key_rotation" {
  type        = bool
  description = "Enable automatic KMS key rotation"
  default     = true
}

variable "secret_prefix" {
  type        = string
  description = "Prefix for secret names"
  default     = "pao"
}

variable "app_secrets" {
  description = "Application secrets to create"
  type = map(object({
    description = string
    generate_string = optional(object({
      length  = number
      special = bool
    }))
    kms_key_id = optional(string)
  }))
  default = {
    "app/config" = {
      description = "Application configuration"
      generate_string = {
        length  = 64
        special = true
      }
    }
    "app/jwt-secret" = {
      description = "JWT signing secret"
      generate_string = {
        length  = 64
        special = true
      }
    }
    "app/encryption-key" = {
      description = "Application encryption key"
      generate_string = {
        length  = 32
        special = false
      }
    }
  }
}

variable "external_api_secrets" {
  description = "External API secrets"
  type = map(object({
    description = string
    kms_key_id  = optional(string)
  }))
  default = {
    "external/github-token" = {
      description = "GitHub Personal Access Token"
    }
    "external/slack-webhook" = {
      description = "Slack webhook URL"
    }
    "external/pagerduty-key" = {
      description = "PagerDuty integration key"
    }
  }
}

variable "oauth_secrets" {
  description = "OAuth client secrets"
  type = map(object({
    description = string
    kms_key_id  = optional(string)
  }))
  default = {
    "oauth/github/client-secret" = {
      description = "GitHub OAuth client secret"
    }
    "oauth/google/client-secret" = {
      description = "Google OAuth client secret"
    }
  }
}

variable "mtls_certificates" {
  description = "mTLS certificates"
  type = map(object({
    description = string
    kms_key_id  = optional(string)
  }))
  default = {
    "mtls/ca-cert" = {
      description = "mTLS CA certificate"
    }
    "mtls/server-cert" = {
      description = "mTLS server certificate"
    }
    "mtls/server-key" = {
      description = "mTLS server private key"
    }
    "mtls/client-ca-cert" = {
      description = "mTLS client CA certificate"
    }
  }
}

variable "database_secrets" {
  description = "Database credentials"
  type = map(object({
    description = string
    kms_key_id  = optional(string)
  }))
  default = {
    "database/postgres/username" = {
      description = "PostgreSQL username"
    }
    "database/postgres/password" = {
      description = "PostgreSQL password"
      generate_string = {
        length  = 32
        special = true
      }
    }
    "database/redis/auth-token" = {
      description = "Redis auth token"
      generate_string = {
        length  = 32
        special = false
      }
    }
  }
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}