# OmniStream Infrastructure Skeleton

This directory contains the first Terraform skeleton for OmniStream AWS readiness. It defines environment, provider, naming, tag, and future configuration path conventions only.

It follows the ECS-first direction from `docs/adr/0001-initial-aws-runtime-target.md` and `docs/ecs-deployment-design.md`, while keeping Docker Compose as the implemented local runtime.

## Layout

```text
infra/
  ecs/
    README.md
    task-definitions/
      query-api.taskdef.json
      processing-agent.taskdef.json
  modules/
    ecr-publishing-prereqs/
      main.tf
      variables.tf
      outputs.tf
      README.md
  environments/
    dev/
      main.tf
      versions.tf
      variables.tf
      locals.tf
      outputs.tf
      terraform.tfvars.example
    prod/
      main.tf
      versions.tf
      variables.tf
      locals.tf
      outputs.tf
      terraform.tfvars.example
```

Each environment root is intentionally minimal and consistent. The roots configure Terraform and the AWS provider, define safe input variables, calculate shared naming and tag locals, and output those conventions for later infrastructure steps.

The optional `ecr-publishing-prereqs` module is wired into each root behind `enable_ecr_publishing_prereqs = false`. The committed default does not create resources. If explicitly enabled in an environment tfvars file and applied in a real AWS account, it creates only the ECR repositories and GitHub Actions OIDC/IAM prerequisites required by the existing manual image publishing workflow.

The `ecs/` directory contains static ECS task-definition templates for the first always-on `query-api` and `processing-agent` service set. These templates are readiness artifacts only; they are not wired into Terraform and do not deploy or create resources.

## What This Defines

The current skeleton defines conventions for:

* project and environment names;
* AWS region selection;
* common tags;
* name prefixes;
* future SSM Parameter Store paths;
* future Secrets Manager name prefixes;
* future CloudWatch log group prefixes; and
* future ECR repository prefixes matching the existing image contract.

The optional ECR publishing prerequisites module can define:

* ECR repositories for `query-api`, `processing-agent`, and `producer`;
* immutable ECR image tags, scan-on-push, and repository encryption defaults;
* a GitHub Actions OIDC provider and publish role; and
* IAM permissions for the manual workflow to push images only to those repositories.

The ECS task-definition templates additionally document first-pass Fargate CPU and memory assumptions, image placeholders, role placeholders, CloudWatch log placeholders, environment variables, and container health checks for the two always-on services.

## Non-goals

The committed default skeleton does not deploy OmniStream and does not create live AWS resources.

Even when the ECR publishing prerequisites module is enabled, it does not create ECS clusters, ECS task definitions, ECS services, Kinesis streams, MSK resources, OpenSearch resources, S3 buckets, DynamoDB tables, CloudWatch log groups, SSM parameters, Secrets Manager secrets, VPCs, subnets, load balancers, alarms, dashboards, runtime task roles, or application deployment resources.

It also does not change service source code, API contracts, Dockerfiles, Docker Compose behavior, CI image builds, or the manual ECR publishing workflow.

## Remote State Assumptions

No remote backend is configured yet. This keeps normal local verification from requiring AWS credentials, an S3 backend bucket, or a DynamoDB lock table.

A future deploying infrastructure step should choose and document a real backend before managing shared state. Expected options include an S3 backend with DynamoDB locking or Terraform Cloud. Backend bucket names, lock table names, account IDs, role ARNs, and workspace names must be supplied by the target environment and should not be hardcoded in this skeleton.

## Usage

Copy an example tfvars file only when you are ready to experiment with local Terraform commands:

```bash
cp infra/environments/dev/terraform.tfvars.example infra/environments/dev/terraform.tfvars
```

Do not put secrets, credentials, account IDs, fixed ARNs, or production-only values in committed tfvars examples.

The ECR/OIDC prerequisites remain off unless explicitly enabled:

```hcl
enable_ecr_publishing_prereqs = false
```

To apply them in a real AWS account, set that flag to `true`, replace the GitHub repository placeholders, review the OIDC thumbprint, and run Terraform from the selected environment root. After apply, use the `ecr_publishing_role_arn` output as the `AWS_ROLE_TO_ASSUME` GitHub repository variable for `.github/workflows/publish-images.yml`.

## Verification

The Makefile-backed readiness check validates required AWS-readiness files, ECS task-definition JSON syntax, deterministic image-tag resolution, and Terraform formatting without requiring AWS credentials:

```bash
make aws-readiness-check
```

Terraform is required for the formatting check. The underlying direct command is:

```bash
terraform fmt -check -recursive infra
```

If Terraform is installed and provider downloads are available, validate each root with the backend disabled:

```bash
terraform -chdir=infra/environments/dev init -backend=false
terraform -chdir=infra/environments/dev validate
terraform -chdir=infra/environments/prod init -backend=false
terraform -chdir=infra/environments/prod validate
```

The broader OmniStream verification remains:

```bash
bash scripts/run_tests.sh
docker compose config
python3 scripts/resolve_image_tags.py --git-sha 0123456789abcdef0123456789abcdef01234567
```
