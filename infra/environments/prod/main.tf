module "ecr_publishing_prereqs" {
  count = var.enable_ecr_publishing_prereqs ? 1 : 0

  source = "../../modules/ecr-publishing-prereqs"

  name_prefix                     = local.name_prefix
  image_namespace                 = local.ecr_repository_prefix
  github_actions_repository_owner = var.github_actions_repository_owner
  github_actions_repository_name  = var.github_actions_repository_name
  github_actions_ref_patterns     = var.github_actions_ref_patterns
  github_oidc_thumbprint_list     = var.github_oidc_thumbprint_list
  publish_role_name               = var.github_actions_publish_role_name
  scan_on_push                    = var.ecr_scan_on_push
  encryption_type                 = var.ecr_encryption_type
  kms_key_arn                     = var.ecr_kms_key_arn
  tags                            = local.common_tags
}
