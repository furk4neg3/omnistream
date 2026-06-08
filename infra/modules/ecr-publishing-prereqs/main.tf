locals {
  github_oidc_provider_url  = "https://token.actions.githubusercontent.com"
  github_oidc_provider_host = "token.actions.githubusercontent.com"

  service_repositories = {
    processing_agent = "${var.image_namespace}/processing-agent"
    producer         = "${var.image_namespace}/producer"
    query_api        = "${var.image_namespace}/query-api"
  }

  github_repository_slug = "${var.github_actions_repository_owner}/${var.github_actions_repository_name}"
  github_sub_patterns = [
    for ref_pattern in var.github_actions_ref_patterns :
    "repo:${local.github_repository_slug}:${ref_pattern}"
  ]
}

resource "aws_ecr_repository" "service" {
  for_each = local.service_repositories

  name                 = each.value
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  encryption_configuration {
    encryption_type = var.encryption_type
    kms_key         = var.kms_key_arn
  }

  tags = merge(
    var.tags,
    {
      Name    = each.value
      Service = replace(each.key, "_", "-")
    },
  )
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = local.github_oidc_provider_url
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = var.github_oidc_thumbprint_list

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-github-actions-oidc"
    },
  )
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    sid     = "AllowGitHubActionsOidc"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_provider_host}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "${local.github_oidc_provider_host}:sub"
      values   = local.github_sub_patterns
    }
  }
}

resource "aws_iam_role" "publish_images" {
  name                 = var.publish_role_name != "" ? var.publish_role_name : substr("${var.name_prefix}-github-ecr-publisher", 0, 64)
  description          = "Allows the OmniStream manual GitHub Actions workflow to publish immutable service images to ECR."
  assume_role_policy   = data.aws_iam_policy_document.github_actions_assume_role.json
  max_session_duration = 3600

  tags = merge(
    var.tags,
    {
      Name = var.publish_role_name != "" ? var.publish_role_name : substr("${var.name_prefix}-github-ecr-publisher", 0, 64)
    },
  )
}

data "aws_iam_policy_document" "publish_images" {
  statement {
    sid       = "AllowEcrAuthorizationToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowPushToOmniStreamRepositories"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:DescribeRepositories",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:ListImages",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = values(aws_ecr_repository.service)[*].arn
  }
}

resource "aws_iam_policy" "publish_images" {
  name        = substr("${var.name_prefix}-ecr-image-publish", 0, 128)
  description = "Allows GitHub Actions to push OmniStream images only to the managed ECR repositories."
  policy      = data.aws_iam_policy_document.publish_images.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "publish_images" {
  role       = aws_iam_role.publish_images.name
  policy_arn = aws_iam_policy.publish_images.arn
}
