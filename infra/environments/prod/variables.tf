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
  default     = "prod"

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
