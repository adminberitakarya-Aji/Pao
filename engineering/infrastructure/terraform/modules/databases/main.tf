# Databases Module for PAO

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

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs"
}

variable "region" {
  type        = string
  description = "AWS region"
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.r6g.xlarge"
}

variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage in GB"
  default     = 100
}

variable "db_max_allocated_storage" {
  type        = number
  description = "Max allocated storage for autoscaling"
  default     = 500
}

variable "redis_node_type" {
  type        = string
  description = "ElastiCache node type"
  default     = "cache.r6g.xlarge"
}

variable "redis_num_cache_nodes" {
  type        = number
  description = "Number of cache nodes"
  default     = 2
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "random_password" "redis_auth_token" {
  length  = 32
  special = false
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "pao-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-db-subnet-group"
    Environment = var.environment
  })
}

# RDS PostgreSQL with pgvector
resource "aws_db_instance" "postgres" {
  identifier        = "pao-${var.environment}-postgres"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted = true
  storage_type      = "gp3"

  db_name  = "pao"
  username = "paoadmin"
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment != "prod"
  deletion_protection   = var.environment == "prod"

  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn         = aws_iam_role.rds_monitoring.arn

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  parameter_group_name = aws_db_parameter_group.pgvector.name

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-postgres"
    Environment = var.environment
  })
}

# Parameter group for pgvector
resource "aws_db_parameter_group" "pgvector" {
  family = "postgres16"
  name   = "pao-${var.environment}-pgvector"

  parameter {
    name  = "shared_preload_libraries"
    value = "vector,pg_stat_statements"
  }

  parameter {
    name  = "max_connections"
    value = "500"
  }

  parameter {
    name  = "shared_buffers"
    value = "256MB"
  }

  parameter {
    name  = "effective_cache_size"
    value = "768MB"
  }

  parameter {
    name  = "work_mem"
    value = "16MB"
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "256MB"
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-pgvector"
    Environment = var.environment
  })
}

# Security group for RDS
resource "aws_security_group" "rds" {
  name        = "pao-${var.environment}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-rds-sg"
    Environment = var.environment
  })
}

# Reference to EKS node security group (passed via data source or variable)
data "aws_security_group" "eks_nodes" {
  filter {
    name   = "group-name"
    values = ["*node-group-sg*"]
  }
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "pao-${var.environment}-redis"
  replication_group_description = "PAO Redis cluster for ${var.environment}"

  engine               = "redis"
  engine_version       = "7.2"
  node_type            = var.redis_node_type
  number_cache_clusters = var.redis_num_cache_nodes
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.redis.name

  automatic_failover_enabled = true
  multi_az_enabled           = true

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token.result

  subnet_group_name = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  snapshot_retention_limit = var.environment == "prod" ? 7 : 1
  snapshot_window          = "05:00-06:00"

  maintenance_window = "sun:06:00-sun:07:00"

  log_delivery_configuration {
    destination_type = "cloudwatch-logs"
    log_type         = "slow-log"
    log_format       = "json"
    destination_details {
      cloudwatch_logs {
        log_group = aws_cloudwatch_log_group.redis_slow.name
      }
    }
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redis"
    Environment = var.environment
  })
}

resource "aws_elasticache_parameter_group" "redis" {
  name   = "pao-${var.environment}-redis"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redis-param-group"
    Environment = var.environment
  })
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "pao-${var.environment}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redis-subnet-group"
    Environment = var.environment
  })
}

resource "aws_security_group" "redis" {
  name        = "pao-${var.environment}-redis-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redis-sg"
    Environment = var.environment
  })
}

resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/pao-${var.environment}/redis-slow"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redis-slow-logs"
    Environment = var.environment
  })
}

# Qdrant Vector Database (self-managed on EC2 for now, can be migrated to managed)
resource "aws_security_group" "qdrant" {
  name        = "pao-${var.environment}-qdrant-sg"
  description = "Security group for Qdrant"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6333
    to_port         = 6333
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  ingress {
    from_port       = 6334
    to_port         = 6334
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-qdrant-sg"
    Environment = var.environment
  })
}

# ClickHouse for Analytics (self-managed)
resource "aws_security_group" "clickhouse" {
  name        = "pao-${var.environment}-clickhouse-sg"
  description = "Security group for ClickHouse"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8123
    to_port         = 8123
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  ingress {
    from_port       = 9000
    to_port         = 9000
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-clickhouse-sg"
    Environment = var.environment
  })
}

# Redpanda/Kafka
resource "aws_security_group" "redpanda" {
  name        = "pao-${var.environment}-redpanda-sg"
  description = "Security group for Redpanda/Kafka"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  ingress {
    from_port       = 9644
    to_port         = 9644
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redpanda-sg"
    Environment = var.environment
  })
}

# IAM Role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "pao-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Secrets Manager for database credentials
resource "aws_secretsmanager_secret" "postgres" {
  name = "pao/${var.environment}/postgres/credentials"

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-postgres-credentials"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "postgres" {
  secret_id = aws_secretsmanager_secret.postgres.id
  secret_string = jsonencode({
    username = "paoadmin"
    password = random_password.db_password.result
    host     = aws_db_instance.postgres.endpoint
    port     = 5432
    database = "pao"
  })
}

resource "aws_secretsmanager_secret" "redis" {
  name = "pao/${var.environment}/redis/credentials"

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-redis-credentials"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    host = aws_elasticache_replication_group.redis.primary_endpoint_address
    port = 6379
    auth_token = random_password.redis_auth_token.result
  })
}

# Outputs
output "postgres_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "postgres_host" {
  value = aws_db_instance.postgres.address
}

output "postgres_port" {
  value = aws_db_instance.postgres.port
}

output "postgres_database" {
  value = "pao"
}

output "postgres_credentials_secret_arn" {
  value = aws_secretsmanager_secret.postgres.arn
}

output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  value = 6379
}

output "redis_credentials_secret_arn" {
  value = aws_secretsmanager_secret.redis.arn
}

output "qdrant_security_group_id" {
  value = aws_security_group.qdrant.id
}

output "clickhouse_security_group_id" {
  value = aws_security_group.clickhouse.id
}

output "redpanda_security_group_id" {
  value = aws_security_group.redpanda.id
}