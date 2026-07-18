# Secrets Module Outputs

output "kms_key_id" {
  description = "KMS Key ID for secrets encryption"
  value       = aws_kms_key.secrets.id
}

output "kms_key_arn" {
  description = "KMS Key ARN for secrets encryption"
  value       = aws_kms_key.secrets.arn
}

output "kms_key_alias" {
  description = "KMS Key alias"
  value       = aws_kms_alias.secrets.name
}

output "app_secret_arns" {
  description = "Map of application secret ARNs"
  value       = { for name, secret in aws_secretsmanager_secret.app : name => secret.arn }
  sensitive   = true
}

output "app_secret_names" {
  description = "Map of application secret names"
  value       = { for name, secret in aws_secretsmanager_secret.app : name => secret.name }
}

output "external_api_secret_arns" {
  description = "Map of external API secret ARNs"
  value       = { for name, secret in aws_secretsmanager_secret.external_api : name => secret.arn }
  sensitive   = true
}

output "external_api_secret_names" {
  description = "Map of external API secret names"
  value       = { for name, secret in aws_secretsmanager_secret.external_api : name => secret.name }
}

output "oauth_secret_arns" {
  description = "Map of OAuth secret ARNs"
  value       = { for name, secret in aws_secretsmanager_secret.oauth : name => secret.arn }
  sensitive   = true
}

output "oauth_secret_names" {
  description = "Map of OAuth secret names"
  value       = { for name, secret in aws_secretsmanager_secret.oauth : name => secret.name }
}

output "mtls_secret_arns" {
  description = "Map of mTLS certificate secret ARNs"
  value       = { for name, secret in aws_secretsmanager_secret.mtls : name => secret.arn }
  sensitive   = true
}

output "mtls_secret_names" {
  description = "Map of mTLS certificate secret names"
  value       = { for name, secret in aws_secretsmanager_secret.mtls : name => secret.name }
}

output "database_secret_arns" {
  description = "Map of database secret ARNs"
  value       = { for name, secret in aws_secretsmanager_secret.database : name => secret.arn }
  sensitive   = true
}

output "database_secret_names" {
  description = "Map of database secret names"
  value       = { for name, secret in aws_secretsmanager_secret.database : name => secret.name }
}

output "secret_rotation_lambda_arn" {
  description = "Lambda function ARN for secret rotation"
  value       = aws_lambda_function.secret_rotation.arn
}

output "all_secrets" {
  description = "All secret names and ARNs combined"
  value = {
    app         = { for name, secret in aws_secretsmanager_secret.app : name => secret.arn }
    external_api = { for name, secret in aws_secretsmanager_secret.external_api : name => secret.arn }
    oauth       = { for name, secret in aws_secretsmanager_secret.oauth : name => secret.arn }
    mtls        = { for name, secret in aws_secretsmanager_secret.mtls : name => secret.arn }
    database    = { for name, secret in aws_secretsmanager_secret.database : name => secret.arn }
  }
  sensitive = true
}