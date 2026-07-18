# EKS Module Outputs

output "cluster_id" {
  description = "EKS Cluster ID"
  value       = aws_eks_cluster.main.id
}

output "cluster_arn" {
  description = "EKS Cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "EKS Cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate authority data"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "cluster_security_group_id" {
  description = "Cluster security group ID"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "cluster_version" {
  description = "Kubernetes version"
  value       = aws_eks_cluster.main.version
}

output "cluster_oidc_provider_arn" {
  description = "OIDC Provider ARN for IRSA"
  value       = aws_iam_openid_connect_provider.oidc.arn
}

output "cluster_oidc_provider_url" {
  description = "OIDC Provider URL"
  value       = aws_iam_openid_connect_provider.oidc.url
}

output "node_group_arns" {
  description = "Map of node group ARNs"
  value       = { for ng in aws_eks_node_group.main : ng.name => ng.arn }
}

output "node_group_autoscaling_group_names" {
  description = "Map of node group ASG names"
  value       = { for ng in aws_eks_node_group.main : ng.name => ng.autoscaling_group_names[0] }
}

output "kubeconfig" {
  description = "Kubeconfig for cluster access"
  value       = data.aws_eks_cluster_auth.main.token
  sensitive   = true
}

output "addon_versions" {
  description = "Map of addon versions"
  value       = { for addon in aws_eks_addon.main : addon.addon_name => addon.addon_version }
}

output "role_arn" {
  description = "EKS Cluster IAM Role ARN"
  value       = aws_iam_role.cluster.arn
}

output "node_role_arn" {
  description = "EKS Node Group IAM Role ARN"
  value       = aws_iam_role.node_group.arn
}

output "oidc_provider_arn" {
  description = "OIDC Provider ARN"
  value       = aws_iam_openid_connect_provider.oidc.arn
}