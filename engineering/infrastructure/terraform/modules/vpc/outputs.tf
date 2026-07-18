# VPC Module Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_arn" {
  description = "VPC ARN"
  value       = aws_vpc.main.arn
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "public_subnet_arns" {
  description = "List of public subnet ARNs"
  value       = aws_subnet.public[*].arn
}

output "public_subnet_cidr_blocks" {
  description = "List of public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "private_subnet_arns" {
  description = "List of private subnet ARNs"
  value       = aws_subnet.private[*].arn
}

output "private_subnet_cidr_blocks" {
  description = "List of private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

output "database_subnet_ids" {
  description = "List of database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "database_subnet_arns" {
  description = "List of database subnet ARNs"
  value       = aws_subnet.database[*].arn
}

output "database_subnet_cidr_blocks" {
  description = "List of database subnet CIDR blocks"
  value       = aws_subnet.database[*].cidr_block
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "List of NAT Gateway public IPs"
  value       = aws_nat_gateway.main[*].public_ip
}

output "nat_gateway_private_ips" {
  description = "List of NAT Gateway private IPs"
  value       = aws_nat_gateway.main[*].private_ip
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = aws_internet_gateway.main.id
}

output "vpc_endpoint_ids" {
  description = "Map of VPC endpoint IDs by service name"
  value       = { for ep in aws_vpc_endpoint.main : ep.service_name => ep.id }
}

output "vpc_endpoint_dns_entries" {
  description = "Map of VPC endpoint DNS entries by service name"
  value       = { for ep in aws_vpc_endpoint.main : ep.service_name => ep.dns_entry[0].dns_name }
}

output "security_group_ids" {
  description = "Map of security group IDs by name"
  value = {
    default       = aws_security_group.default.id
    alb           = aws_security_group.alb.id
    eks_cluster   = aws_security_group.eks_cluster.id
    eks_nodegroup = aws_security_group.eks_nodegroup.id
    rds           = aws_security_group.rds.id
    elasticache   = aws_security_group.elasticache.id
    qdrant        = aws_security_group.qdrant.id
    clickhouse    = aws_security_group.clickhouse.id
    redpanda      = aws_security_group.redpanda.id
  }
}

output "route_table_ids" {
  description = "Map of route table IDs by type"
  value = {
    public  = aws_route_table.public[*].id
    private = aws_route_table.private[*].id
    database = aws_route_table.database[*].id
  }
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = data.aws_availability_zones.available.names
}

output "region" {
  description = "AWS region"
  value       = var.region
}