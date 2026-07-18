# Databases Module Variables

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for database subnets"
}

variable "region" {
  type        = string
  description = "AWS region"
}

variable "postgres_config" {
  type = object({
    instance_class         = string
    allocated_storage      = number
    max_allocated_storage  = number
    engine_version         = string
    multi_az               = bool
    backup_retention       = number
    publicly_accessible    = bool
    deletion_protection    = bool
    storage_encrypted      = bool
    kms_key_id             = string
    parameter_group_name   = string
    maintenance_window     = string
    backup_window          = string
  })
  description = "PostgreSQL configuration"
  default = {
    instance_class         = "db.r6g.large"
    allocated_storage      = 100
    max_allocated_storage  = 500
    engine_version         = "16.3"
    multi_az               = true
    backup_retention       = 30
    publicly_accessible    = false
    deletion_protection    = true
    storage_encrypted      = true
    kms_key_id             = ""
    parameter_group_name   = ""
    maintenance_window     = "mon:03:00-mon:04:00"
    backup_window          = "03:00-04:00"
  }
}

variable "redis_config" {
  type = object({
    node_type             = string
    num_cache_nodes       = number
    engine_version        = string
    automatic_failover    = bool
    multi_az              = bool
    at_rest_encryption    = bool
    transit_encryption    = bool
    auth_token            = string
    parameter_group_name  = string
    maintenance_window    = string
    snapshot_retention    = number
    snapshot_window       = string
  })
  description = "ElastiCache Redis configuration"
  default = {
    node_type             = "cache.r7g.large"
    num_cache_nodes       = 2
    engine_version        = "7.1"
    automatic_failover    = true
    multi_az              = true
    at_rest_encryption    = true
    transit_encryption    = true
    auth_token            = ""
    parameter_group_name  = ""
    maintenance_window    = "tue:04:00-tue:05:00"
    snapshot_retention    = 7
    snapshot_window       = "04:00-05:00"
  }
}

variable "enable_qdrant" {
  type        = bool
  description = "Enable Qdrant vector database security group"
  default     = true
}

variable "enable_clickhouse" {
  type        = bool
  description = "Enable ClickHouse analytics database security group"
  default     = true
}

variable "enable_redpanda" {
  type        = bool
  description = "Enable Redpanda streaming security group"
  default     = true
}

variable "enable_documentdb" {
  type        = bool
  description = "Enable DocumentDB (MongoDB compatible)"
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}