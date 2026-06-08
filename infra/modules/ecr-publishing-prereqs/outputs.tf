output "repository_names" {
  description = "ECR repository names keyed by OmniStream service."
  value = {
    for service, repository in aws_ecr_repository.service :
    service => repository.name
  }
}

output "repository_urls" {
  description = "ECR repository URLs keyed by OmniStream service."
  value = {
    for service, repository in aws_ecr_repository.service :
    service => repository.repository_url
  }
}

output "repository_arns" {
  description = "ECR repository ARNs keyed by OmniStream service."
  value = {
    for service, repository in aws_ecr_repository.service :
    service => repository.arn
  }
}

output "publish_role_arn" {
  description = "IAM role ARN to configure as the GitHub repository variable AWS_ROLE_TO_ASSUME."
  value       = aws_iam_role.publish_images.arn
}

output "github_oidc_provider_arn" {
  description = "GitHub Actions OIDC provider ARN created by this module."
  value       = aws_iam_openid_connect_provider.github_actions.arn
}
