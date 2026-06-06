locals {
  normalized_project_name = lower(replace(var.project_name, "_", "-"))
  normalized_environment  = lower(var.environment)
  normalized_owner        = trimspace(var.owner)
  normalized_cost_center  = trimspace(var.cost_center)
  normalized_image_namespace = lower(
    trim(var.image_namespace, "/")
  )

  name_prefix = "${local.normalized_project_name}-${local.normalized_environment}"

  base_tags = {
    Application = local.normalized_project_name
    Environment = local.normalized_environment
    ManagedBy   = "terraform"
    Owner       = local.normalized_owner
    Project     = local.normalized_project_name
  }

  cost_center_tags = local.normalized_cost_center != "" ? {
    CostCenter = local.normalized_cost_center
  } : {}

  common_tags = merge(
    local.base_tags,
    local.cost_center_tags,
    var.additional_tags,
  )

  ssm_parameter_prefix  = "/${local.normalized_project_name}/${local.normalized_environment}"
  secrets_prefix        = "${local.normalized_project_name}/${local.normalized_environment}"
  log_group_prefix      = "/aws/ecs/${local.name_prefix}"
  ecr_repository_prefix = local.normalized_image_namespace
}
