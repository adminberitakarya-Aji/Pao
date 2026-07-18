# CI/CD Module Variables

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "github_org" {
  type        = string
  description = "GitHub organization name"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
}

variable "cluster_arn" {
  type        = string
  description = "EKS cluster ARN"
}

variable "cluster_endpoint" {
  type        = string
  description = "EKS cluster endpoint"
}

variable "cluster_certificate_authority_data" {
  type        = string
  description = "EKS cluster certificate authority data (base64 encoded)"
}

variable "oidc_provider_arn" {
  type        = string
  description = "OIDC provider ARN for IRSA"
}

variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "ecr_repositories" {
  type = list(object({
    name                 = string
    image_tag_mutability = string
    scan_on_push         = bool
    lifecycle_policy     = map(string)
  }))
  default = [
    {
      name                 = "backend"
      image_tag_mutability = "MUTABLE"
      scan_on_push         = true
      lifecycle_policy     = { max_images = "100" }
    },
    {
      name                 = "ai"
      image_tag_mutability = "MUTABLE"
      scan_on_push         = true
      lifecycle_policy     = { max_images = "50" }
    },
    {
      name                 = "mobile"
      image_tag_mutability = "MUTABLE"
      scan_on_push         = true
      lifecycle_policy     = { max_images = "100" }
    },
    {
      name                 = "nginx"
      image_tag_mutability = "MUTABLE"
      scan_on_push         = true
      lifecycle_policy     = { max_images = "100" }
    }
  ]
}

variable "argocd_version" {
  type        = string
  description = "ArgoCD Helm chart version"
  default     = "7.0.0"
}

variable "argocd_domain" {
  type        = string
  description = "ArgoCD domain name"
  default     = "argocd"
}

variable "enable_argocd" {
  type        = bool
  description = "Enable ArgoCD installation"
  default     = true
}

variable "github_client_id" {
  type        = string
  description = "GitHub OAuth Client ID for ArgoCD Dex"
  default     = ""
}

variable "github_client_secret" {
  type        = string
  description = "GitHub OAuth Client Secret for ArgoCD Dex"
  sensitive   = true
  default     = ""
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}