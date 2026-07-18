# Databases Module Outputs

output "postgres_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "postgres_endpoint_address" {
  description = "PostgreSQL endpoint address"
  value       = aws_db_instance.postgres.address
}

output "postgres_endpoint_port" {
  description = "PostgreSQL endpoint port"
  value       = aws_db_instance.postgres.port
}

output "postgres_arn" {
  description = "PostgreSQL instance ARN"
  value       = aws_db_instance.postgres.arn
}

output "postgres_security_group_id" {
  description = "PostgreSQL security group ID"
  value       = aws_security_group.postgres.id
}

output "postgres_parameter_group_name" {
  description = "PostgreSQL parameter group name"
  value       = aws_db_parameter_group.postgres.name
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_arn" {
  description = "ElastiCache replication group ARN"
  value       = aws_elasticache_replication_group.redis.arn
}

output "redis_security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}

output "redis_parameter_group_name" {
  description = "Redis parameter group name"
  value       = aws_elasticache_parameter_group.redis.name
}

output "qdrant_security_group_id" {
  description = "Qdrant security group ID"
  value       = aws_security_group.qdrant.id
}

output "clickhouse_security_group_id" {
  description = "ClickHouse security group ID"
  value       = aws_security_group.clickhouse.id
}

output "redpanda_security_group_id" {
  description = "Redpanda security group ID"
  value       = aws_security_group.redpanda.id
}

output "database_subnet_group_name" {
  description = "Database subnet group name"
  value       = aws_db_subnet_group.main.name
}

output "endpoints" {
  description = "All database endpoints"
  value = {
    postgres = {
      host = aws_db_instance.postgres.address
      port = aws_db_instance.postgres.port
    }
    redis = {
      host = aws_elasticache_replication_group.redis.primary_endpoint_address
      port = aws_elasticache_replication_group.redis.port
    }
  }
  sensitive = true
}