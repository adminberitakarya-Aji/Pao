# Secrets Module for PAO

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}

# KMS Key for Secrets Manager
resource "aws_kms_key" "secrets" {
  description             = "KMS key for Secrets Manager"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "key-default-1"
    Statement = [{
      Sid    = "Allow administration of the key"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }
      Action   = "kms:*"
      Resource = "*"
    }, {
      Sid    = "Allow Secrets Manager to use the key"
      Effect = "Allow"
      Principal = {
        Service = "secretsmanager.amazonaws.com"
      }
      Action = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ]
      Resource = "*"
    }]
  })

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-secrets-kms"
    Environment = var.environment
  })
}

data "aws_caller_identity" "current" {}

# Alias for easier reference
resource "aws_kms_alias" "secrets" {
  name          = "alias/pao/${var.environment}/secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# Application Secrets
resource "aws_secretsmanager_secret" "app" {
  name        = "pao/${var.environment}/app"
  description = "Application configuration secrets"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-app-secrets"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    app_env = var.environment
    log_level = "info"
    feature_flags = "{}"
  })
}

# JWT Secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "aws_secretsmanager_secret" "jwt" {
  name        = "pao/${var.environment}/auth/jwt"
  description = "JWT signing secret"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-jwt-secret"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "jwt" {
  secret_id = aws_secretsmanager_secret.jwt.id
  secret_string = jsonencode({
    secret = random_password.jwt_secret.result
    algorithm = "RS256"
  })
}

# Database credentials (created in databases module, referenced here)
# These are just references - actual creation happens in databases module

# Redis credentials (created in databases module)

# External API Keys
resource "aws_secretsmanager_secret" "openai" {
  name        = "pao/${var.environment}/external/openai"
  description = "OpenAI API key"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-openai-key"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "openai" {
  secret_id = aws_secretsmanager_secret.openai.id
  secret_string = jsonencode({
    api_key = ""  # To be filled manually or via CI/CD
  })
}

resource "aws_secretsmanager_secret" "anthropic" {
  name        = "pao/${var.environment}/external/anthropic"
  description = "Anthropic API key"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-anthropic-key"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "anthropic" {
  secret_id = aws_secretsmanager_secret.anthropic.id
  secret_string = jsonencode({
    api_key = ""  # To be filled manually or via CI/CD
  })
}

resource "aws_secretsmanager_secret" "elevenlabs" {
  name        = "pao/${var.environment}/external/elevenlabs"
  description = "ElevenLabs API key for TTS"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-elevenlabs-key"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "elevenlabs" {
  secret_id = aws_secretsmanager_secret.elevenlabs.id
  secret_string = jsonencode({
    api_key = ""  # To be filled manually or via CI/CD
  })
}

# Sentry DSN
resource "aws_secretsmanager_secret" "sentry" {
  name        = "pao/${var.environment}/observability/sentry"
  description = "Sentry DSN for error tracking"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-sentry-dsn"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "sentry" {
  secret_id = aws_secretsmanager_secret.sentry.id
  secret_string = jsonencode({
    dsn = ""  # To be filled manually or via CI/CD
  })
}

# Datadog API Key
resource "aws_secretsmanager_secret" "datadog" {
  name        = "pao/${var.environment}/observability/datadog"
  description = "Datadog API key"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-datadog-key"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "datadog" {
  secret_id = aws_secretsmanager_secret.datadog.id
  secret_string = jsonencode({
    api_key = ""  # To be filled manually or via CI/CD
  })
}

# Firebase/FCM credentials
resource "aws_secretsmanager_secret" "firebase" {
  name        = "pao/${var.environment}/mobile/firebase"
  description = "Firebase configuration for push notifications"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-firebase-config"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "firebase" {
  secret_id = aws_secretsmanager_secret.firebase.id
  secret_string = jsonencode({
    project_id = ""
    private_key = ""
    client_email = ""
    api_key = ""
  })
}

# Apple Push Notification credentials
resource "aws_secretsmanager_secret" "apns" {
  name        = "pao/${var.environment}/mobile/apns"
  description = "APNs certificates and keys"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-apns-credentials"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "apns" {
  secret_id = aws_secretsmanager_secret.apns.id
  secret_string = jsonencode({
    key_id = ""
    team_id = ""
    bundle_id = ""
    private_key = ""
  })
}

# Google OAuth credentials
resource "aws_secretsmanager_secret" "google_oauth" {
  name        = "pao/${var.environment}/auth/google"
  description = "Google OAuth credentials"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-google-oauth"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "google_oauth" {
  secret_id = aws_secretsmanager_secret.google_oauth.id
  secret_string = jsonencode({
    client_id = ""
    client_secret = ""
  })
}

# Apple OAuth credentials
resource "aws_secretsmanager_secret" "apple_oauth" {
  name        = "pao/${var.environment}/auth/apple"
  description = "Apple Sign In credentials"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-apple-oauth"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "apple_oauth" {
  secret_id = aws_secretsmanager_secret.apple_oauth.id
  secret_string = jsonencode({
    client_id = ""
    team_id = ""
    key_id = ""
    private_key = ""
  })
}

# TLS Certificates (for internal mTLS)
resource "aws_secretsmanager_secret" "mtls_ca" {
  name        = "pao/${var.environment}/mtls/ca"
  description = "mTLS CA certificate and key"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-mtls-ca"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "mtls_ca" {
  secret_id = aws_secretsmanager_secret.mtls_ca.id
  secret_string = jsonencode({
    ca_cert = ""
    ca_key = ""
  })
}

# Outputs
output "kms_key_arn" {
  value = aws_kms_key.secrets.arn
}

output "app_secret_arn" {
  value = aws_secretsmanager_secret.app.arn
}

output "jwt_secret_arn" {
  value = aws_secretsmanager_secret.jwt.arn
}

output "openai_secret_arn" {
  value = aws_secretsmanager_secret.openai.arn
}

output "anthropic_secret_arn" {
  value = aws_secretsmanager_secret.anthropic.arn
}

output "elevenlabs_secret_arn" {
  value = aws_secretsmanager_secret.elevenlabs.arn
}

output "sentry_secret_arn" {
  value = aws_secretsmanager_secret.sentry.arn
}

output "datadog_secret_arn" {
  value = aws_secretsmanager_secret.datadog.arn
}

output "firebase_secret_arn" {
  value = aws_secretsmanager_secret.firebase.arn
}

output "apns_secret_arn" {
  value = aws_secretsmanager_secret.apns.arn
}

output "google_oauth_secret_arn" {
  value = aws_secretsmanager_secret.google_oauth.arn
}

output "apple_oauth_secret_arn" {
  value = aws_secretsmanager_secret.apple_oauth.arn
}

output "mtls_ca_secret_arn" {
  value = aws_secretsmanager_secret.mtls_ca.arn
}