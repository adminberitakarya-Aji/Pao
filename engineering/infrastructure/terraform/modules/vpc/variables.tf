# VPC Module Variables

variable "name" {
  type        = string
  description = "Name prefix for VPC resources"
}

variable "cidr_block" {
  type        = string
  description = "CIDR block for the VPC"
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
  description = "List of availability zones"
  default     = []
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets"
  default     = []
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets"
  default     = []
}

variable "database_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for database subnets"
  default     = []
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Enable NAT Gateway for private subnet internet access"
  default     = true
}

variable "single_nat_gateway" {
  type        = bool
  description = "Use single NAT Gateway (cost savings for dev/staging)"
  default     = false
}

variable "enable_dns_hostnames" {
  type        = bool
  description = "Enable DNS hostnames in VPC"
  default     = true
}

variable "enable_dns_support" {
  type        = bool
  description = "Enable DNS support in VPC"
  default     = true
}

variable "enable_classiclink" {
  type        = bool
  description = "Enable ClassicLink for EC2-Classic"
  default     = false
}

variable "enable_vpc_endpoints" {
  type        = bool
  description = "Enable VPC endpoints for AWS services"
  default     = true
}

variable "vpc_endpoints" {
  type        = list(string)
  description = "List of VPC endpoints to create"
  default     = ["s3", "dynamodb", "ecr.api", "ecr.dkr", "logs", "monitoring", "sts", "secretsmanager", "kms", "ssm", "ssmmessages", "ec2messages"]
}

variable "flow_log_destination" {
  type        = string
  description = "CloudWatch Log Group ARN or S3 bucket ARN for VPC flow logs"
  default     = ""
}

variable "enable_flow_logs" {
  type        = bool
  description = "Enable VPC flow logs"
  default     = true
}

variable "flow_log_traffic_type" {
  type        = string
  description = "Type of traffic to log (ALL, ACCEPT, REJECT)"
  default     = "ALL"
}

variable "tags" {
  type        = map(string)
  description = "Additional tags for VPC resources"
  default     = {}
}