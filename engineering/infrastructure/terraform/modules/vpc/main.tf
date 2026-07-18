# VPC Module for PAO

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "name" {
  type        = string
  description = "Name prefix for VPC resources"
}

variable "cidr_block" {
  type        = string
  description = "CIDR block for VPC"
}

variable "region" {
  type        = string
  description = "AWS region"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones"
  default     = []
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = var.name
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.name}-igw"
    Environment = var.environment
  }
}

# Public subnets
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones) > 0 ? length(var.availability_zones) : 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.cidr_block, 4, count.index)
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.name}-public-${count.index}"
    Environment = var.environment
    Type        = "public"
  }
}

# Private subnets
resource "aws_subnet" "private" {
  count             = length(var.availability_zones) > 0 ? length(var.availability_zones) : 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 4, count.index + 10)
  availability_zone = var.availability_zones[count.index % length(var.availability_zones)]

  tags = {
    Name        = "${var.name}-private-${count.index}"
    Environment = var.environment
    Type        = "private"
  }
}

# Database subnets (for RDS)
resource "aws_subnet" "database" {
  count             = length(var.availability_zones) > 0 ? length(var.availability_zones) : 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 4, count.index + 20)
  availability_zone = var.availability_zones[count.index % length(var.availability_zones)]

  tags = {
    Name        = "${var.name}-database-${count.index}"
    Environment = var.environment
    Type        = "database"
  }
}

# NAT Gateways (one per AZ for HA)
resource "aws_eip" "nat" {
  count  = length(var.availability_zones) > 0 ? length(var.availability_zones) : 3
  domain = "vpc"

  tags = {
    Name        = "${var.name}-nat-eip-${count.index}"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones) > 0 ? length(var.availability_zones) : 3
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "${var.name}-nat-${count.index}"
    Environment = var.environment
  }
}

# Route tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.name}-public-rt"
    Environment = var.environment
  }
}

resource "aws_route_table" "private" {
  count  = length(var.availability_zones) > 0 ? length(var.availability_zones) : 3
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name        = "${var.name}-private-rt-${count.index}"
    Environment = var.environment
  }
}

# Route table associations
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Database subnet group
resource "aws_db_subnet_group" "main" {
  name       = "${var.name}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id

  tags = {
    Name        = "${var.name}-db-subnet-group"
    Environment = var.environment
  }
}

# VPC Flow Logs
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name        = "${var.name}-flow-logs"
    Environment = var.environment
  }
}

resource "aws_iam_role" "flow_logs" {
  name = "${var.name}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  name = "${var.name}-flow-logs-policy"
  role = aws_iam_role.flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}

resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/aws/vpc/${var.name}/flowlogs"
  retention_in_days = 30

  tags = {
    Name        = "${var.name}-flow-logs"
    Environment = var.environment
  }
}

# VPC Endpoints for private access to AWS services
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id] + aws_route_table.private[*].id

  tags = {
    Name        = "${var.name}-s3-endpoint"
    Environment = var.environment
  }
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  tags = {
    Name        = "${var.name}-ecr-api-endpoint"
    Environment = var.environment
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  tags = {
    Name        = "${var.name}-ecr-dkr-endpoint"
    Environment = var.environment
  }
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  tags = {
    Name        = "${var.name}-logs-endpoint"
    Environment = var.environment
  }
}

resource "aws_vpc_endpoint" "sts" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.sts"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoints.id]

  tags = {
    Name        = "${var.name}-sts-endpoint"
    Environment = var.environment
  }
}

resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.name}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.name}-vpc-endpoints-sg"
    Environment = var.environment
  }
}

# Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "vpc_cidr_block" {
  value = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "database_subnet_ids" {
  value = aws_subnet.database[*].id
}

output "db_subnet_group_name" {
  value = aws_db_subnet_group.main.name
}

output "nat_gateway_ids" {
  value = aws_nat_gateway.main[*].id
}

output "availability_zones" {
  value = aws_subnet.public[*].availability_zone
}