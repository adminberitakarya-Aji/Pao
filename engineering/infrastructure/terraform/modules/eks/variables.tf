# EKS Module Variables

variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster"
}

variable "region" {
  type        = string
  description = "AWS region"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the cluster"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for EKS nodes"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for ALB/ingress"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version"
  default     = "1.28"
}

variable "cluster_endpoint_public_access" {
  type        = bool
  description = "Enable public access to cluster endpoint"
  default     = true
}

variable "cluster_endpoint_private_access" {
  type        = bool
  description = "Enable private access to cluster endpoint"
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed for public endpoint access"
  default     = ["0.0.0.0/0"]
}

variable "enable_irsa" {
  type        = bool
  description = "Enable IAM Roles for Service Accounts"
  default     = true
}

variable "node_groups" {
  description = "Map of node group configurations"
  type = map(object({
    name                    = string
    instance_types          = list(string)
    capacity_type           = string
    min_size                = number
    max_size                = number
    desired_size            = number
    disk_size               = number
    ami_type                = string
    labels                  = map(string)
    taints                  = list(object({ key = string, value = string, effect = string }))
    subnets                 = list(string)
    enable_detailed_monitoring = bool
    tags                    = map(string)
  }))
}

variable "addons" {
  description = "EKS addons to install"
  type = map(object({
    version     = optional(string)
    configuration = optional(string)
    resolve_conflicts = optional(string)
  }))
  default = {
    "vpc-cni" = {}
    "coredns" = {}
    "kube-proxy" = {}
    "aws-ebs-csi-driver" = {}
    "snapshot-controller" = {}
  }
}

variable "enable_cluster_autoscaler" {
  type        = bool
  description = "Enable Cluster Autoscaler"
  default     = true
}

variable "enable_metrics_server" {
  type        = bool
  description = "Enable Metrics Server"
  default     = true
}

variable "encryption_config" {
  description = "Encryption config for secrets"
  type = list(object({
    provider_key_arn = string
    resources        = list(string)
  }))
  default = []
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}