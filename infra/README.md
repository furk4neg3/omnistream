# OmniStream Infrastructure Skeleton

This directory contains the first Terraform skeleton for OmniStream AWS readiness. It defines environment, provider, naming, tag, and future configuration path conventions only.

It follows the ECS-first direction from `docs/adr/0001-initial-aws-runtime-target.md` and `docs/ecs-deployment-design.md`, while keeping Docker Compose as the implemented local runtime.

## Layout

```text
infra/
  environments/
    dev/
      versions.tf
      variables.tf
      locals.tf
      outputs.tf
      terraform.tfvars.example
    prod/
      versions.tf
      variables.tf
      locals.tf
      outputs.tf
      terraform.tfvars.example
```

Each environment root is intentionally minimal and consistent. The roots configure Terraform and the AWS provider, define safe input variables, calculate shared naming and tag locals, and output those conventions for later infrastructure steps.

The existing placeholder module directories are reserved for later work. They are not wired into these roots yet.

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

## Non-goals

This skeleton does not deploy OmniStream and does not create live AWS resources.

It does not create ECS clusters, ECS task definitions, ECS services, ECR repositories, IAM roles or policies, Kinesis streams, MSK resources, OpenSearch resources, S3 buckets, DynamoDB tables, CloudWatch log groups, SSM parameters, Secrets Manager secrets, VPCs, subnets, load balancers, alarms, dashboards, or any other AWS resource.

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

## Verification

These commands validate the current non-deploying skeleton without requiring AWS credentials:

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
