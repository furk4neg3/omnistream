output "project_name" {
  description = "Normalized project name used by future AWS resources."
  value       = local.normalized_project_name
}

output "environment" {
  description = "Normalized environment name used by this root."
  value       = local.normalized_environment
}

output "aws_region" {
  description = "AWS region selected for this environment."
  value       = var.aws_region
}

output "name_prefix" {
  description = "Shared name prefix for future AWS resource names."
  value       = local.name_prefix
}

output "common_tags" {
  description = "Common tags for future AWS resources."
  value       = local.common_tags
}

output "ssm_parameter_prefix" {
  description = "Future SSM Parameter Store path prefix for non-secret configuration."
  value       = local.ssm_parameter_prefix
}

output "secrets_prefix" {
  description = "Future Secrets Manager name prefix for secret configuration."
  value       = local.secrets_prefix
}

output "log_group_prefix" {
  description = "Future CloudWatch Logs prefix for ECS service log groups."
  value       = local.log_group_prefix
}

output "ecr_repository_prefix" {
  description = "Future ECR repository prefix matching the existing image namespace contract."
  value       = local.ecr_repository_prefix
}

output "service_ecr_repositories" {
  description = "Expected ECR repository names for the existing service image contract."
  value       = local.service_ecr_repositories
}

output "service_log_group_names" {
  description = "Future ECS CloudWatch log group names for the always-on service boundary."
  value = {
    processing_agent = "${local.log_group_prefix}/processing-agent"
    query_api        = "${local.log_group_prefix}/query-api"
  }
}

output "ecr_publishing_repository_names" {
  description = "ECR repository names for image publishing. When the optional module is disabled, these are expected names only."
  value       = var.enable_ecr_publishing_prereqs ? module.ecr_publishing_prereqs[0].repository_names : local.service_ecr_repositories
}

output "ecr_publishing_repository_urls" {
  description = "ECR repository URLs created by the optional publishing prerequisites module. Empty until the module is enabled and applied."
  value = var.enable_ecr_publishing_prereqs ? module.ecr_publishing_prereqs[0].repository_urls : {
    processing_agent = null
    producer         = null
    query_api        = null
  }
}

output "ecr_publishing_repository_arns" {
  description = "ECR repository ARNs created by the optional publishing prerequisites module. Empty until the module is enabled and applied."
  value = var.enable_ecr_publishing_prereqs ? module.ecr_publishing_prereqs[0].repository_arns : {
    processing_agent = null
    producer         = null
    query_api        = null
  }
}

output "ecr_publishing_role_arn" {
  description = "GitHub Actions publish role ARN created by the optional publishing prerequisites module. Null until enabled and applied."
  value       = var.enable_ecr_publishing_prereqs ? module.ecr_publishing_prereqs[0].publish_role_arn : null
}
