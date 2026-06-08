variable "project_name" {
  description = "Short project name used for naming and tagging conventions."
  type        = string
  default     = "omnistream"

  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9_-]*$", var.project_name))
    error_message = "project_name must contain only letters, numbers, hyphens, and underscores, and must start with a letter or number."
  }
}

variable "environment" {
  description = "Deployment environment name for this Terraform root."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9-]*$", var.environment))
    error_message = "environment must contain only letters, numbers, and hyphens, and must start with a letter or number."
  }
}

variable "aws_region" {
  description = "AWS region selected for future resources in this environment."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must look like an AWS region, such as us-east-1."
  }
}

variable "owner" {
  description = "Owner tag value for future AWS resources."
  type        = string
  default     = "portfolio-owner"

  validation {
    condition     = length(trimspace(var.owner)) > 0
    error_message = "owner must not be empty."
  }
}

variable "cost_center" {
  description = "Optional cost center tag value for future AWS resources."
  type        = string
  default     = ""
}

variable "additional_tags" {
  description = "Additional non-secret tags to merge into the common tag set."
  type        = map(string)
  default     = {}
}

variable "image_namespace" {
  description = "Container image namespace or ECR repository prefix used by the existing image publishing contract."
  type        = string
  default     = "omnistream"

  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*$", var.image_namespace)) && !endswith(var.image_namespace, "/")
    error_message = "image_namespace must contain only letters, numbers, dots, underscores, hyphens, and slashes, and must not end with a slash."
  }
}

variable "enable_ecr_publishing_prereqs" {
  description = "Whether to create optional ECR repositories and GitHub Actions OIDC publishing prerequisites for the manual image publish workflow."
  type        = bool
  default     = false
}

variable "github_actions_repository_owner" {
  description = "GitHub organization or user allowed to assume the optional ECR image publish role when enabled."
  type        = string
  default     = "REPLACE_WITH_GITHUB_OWNER"
}

variable "github_actions_repository_name" {
  description = "GitHub repository allowed to assume the optional ECR image publish role when enabled."
  type        = string
  default     = "REPLACE_WITH_GITHUB_REPOSITORY"
}

variable "github_actions_ref_patterns" {
  description = "GitHub OIDC sub-claim ref patterns allowed to assume the optional ECR image publish role."
  type        = list(string)
  default     = ["ref:refs/heads/main"]

  validation {
    condition     = length(var.github_actions_ref_patterns) > 0
    error_message = "github_actions_ref_patterns must include at least one allowed ref pattern."
  }
}

variable "github_oidc_thumbprint_list" {
  description = "Thumbprints for the GitHub Actions OIDC provider. Verify against GitHub/AWS guidance before applying in a real account."
  type        = list(string)
  default     = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

variable "github_actions_publish_role_name" {
  description = "Optional explicit IAM role name for the GitHub Actions image publish role."
  type        = string
  default     = ""
}

variable "ecr_scan_on_push" {
  description = "Whether optional ECR repositories should scan images on push."
  type        = bool
  default     = true
}

variable "ecr_encryption_type" {
  description = "Encryption type for optional ECR repositories."
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "KMS"], var.ecr_encryption_type)
    error_message = "ecr_encryption_type must be AES256 or KMS."
  }
}

variable "ecr_kms_key_arn" {
  description = "Optional KMS key ARN when ecr_encryption_type is KMS."
  type        = string
  default     = null
}
