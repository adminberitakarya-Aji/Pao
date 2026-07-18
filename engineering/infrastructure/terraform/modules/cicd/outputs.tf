# CI/CD Module Outputs

output "github_actions_deploy_role_arn" {
  description = "GitHub Actions deploy role ARN"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "github_actions_ecr_role_arn" {
  description = "GitHub Actions ECR role ARN"
  value       = aws_iam_role.github_actions_ecr.arn
}

output "oidc_provider_arn" {
  description = "GitHub OIDC provider ARN"
  value       = aws_iam_openid_connect_provider.github.arn
}

output "ecr_repository_urls" {
  description = "Map of ECR repository URLs"
  value = {
    backend = aws_ecr_repository.backend.repository_url
    ai      = aws_ecr_repository.ai.repository_url
    mobile  = aws_ecr_repository.mobile.repository_url
    nginx   = aws_ecr_repository.nginx.repository_url
  }
}

output "ecr_repository_arns" {
  description = "Map of ECR repository ARNs"
  value = {
    backend = aws_ecr_repository.backend.arn
    ai      = aws_ecr_repository.ai.arn
    mobile  = aws_ecr_repository.mobile.arn
    nginx   = aws_ecr_repository.nginx.arn
  }
}

output "argocd_namespace" {
  description = "ArgoCD namespace"
  value       = kubernetes_namespace.argocd.metadata[0].name
}

output "argocd_server_url" {
  description = "ArgoCD server URL"
  value       = "https://argocd.${var.environment}.pao.ai"
}

output "argocd_initial_admin_password" {
  description = "ArgoCD initial admin password (from secret)"
  value       = kubernetes_secret.argocd_initial_admin_secret.data[0]["admin.password"]
  sensitive   = true
}

output "github_secrets_created" {
  description = "List of GitHub secrets created"
  value = [
    "AWS_ROLE_ARN_DEPLOY",
    "AWS_ROLE_ARN_ECR",
    "ECR_REGISTRY",
    "EKS_CLUSTER_NAME",
    "ARGOCD_SERVER"
  ]
}

output "github_variables_created" {
  description = "List of GitHub variables created"
  value = [
    "ENVIRONMENT",
    "EKS_CLUSTER_NAME",
    "AWS_REGION"
  ]
}

output "github_environments_created" {
  description = "List of GitHub environments created"
  value = [
    "staging",
    "production"
  ]
}

output "branch_protection_enabled" {
  description = "Whether branch protection is enabled on main"
  value       = true
}