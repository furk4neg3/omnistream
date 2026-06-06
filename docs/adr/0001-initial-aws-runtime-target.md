# ADR 0001: Initial AWS Runtime Target Is ECS-First

## Status

Accepted

## Context

OmniStream currently runs as a local Docker Compose baseline with three active containerized services:

* `producer`, an optional one-shot profile service that appends raw support events to local JSONL.
* `processing-agent`, a continuously running worker that polls the append-only JSONL input, checkpoints progress, enriches and chunks events, embeds chunks, writes enriched JSONL, updates the local vector store, and writes local status/metrics snapshots.
* `query-api`, a FastAPI service exposing `/health`, `/status`, `/metrics`, `/search`, `/ask`, and `/ingest`.

Docker Compose wires these services together through a shared `.local/omnistream` mount. The current local transport, checkpointing, status snapshots, vector store, and default fallback embedding/RAG behavior are all file-backed and intentionally local.

CI validates the Python test suite, Docker Compose configuration, and Docker image builds for the three active services. A manual GitHub Actions workflow can publish immutable `query-api`, `processing-agent`, and `producer` images to pre-existing Amazon ECR repositories through GitHub Actions OIDC, but it does not create ECR repositories, deploy services, or create AWS resources.

The first AWS runtime target needs to match what already exists: independently built service containers, a working local Compose workflow, an ECR image publishing contract, and no committed AWS infrastructure implementation yet.

## Decision Drivers

* Reuse the current three-service container boundary without changing service code.
* Keep Docker Compose as the local development and demo workflow.
* Build on the existing ECR image publishing workflow.
* Prefer the smallest first cloud runtime surface that can run long-lived API and worker containers.
* Avoid Kubernetes operational overhead until the project has a demonstrated need for it.
* Preserve room for later managed streaming, managed vector search, observability, and secrets work.
* Avoid implying that Terraform, ECS services, EKS manifests, Helm charts, or managed AWS integrations already exist.

## Considered Options

### ECS-first

ECS-first means the initial AWS deployment path should model the existing containers as ECS task definitions and ECS services in a later step. `query-api` can become an ALB-facing service later, while `processing-agent` can run as a long-lived worker service or task. The manual ECR publishing workflow already produces the image references that ECS would consume.

This option fits the current repo because it has three containerized services, Docker Compose already proves the service boundaries, and ECS can run those containers without adding Kubernetes cluster, Helm, ingress controller, or pod manifest complexity to the first deployment path.

### EKS-first

EKS-first would model the services as Kubernetes workloads from the start. This remains a reasonable later option if OmniStream needs Kubernetes-native scheduling, shared cluster standards, custom controllers, service mesh behavior, Helm-based release management, or Milvus-on-Kubernetes operations.

For the first deployment path, EKS adds more moving parts than the current repo needs. There are no Kubernetes manifests, Helm charts, cluster add-on definitions, or Kubernetes-specific operational assumptions in the repository today.

### Lambda-first or Serverless-first

Lambda-first or serverless-first can be useful for event-driven edges, scheduled jobs, or narrow functions. It is less aligned with the current repo because `query-api` is a containerized HTTP service and `processing-agent` is a polling, checkpointing worker that is already shaped as a long-running container.

Serverless services may still be useful later around ingestion, fan-out, scheduled maintenance, or lightweight control-plane work, but they are not the best initial runtime target for the current containers.

## Decision

Choose ECS-first as the initial AWS deployment path.

The first AWS runtime design should target ECS task and service definitions for the existing containers in a later step. The decision does not deploy OmniStream to AWS and does not add ECS task definitions in this task.

## Why ECS-First Fits This Repo

* The repo already has three containerized services: `producer`, `processing-agent`, and `query-api`.
* The existing manual ECR workflow can publish immutable service images for an ECS runtime to consume later.
* ECS is a simpler first deployment target than Kubernetes for the current service shape.
* `query-api` maps cleanly to an ALB-facing ECS service later.
* `processing-agent` maps cleanly to a long-running ECS worker task or service later.
* ECS-first keeps the local Docker Compose workflow intact for development and demos.

## What Stays Local For Now

* JSONL file transport for raw and enriched event flow.
* The local vector store under `.local/omnistream`.
* Local checkpoint files and local status/metrics snapshot files.
* Local fallback embedding and RAG behavior, including disabled-by-default LLM RAG.
* Docker Compose as the source of truth for local development.

## What Moves Toward AWS First

* Published container images in ECR, using the existing manual publishing workflow.
* ECS task and service definitions in a later step.
* An ALB-facing `query-api` service in a later step.
* CloudWatch logs and metrics in a later step.
* SSM Parameter Store and Secrets Manager configuration in a later step.

## Consequences And Tradeoffs

* The first cloud path can focus on running the existing containers before replacing transport, vector search, or state stores.
* The repo can keep Compose as the local baseline while adding ECS-specific deployment artifacts later.
* ECS-first avoids adding Kubernetes-specific files before the project needs Kubernetes-specific behavior.
* ECS-first still requires careful design for IAM roles, networking, health checks, logs, resource limits, config, and secrets.
* The current JSONL transport, local vector store, and local checkpoint/status files are not cloud-ready persistence choices and must be replaced or adapted before relying on an AWS deployment.
* ECS may be less flexible than EKS for workloads that later need Kubernetes-native operators, cluster-level policy, service mesh behavior, or Milvus-on-Kubernetes operations.

## Why This Does Not Permanently Reject EKS

ECS-first is an initial deployment target decision, not a permanent platform rejection. EKS remains a later option if OmniStream needs Kubernetes-native scheduling, Helm-based releases, shared cluster operations, service mesh features, custom controllers, or a vector database architecture that is better operated on Kubernetes.

The service code and container image contract should remain portable enough that a later EKS path can reuse the same images and core service boundaries.

## Explicit Non-Goals

* No Terraform is added in this task.
* No live AWS resources are created.
* No ECS task definitions are added yet.
* No EKS manifests or Helm charts are added.
* No Kinesis, OpenSearch, Bedrock, or SageMaker integration is added.
* No AWS SDK runtime code is added.
* No service source code is changed.
* No Docker Compose behavior is changed.
* No secrets or real AWS credentials are added.

## Assumptions

* ECR repositories and the GitHub OIDC role, when used, are provisioned outside the current repository unless a future infrastructure step explicitly adds that responsibility.
* The first ECS design can consume immutable images produced by the existing manual workflow.
* The local file-backed workflow remains valuable for development and should continue to work independently of AWS readiness artifacts.
* Managed stream, vector database, observability, config, and secrets migrations will be handled as separate later steps.

## Next Migration Step

Define the initial ECS task and service design for `query-api` and `processing-agent`, including container images, environment variable sources, IAM role boundaries, health checks, logs, resource sizing, and ALB exposure for `query-api`, without creating live AWS resources.
