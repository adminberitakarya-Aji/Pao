# EKS Module for PAO

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

variable "name" {
  type        = string
  description = "Name prefix for EKS resources"
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

variable "cluster_version" {
  type        = string
  description = "EKS cluster version"
  default     = "1.28"
}

variable "instance_types" {
  type        = list(string)
  description = "EC2 instance types for node groups"
  default     = ["m6i.xlarge", "m6i.2xlarge"]
}

variable "node_group_min_size" {
  type        = number
  description = "Minimum node group size"
  default     = 2
}

variable "node_group_max_size" {
  type        = number
  description = "Maximum node group size"
  default     = 20
}

variable "node_group_desired_size" {
  type        = number
  description = "Desired node group size"
  default     = 3
}

variable "enable_irsa" {
  type        = bool
  description = "Enable IAM Roles for Service Accounts"
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}

# IAM Role for EKS Cluster
resource "aws_iam_role" "cluster" {
  name = "${var.name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(var.tags, {
    Name        = "${var.name}-cluster-role"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSVPCResourceController" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.cluster.name
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = var.name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  tags = merge(var.tags, {
    Name        = var.name
    Environment = var.environment
  })

  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.cluster_AmazonEKSVPCResourceController,
  ]
}

# KMS Key for EKS secrets encryption
resource "aws_kms_key" "eks" {
  description             = "KMS key for EKS secrets encryption"
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
      Sid    = "Allow EKS to use the key"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
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
    Name        = "${var.name}-eks-kms"
    Environment = var.environment
  })
}

data "aws_caller_identity" "current" {}

# IAM Role for Node Groups
resource "aws_iam_role" "node_group" {
  name = "${var.name}-node-group-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(var.tags, {
    Name        = "${var.name}-node-group-role"
    Environment = var.environment
  })
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = aws_iam_role.node_group.name
}

# Additional policy for node group to access other AWS services
resource "aws_iam_policy" "node_group_additional" {
  name = "${var.name}-node-group-additional"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sns:Publish",
        "events:PutEvents"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "node_group_additional" {
  policy_arn = aws_iam_policy.node_group_additional.arn
  role       = aws_iam_role.node_group.name
}

# Security Group for EKS Cluster
resource "aws_security_group" "cluster" {
  name        = "${var.name}-cluster-sg"
  description = "Security group for EKS cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-cluster-sg"
    Environment = var.environment
  })
}

# Security Group for Node Groups
resource "aws_security_group" "node_group" {
  name        = "${var.name}-node-group-sg"
  description = "Security group for EKS node groups"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 1025
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.cluster.id]
  }

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.cluster.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-node-group-sg"
    Environment = var.environment
  })
}

# EKS Node Group - General Purpose
resource "aws_eks_node_group" "general" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.name}-general"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = var.instance_types
  capacity_type   = "ON_DEMAND"

  scaling_config {
    desired_size = var.node_group_desired_size
    max_size     = var.node_group_max_size
    min_size     = var.node_group_min_size
  }

  update_config {
    max_unavailable_percentage = 25
  }

  labels = {
    "node-type" = "general"
  }

  taints {
    key    = "dedicated"
    value  = "general"
    effect = "NO_SCHEDULE"
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-general"
    Environment = var.environment
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.node_group_CloudWatchAgentServerPolicy,
    aws_iam_role_policy_attachment.node_group_additional,
  ]
}

# EKS Node Group - AI/ML Workloads (GPU)
resource "aws_eks_node_group" "ai_ml" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.name}-ai-ml"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = ["g5.xlarge", "g5.2xlarge"]
  capacity_type   = "SPOT"

  scaling_config {
    desired_size = 0
    max_size     = 10
    min_size     = 0
  }

  update_config {
    max_unavailable_percentage = 50
  }

  labels = {
    "node-type"      = "ai-ml"
    "workload-type"  = "gpu"
  }

  taints {
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-ai-ml"
    Environment = var.environment
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.node_group_CloudWatchAgentServerPolicy,
    aws_iam_role_policy_attachment.node_group_additional,
  ]
}

# EKS Node Group - Memory Intensive
resource "aws_eks_node_group" "memory" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.name}-memory"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids
  instance_types  = ["r6i.xlarge", "r6i.2xlarge", "r6i.4xlarge"]
  capacity_type   = "ON_DEMAND"

  scaling_config {
    desired_size = 1
    max_size     = 10
    min_size     = 1
  }

  update_config {
    max_unavailable_percentage = 25
  }

  labels = {
    "node-type"      = "memory"
    "workload-type"  = "memory-intensive"
  }

  taints {
    key    = "dedicated"
    value  = "memory"
    effect = "NO_SCHEDULE"
  }

  tags = merge(var.tags, {
    Name        = "${var.name}-memory"
    Environment = var.environment
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
    aws_iam_role_policy_attachment.node_group_CloudWatchAgentServerPolicy,
    aws_iam_role_policy_attachment.node_group_additional,
  ]
}

# IAM Role for IRSA (IAM Roles for Service Accounts)
resource "aws_iam_openid_connect_provider" "eks" {
  count = var.enable_irsa ? 1 : 0

  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["9e99a48a9960b14926bb7f3b02e22da2b0ab7280"]
  url             = aws_eks_cluster.main.identity[0].oidc.issuer_url

  tags = merge(var.tags, {
    Name        = "${var.name}-oidc-provider"
    Environment = var.environment
  })
}

# Kubernetes Provider Configuration
provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", aws_eks_cluster.main.name]
  }
}

provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", aws_eks_cluster.main.name]
    }
  }
}

# Essential Cluster Add-ons
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
  addon_version = "v1.14.1-eksbuild.1"
  resolve_conflicts = "OVERWRITE"

  configuration_values = jsonencode({
    enableNetworkPolicy = true
    enablePodENI       = true
  })
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"
  addon_version = "v1.10.1-eksbuild.4"
  resolve_conflicts = "OVERWRITE"
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"
  addon_version = "v1.28.2-eksbuild.1"
  resolve_conflicts = "OVERWRITE"
}

resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "aws-ebs-csi-driver"
  addon_version = "v1.24.0-eksbuild.1"
  resolve_conflicts = "OVERWRITE"

  service_account_role_arn = aws_iam_role.ebs_csi_driver.arn
}

# IAM Role for EBS CSI Driver (IRSA)
resource "aws_iam_role" "ebs_csi_driver" {
  name = "${var.name}-ebs-csi-driver"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks[0].arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.eks[0].url, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "ebs_csi_driver" {
  name = "${var.name}-ebs-csi-driver"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:AttachVolume",
        "ec2:CreateSnapshot",
        "ec2:CreateTags",
        "ec2:CreateVolume",
        "ec2:DeleteSnapshot",
        "ec2:DeleteTags",
        "ec2:DeleteVolume",
        "ec2:DescribeInstances",
        "ec2:DescribeSnapshots",
        "ec2:DescribeTags",
        "ec2:DescribeVolumes",
        "ec2:DetachVolume",
        "ec2:ModifyVolume"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  policy_arn = aws_iam_policy.ebs_csi_driver.arn
  role       = aws_iam_role.ebs_csi_driver.name
}

# CloudWatch Observability Add-on
resource "aws_eks_addon" "cloudwatch_observability" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "amazon-cloudwatch-observability"
  addon_version = "v1.0.0-eksbuild.1"
  resolve_conflicts = "OVERWRITE"
}

# Outputs
output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cluster_arn" {
  value = aws_eks_cluster.main.arn
}

output "cluster_certificate_authority_data" {
  value = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_oidc_issuer_url" {
  value = aws_eks_cluster.main.identity[0].oidc.issuer_url
}

output "cluster_oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks[0].arn
}

output "node_group_role_arn" {
  value = aws_iam_role.node_group.arn
}

output "general_node_group_name" {
  value = aws_eks_node_group.general.node_group_name
}

output "ai_ml_node_group_name" {
  value = aws_eks_node_group.ai_ml.node_group_name
}

output "memory_node_group_name" {
  value = aws_eks_node_group.memory.node_group_name
}