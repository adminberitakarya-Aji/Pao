# CI/CD Module for PAO

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "github_org" {
  type        = string
  description = "GitHub organization"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository"
}

variable "cluster_arn" {
  type        = string
  description = "EKS cluster ARN"
}

variable "cluster_endpoint" {
  type        = string
  description = "EKS cluster endpoint"
}

variable "oidc_provider_arn" {
  type        = string
  description = "OIDC provider ARN"
}

variable "cluster_certificate_authority_data" {
  type        = string
  description = "EKS cluster certificate authority data (base64 encoded)"
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}

# GitHub OIDC Provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-github-oidc"
    Environment = var.environment
  })
}

# IAM Role for GitHub Actions to deploy to EKS
resource "aws_iam_role" "github_actions_deploy" {
  name = "pao-${var.environment}-github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-github-actions-deploy"
    Environment = var.environment
  })
}

# Policy for GitHub Actions deploy role
resource "aws_iam_policy" "github_actions_deploy" {
  name = "pao-${var.environment}-github-actions-deploy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "eks:DescribeCluster",
        "eks:ListNodegroups",
        "eks:DescribeNodegroup",
        "eks:UpdateNodegroupConfig",
        "eks:DescribeUpdate",
        "iam:GetRole",
        "iam:PassRole",
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "sts:GetCallerIdentity"
      ]
      Resource = "*"
    }, {
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ]
      Resource = "arn:aws:ssm:*:${data.aws_caller_identity.current.account_id}:parameter/pao/${var.environment}/*"
    }, {
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ]
      Resource = "arn:aws:secretsmanager:*:${data.aws_caller_identity.current.account_id}:secret:pao/${var.environment}/*"
    }]
  })
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy_attachment" "github_actions_deploy" {
  role       = aws_iam_role.github_actions_deploy.name
  policy_arn = aws_iam_policy.github_actions_deploy.arn
}

# IAM Role for GitHub Actions to push to ECR
resource "aws_iam_role" "github_actions_ecr" {
  name = "pao-${var.environment}-github-actions-ecr"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-github-actions-ecr"
    Environment = var.environment
  })
}

resource "aws_iam_policy" "github_actions_ecr" {
  name = "pao-${var.environment}-github-actions-ecr"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages",
        "ecr:ListImages"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions_ecr" {
  role       = aws_iam_role.github_actions_ecr.name
  policy_arn = aws_iam_policy.github_actions_ecr.arn
}

# ECR Repositories
resource "aws_ecr_repository" "backend" {
  name                 = "pao/${var.environment}/backend"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-backend-ecr"
    Environment = var.environment
  })
}

resource "aws_ecr_repository" "ai" {
  name                 = "pao/${var.environment}/ai"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-ai-ecr"
    Environment = var.environment
  })
}

resource "aws_ecr_repository" "mobile" {
  name                 = "pao/${var.environment}/mobile"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-mobile-ecr"
    Environment = var.environment
  })
}

resource "aws_ecr_repository" "nginx" {
  name                 = "pao/${var.environment}/nginx"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.tags, {
    Name        = "pao-${var.environment}-nginx-ecr"
    Environment = var.environment
  })
}

# ECR Lifecycle Policies
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 100 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 100
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "ai" {
  repository = aws_ecr_repository.ai.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 50 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 50
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "mobile" {
  repository = aws_ecr_repository.mobile.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 100 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 100
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "nginx" {
  repository = aws_ecr_repository.nginx.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 100 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 100
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# ArgoCD Installation (via Helm)
resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
    labels = {
      "environment" = var.environment
    }
  }
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "7.0.0"
  namespace  = kubernetes_namespace.argocd.metadata[0].name

  values = [
    jsonencode({
      global = {
        domain = var.environment == "prod" ? "pao.ai" : "${var.environment}.pao.ai"
      }
      server = {
        ingress = {
          enabled = true
          ingressClassName = "nginx"
          annotations = {
            "cert-manager.io/cluster-issuer" = "letsencrypt-prod"
          }
        }
        service = {
          type = "LoadBalancer"
        }
      }
      dex = {
        enabled = true
        config = <<-EOF
          connectors:
            - type: github
              id: github
              name: GitHub
              config:
                clientID: $GITHUB_CLIENT_ID
                clientSecret: $GITHUB_CLIENT_SECRET
                orgs:
                  - name: ${var.github_org}
        EOF
      }
      repoServer = {
        env = [{
          name  = "GITHUB_TOKEN"
          valueFrom = {
            secretKeyRef = {
              name = "argocd-github-token"
              key  = "token"
            }
          }
        }]
      }
      applicationSet = {
        enabled = true
      }
      notifications = {
        enabled = true
      }
    })
  ]
}

# Kubernetes provider for ArgoCD
# Note: cluster_ca_certificate should be passed as a separate variable from EKS module output
provider "kubernetes" {
  host                   = var.cluster_endpoint
  cluster_ca_certificate = base64decode(var.cluster_certificate_authority_data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", var.environment]
  }
}

provider "helm" {
  kubernetes {
    host                   = var.cluster_endpoint
    cluster_ca_certificate = base64decode(var.cluster_certificate_authority_data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", var.environment]
    }
  }
}

# GitHub Repository Secrets (for CI/CD)
resource "github_actions_secret" "aws_role_arn_deploy" {
  repository = var.github_repo
  secret_name = "AWS_ROLE_ARN_DEPLOY"
  plaintext_value = aws_iam_role.github_actions_deploy.arn
}

resource "github_actions_secret" "aws_role_arn_ecr" {
  repository = var.github_repo
  secret_name = "AWS_ROLE_ARN_ECR"
  plaintext_value = aws_iam_role.github_actions_ecr.arn
}

resource "github_actions_secret" "ecr_registry" {
  repository = var.github_repo
  secret_name = "ECR_REGISTRY"
  plaintext_value = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
}

resource "github_actions_secret" "eks_cluster_name" {
  repository = var.github_repo
  secret_name = "EKS_CLUSTER_NAME"
  plaintext_value = "pao-${var.environment}"
}

resource "github_actions_secret" "argocd_server" {
  repository = var.github_repo
  secret_name = "ARGOCD_SERVER"
  plaintext_value = "argocd.${var.environment}.pao.ai"
}

# GitHub Environments
resource "github_branch_protection" "main" {
  repository_id = github_repository.repo.id
  pattern       = "main"
  required_status_checks = {
    strict   = true
    contexts = ["ci/lint", "ci/test", "ci/build", "ci/security"]
  }
  enforce_admins = true
  required_pull_request_reviews = {
    required_approving_review_count = 2
    dismiss_stale_reviews          = true
    require_code_owner_reviews     = true
  }
  restrictions = {
    users = []
    teams = ["platform"]
  }
}

data "github_repository" "repo" {
  full_name = "${var.github_org}/${var.github_repo}"
}

# GitHub Environments for deployment
resource "github_environment" "staging" {
  repository = var.github_repo
  environment = "staging"
  wait_timer = 0
  deployment_branch_policy {
    protected_branches = true
    custom_branch_policies = false
  }
}

resource "github_environment" "production" {
  repository = var.github_repo
  environment = "production"
  wait_timer = 5
  deployment_branch_policy {
    protected_branches = true
    custom_branch_policies = false
  }
}

# GitHub Variables for CI/CD
resource "github_actions_variable" "environment" {
  repository = var.github_repo
  variable_name = "ENVIRONMENT"
  value = var.environment
}

resource "github_actions_variable" "eks_cluster" {
  repository = var.github_repo
  variable_name = "EKS_CLUSTER_NAME"
  value = "pao-${var.environment}"
}

resource "github_actions_variable" "aws_region" {
  repository = var.github_repo
  variable_name = "AWS_REGION"
  value = "us-east-1"
}

# Outputs
output "github_actions_deploy_role_arn" {
  value = aws_iam_role.github_actions_deploy.arn
}

output "github_actions_ecr_role_arn" {
  value = aws_iam_role.github_actions_ecr.arn
}

output "ecr_repositories" {
  value = {
    backend = aws_ecr_repository.backend.repository_url
    ai      = aws_ecr_repository.ai.repository_url
    mobile  = aws_ecr_repository.mobile.repository_url
    nginx   = aws_ecr_repository.nginx.repository_url
  }
}

output "argocd_namespace" {
  value = kubernetes_namespace.argocd.metadata[0].name
}