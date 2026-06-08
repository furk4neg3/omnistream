# ECR Publishing Prerequisites Module

This Terraform module is an optional AWS-readiness building block for the existing manual OmniStream image publishing workflow.

It creates image-publishing infrastructure only. It does not deploy OmniStream services.

## What It Creates

When an environment root explicitly enables this module, it creates:

* ECR repositories for the current service image contract:
  * `${image_namespace}/query-api`
  * `${image_namespace}/processing-agent`
  * `${image_namespace}/producer`
* immutable image tags for those repositories through `image_tag_mutability = "IMMUTABLE"`;
* ECR scan-on-push enabled by default;
* AES-256 ECR encryption by default, with an optional KMS override;
* a GitHub Actions OIDC provider for `token.actions.githubusercontent.com`;
* an IAM role trusted by the configured GitHub repository/ref patterns; and
* an IAM policy that allows GitHub Actions to get an ECR authorization token and push images only to the three repositories managed by the module.

The IAM role ARN is intended to become the `AWS_ROLE_TO_ASSUME` GitHub repository variable used by `.github/workflows/publish-images.yml`.

## What It Does Not Create

This module intentionally does not create ECS clusters, ECS services, ECS task definitions, VPCs, subnets, load balancers, Kinesis streams, MSK resources, OpenSearch resources, Bedrock resources, SageMaker resources, SSM parameters, Secrets Manager secrets, CloudWatch log groups, alarms, dashboards, deployment pipelines, or application runtime infrastructure.

It also does not change Dockerfiles, Docker Compose, service source code, API contracts, or the manual publish workflow.

## Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `name_prefix` | Yes | n/a | Environment-scoped prefix for IAM names. |
| `image_namespace` | Yes | n/a | Repository prefix matching `OMNISTREAM_IMAGE_NAMESPACE`; defaults are supplied by environment roots. |
| `github_actions_repository_owner` | Yes | n/a | GitHub organization or user allowed to assume the publish role. |
| `github_actions_repository_name` | Yes | n/a | GitHub repository allowed to assume the publish role. |
| `github_actions_ref_patterns` | No | `["ref:refs/heads/main"]` | OIDC `sub` ref patterns allowed to assume the role. |
| `github_oidc_thumbprint_list` | No | GitHub Actions OIDC SHA-1 thumbprint | Thumbprints for the OIDC provider; verify before applying in a live account. |
| `publish_role_name` | No | derived from `name_prefix` | Optional explicit IAM role name. |
| `scan_on_push` | No | `true` | Enables ECR scan-on-push. |
| `encryption_type` | No | `AES256` | ECR encryption type, either `AES256` or `KMS`. |
| `kms_key_arn` | No | `null` | Optional KMS key ARN when `encryption_type = "KMS"`. |
| `tags` | No | `{}` | Common resource tags. |

## Outputs

| Output | Description |
| --- | --- |
| `repository_names` | ECR repository names keyed by `query_api`, `processing_agent`, and `producer`. |
| `repository_urls` | ECR repository URLs keyed by service. |
| `repository_arns` | ECR repository ARNs keyed by service. |
| `publish_role_arn` | IAM role ARN for the `AWS_ROLE_TO_ASSUME` GitHub repository variable. |
| `github_oidc_provider_arn` | GitHub Actions OIDC provider ARN created by the module. |

## Usage

The committed environment roots keep this module disabled by default:

```hcl
enable_ecr_publishing_prereqs = false
```

To use it in a real AWS account, copy an environment `terraform.tfvars.example`, set `enable_ecr_publishing_prereqs = true`, replace the GitHub owner/repository placeholders, verify the OIDC thumbprint, then run Terraform from that environment root.

The resulting repository names continue to match the existing immutable image contract resolved by:

```bash
python3 scripts/resolve_image_tags.py
```
