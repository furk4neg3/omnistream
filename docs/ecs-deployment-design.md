# ECS Deployment Design

## Purpose

This document defines the first ECS runtime boundary for OmniStream's existing containerized services. It is a design and AWS-readiness artifact only.

It does not create an implemented AWS deployment. A minimal non-deploying Terraform skeleton now exists under `infra/` for environment, provider, naming, tag, and future configuration path conventions only. This design does not add ECS task-definition JSON, deployment manifests, AWS SDK runtime dependencies, live AWS resources, or any requirement for AWS credentials. Docker Compose remains the implemented local runtime.

This design follows [ADR 0001](adr/0001-initial-aws-runtime-target.md), which chooses ECS-first as the initial AWS runtime target while keeping EKS and other managed services available as later options.

## Current Local Service Shape

OmniStream currently runs as a local Docker Compose stack with three active service containers wired together through shared local files under `.local/omnistream`.

* `query-api` is a FastAPI service running Uvicorn on container port `8000`. Compose exposes it on the host port configured by `QUERY_API_PORT`, defaulting to `8000`. It reads the local vector store, exposes `/health`, `/status`, `/metrics`, `/search`, `/ask`, and `/ingest`, and reads producer and processing-agent status snapshots from local JSON files.
* `processing-agent` is a continuously running worker. It polls `events/events.jsonl`, reads and writes a local checkpoint, enriches and chunks raw events, embeds chunks, appends enriched JSONL, updates the local vector-store directory, and writes a metrics/status snapshot.
* `producer` is a Compose profile service, not part of the default always-on stack. It runs as a controlled one-shot local generator that appends demo raw events to `events/events.jsonl` and writes a local status snapshot.

Both `query-api` and `processing-agent` currently share `/workspace/local-data/vector_store` and use the same embedding model name so model or vector-store mismatches fail visibly.

## ECS Target Boundary

The initial ECS target should run the existing images and service commands without changing API contracts or service source code.

The first always-on ECS runtime boundary should include:

* an ALB-facing `query-api` ECS service;
* an internal `processing-agent` ECS worker service or long-running task; and
* no always-on `producer` service.

This boundary is intentionally smaller than a complete production migration. The local file-backed transport, local checkpoints, local status files, and local vector-store directory are not durable cloud persistence choices and need later replacement before the ECS path can be considered production-ready.

## Service Mapping

| Local service | First ECS treatment | Exposure | Notes |
| --- | --- | --- | --- |
| `query-api` | ALB-facing ECS service | Public or private Application Load Balancer listener, depending on environment | Runs the existing `services/query-api` image command on container port `8000`. The target group should use `/health`. |
| `processing-agent` | Internal long-running ECS worker service or task | No public listener | Runs the existing `services/processing-agent` image command. It should have only internal network egress needed for future stream, state, vector database, metrics, and optional embedding/model dependencies. |
| `producer` | Deferred; one-shot or demo-only ECS task later | No always-on exposure | Do not include `producer` in the first always-on ECS runtime. If needed later, run it explicitly as a one-shot/demo task rather than a continuously deployed service. |

## Container Image Source

ECS should consume immutable images produced by the existing image contract and manual ECR publishing workflow.

The intended image source is Amazon ECR repositories that already exist outside this design:

```text
${OMNISTREAM_IMAGE_NAMESPACE}/query-api
${OMNISTREAM_IMAGE_NAMESPACE}/processing-agent
${OMNISTREAM_IMAGE_NAMESPACE}/producer
```

The existing manual workflow publishes immutable `${APP_VERSION}-${GIT_SHA_SHORT}` tags and does not push `latest`, create ECR repositories, or deploy services. The first ECS implementation should reference those immutable tags rather than mutable local `:local` tags.

## Networking and ALB Exposure

`query-api` should be the only first-path ALB-exposed service. The ECS task should listen on container port `8000`, with an Application Load Balancer target group forwarding HTTP traffic to that container port.

Recommended first networking boundary:

* place the ALB in environment-appropriate subnets;
* place ECS tasks in private subnets when practical;
* allow inbound traffic from the ALB security group to the `query-api` task security group on port `8000`;
* do not assign a public listener, target group, or security-group ingress rule to `processing-agent`;
* allow `processing-agent` only the outbound access it needs for future managed stream, state, vector database, CloudWatch, and optional provider/model calls; and
* keep `producer` out of the always-on service graph.

Whether the ALB is internet-facing or internal is an environment decision. A demo environment may choose an internet-facing ALB with tight access controls, while private environments should prefer an internal ALB or private access path.

## Environment Variables and SSM Parameter Store

Non-secret runtime settings should be modeled as SSM Parameter Store values and injected into ECS task definitions in a later implementation step.

Examples of non-secret settings that map naturally to SSM Parameter Store:

| Setting | ECS use |
| --- | --- |
| `APP_NAME` | `query-api` display name. |
| `APP_VERSION` | Runtime version metadata, kept aligned with image tags. |
| `DEPENDENCY_STATUS_MAX_AGE_SECONDS` | `query-api` local dependency snapshot staleness threshold until status moves to CloudWatch. |
| `ENABLE_LLM_RAG` | Feature flag for optional LLM-backed `/ask`. |
| `LLM_MODEL_NAME` | Non-secret model selection. |
| `MAX_CONTEXT_CHUNKS`, `MAX_CONTEXT_CHARS`, `LLM_TEMPERATURE`, `LLM_MAX_OUTPUT_TOKENS` | Non-secret query-api generation controls. |
| `POLL_INTERVAL_SECONDS`, `LOOP_FOREVER`, `BATCH_SIZE` | Processing-agent worker behavior. |
| `CHUNK_SIZE_WORDS`, `CHUNK_OVERLAP_WORDS`, `SCHEMA_VERSION`, `PROCESSING_VERSION` | Shared processing and query behavior. |
| `OMNISTREAM_EMBEDDING_MODEL_NAME` or service-level `EMBEDDING_MODEL_NAME` | Embedding compatibility setting that must stay aligned across worker and API. |
| `AWS_REGION`, `KINESIS_STREAM_NAME` | Future cloud integration settings. |

Local host-path settings such as `VECTOR_STORE_DIR`, `INPUT_FILE`, `OUTPUT_FILE`, `CHECKPOINT_FILE`, `METRICS_FILE`, `PROCESSING_AGENT_METRICS_FILE`, and `PRODUCER_METRICS_FILE` should not be carried forward as durable cloud configuration. During any temporary ECS prototype, these paths would need an explicit temporary storage decision, but the durable design should replace them with managed stream, state, telemetry, and vector-database settings.

## Secrets and Secrets Manager

Secret runtime settings should be stored in AWS Secrets Manager and injected into ECS tasks as secrets in a later implementation step.

The current secret candidates are:

* `GEMINI_API_KEY`;
* `GOOGLE_API_KEY`; and
* any future external provider credentials used by query, embedding, stream, vector, or observability integrations.

Do not put real secret values in `.env.example`, committed docs, task-definition templates, CloudWatch logs, or normal application logs. Long-lived AWS access keys should not be used by ECS tasks; use IAM roles instead.

## IAM Role Boundaries

The first ECS implementation should distinguish the ECS task execution role from application task roles.

The ECS task execution role should be limited to platform needs such as:

* pulling images from ECR;
* writing container logs through the configured log driver; and
* reading Parameter Store or Secrets Manager values only if the ECS agent needs those permissions for injection.

Application task roles should be separate per service where practical:

* `query-api` application task role: read only the SSM parameters and Secrets Manager secrets required by the API; later read vector database or managed retrieval resources; later emit custom metrics if needed.
* `processing-agent` application task role: read only the worker configuration it needs; later consume the managed stream; later write enriched output, checkpoints, vector records, metrics, and any dead-letter or retry state.
* `producer` application task role: no always-on role in the first ECS path; if a later one-shot/demo task is added, grant only the write permission needed for the chosen demo event destination.

The execution role should not become a broad application role, and the application task roles should not get repository-push, infrastructure-management, or unrelated administrative permissions.

## Health Checks

`query-api` already exposes `/health`. The first ALB target group and ECS container health check should use that endpoint on container port `8000`.

`processing-agent` already has a Python healthcheck module invoked locally as:

```text
python -m app.healthcheck
```

That module reads the worker metrics/status snapshot, requires status `running`, validates `updated_at`, and fails if the snapshot is missing, invalid, unreadable, non-running, or stale. The first ECS worker design should preserve this behavior for container health while recognizing that the underlying local status file must later become cloud-safe telemetry.

`producer` should not have an always-on ECS health check in the first runtime path because it is deferred from the first always-on service set.

## Logs, Metrics, and CloudWatch

The first ECS implementation should send stdout and stderr from both always-on services to CloudWatch Logs with service-specific log groups or streams.

Initial CloudWatch expectations:

* preserve structured application log events from `query-api` and `processing-agent`;
* capture container lifecycle, startup, and health-check failures;
* treat `/metrics` and `/status` as current local observability surfaces, not as a complete cloud monitoring system;
* promote important counters, worker freshness, error counts, and vector-store state into CloudWatch metrics in a later step; and
* add CloudWatch alarms only after the deployed metric names and expected thresholds are defined.

Local JSON status snapshots should not be the final CloudWatch metrics design. They are useful for local Compose and initial health behavior, but durable ECS observability should use logs, metrics, alarms, and dashboards.

## CPU and Memory Assumptions

Start with small, explicit ECS resource sizes and revise after load testing.

Recommended first assumptions:

| Service | CPU | Memory | Rationale |
| --- | --- | --- | --- |
| `query-api` | 0.25 to 0.5 vCPU | 512 MiB to 1 GiB | FastAPI service with local embedding/query behavior and optional LLM calls. |
| `processing-agent` | 0.5 vCPU | 1 GiB | Continuous polling, enrichment, chunking, embedding, and vector-store updates. Increase if sentence-transformers or larger embedding models are enabled. |
| `producer` | Not always-on | Not always-on | Defer sizing until a one-shot/demo ECS task is explicitly designed. |

These are readiness assumptions, not measured production limits. Any first implementation should set CPU and memory intentionally and then validate startup time, health-check stability, batch throughput, and query latency.

## Local File-Backed State Limitations

The current local stack depends on file paths under `.local/omnistream`, mounted into containers as `/workspace/local-data`. That design is useful for local development and demos, but it is not a durable cloud persistence strategy.

The following local state must be replaced or deliberately adapted before relying on ECS:

* local raw JSONL event files such as `events/events.jsonl`;
* local enriched JSONL output files such as `enriched/enriched_events.jsonl`;
* local checkpoint files such as `state/processing-checkpoint.json`;
* local status and metrics JSON files such as `state/processing-agent-metrics.json` and `state/producer-metrics.json`;
* local vector-store files under `vector_store/`; and
* local model-cache directories under `model-cache/`, if optional model downloads are enabled.

Likely later replacements include a managed stream for raw events, durable checkpoint ownership in the consumer path, CloudWatch logs and metrics for status, and a managed vector database or other cloud-safe retrieval store for embeddings and metadata.

## Non-goals

This design intentionally does not:

* add deploying Terraform resources or any runtime infrastructure implementation;
* add ECS task-definition JSON;
* add Kubernetes, EKS, or Helm manifests;
* create live AWS resources;
* deploy OmniStream to AWS;
* introduce AWS SDK runtime dependencies;
* require AWS credentials for local verification;
* modify `.env` or add real secret values;
* change service source code, API contracts, Dockerfiles, or Docker Compose behavior;
* replace JSONL transport, checkpoints, status files, or the local vector store; or
* define production alarms, dashboards, autoscaling policies, rollback policy, or managed vector database selection.

## Open Questions

* Which AWS account, region, environment names, VPC, subnet, and DNS conventions should the first ECS implementation use?
* Should the first `query-api` ALB be internet-facing for demo use, internal-only, or exposed through a private access path?
* What is the temporary ECS-safe storage choice, if any, before JSONL transport and local vector-store state are replaced?
* Which managed stream should replace raw JSONL input first: Kinesis Data Streams, MSK, or another source?
* Which managed vector store should replace the local `vector_store/` directory?
* How should tenant isolation move from payload fields into identity, stream partitioning, metadata filters, or separate stores?
* What CloudWatch metric names, dashboards, alarms, and freshness thresholds should replace local status snapshots?
* Should `processing-agent` run as an ECS service with desired count one, a scheduled task, or another worker pattern once stream semantics are defined?

## Recommended Next Implementation Step

Create an infrastructure skeleton for the ECS boundary that defines networking, IAM role names and permissions, SSM parameter names, Secrets Manager secret names, log groups, and placeholders for ECS services, without deploying the services or adding service source-code changes.
