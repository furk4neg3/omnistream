variable "name_prefix" {
  description = "Environment-scoped name prefix used for IAM role and policy names."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9_-]*$", var.name_prefix))
    error_message = "name_prefix must contain only letters, numbers, hyphens, and underscores, and must start with a letter or number."
  }
}

variable "image_namespace" {
  description = "ECR repository namespace matching OMNISTREAM_IMAGE_NAMESPACE from the existing image contract."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]+([._/-][a-z0-9]+)*$", var.image_namespace)) && !endswith(var.image_namespace, "/")
    error_message = "image_namespace must be lowercase and contain only letters, numbers, dots, underscores, hyphens, and slashes, without a trailing slash."
  }
}

variable "tags" {
  description = "Common tags to apply to resources created by this module."
  type        = map(string)
  default     = {}
}

variable "github_actions_repository_owner" {
  description = "GitHub organization or user that owns the repository allowed to assume the publish role."
  type        = string

  validation {
    condition     = length(trimspace(var.github_actions_repository_owner)) > 0
    error_message = "github_actions_repository_owner must not be empty when this module is enabled."
  }
}

variable "github_actions_repository_name" {
  description = "GitHub repository name allowed to assume the publish role."
  type        = string

  validation {
    condition     = length(trimspace(var.github_actions_repository_name)) > 0
    error_message = "github_actions_repository_name must not be empty when this module is enabled."
  }
}

variable "github_actions_ref_patterns" {
  description = "GitHub OIDC sub-claim ref patterns allowed to assume the publish role, such as ref:refs/heads/main."
  type        = list(string)
  default     = ["ref:refs/heads/main"]

  validation {
    condition     = length(var.github_actions_ref_patterns) > 0
    error_message = "github_actions_ref_patterns must include at least one allowed ref pattern."
  }
}

variable "github_oidc_thumbprint_list" {
  description = "Thumbprints for the GitHub Actions OIDC provider. Verify these against GitHub/AWS guidance before applying in a real account."
  type        = list(string)
  default     = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  validation {
    condition = alltrue([
      for thumbprint in var.github_oidc_thumbprint_list :
      can(regex("^[0-9a-fA-F]{40}$", thumbprint))
    ])
    error_message = "github_oidc_thumbprint_list values must be 40-character SHA-1 thumbprints."
  }
}

variable "publish_role_name" {
  description = "Optional explicit IAM role name for the GitHub Actions image publish role."
  type        = string
  default     = ""
}

variable "scan_on_push" {
  description = "Whether ECR should scan images on push."
  type        = bool
  default     = true
}

variable "encryption_type" {
  description = "ECR repository encryption type."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "KMS"], var.encryption_type)
    error_message = "encryption_type must be AES256 or KMS."
  }
}

variable "kms_key_arn" {
  description = "Optional KMS key ARN when encryption_type is KMS. Leave null for AES256."
  type        = string
  default     = null
}
