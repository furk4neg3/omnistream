# AWS Migration Readiness

## Purpose

This is the first AWS-readiness artifact for OmniStream. It maps the current local, Docker Compose-based prototype to likely future AWS resources and identifies the practical gaps to close before a first cloud deployment.

This document is not an AWS deployment plan that has already been implemented. It does not introduce Helm, AWS SDK usage, deployment manifests, or runtime cloud dependencies. A minimal non-deploying Terraform skeleton now exists under `infra/` for environment, provider, naming, tag, and future configuration path conventions only. The implemented baseline remains the local production-style prototype in this repository, with a manual ECR image publishing step available for prepared AWS accounts.

[ADR 0001](adr/0001-initial-aws-runtime-target.md) records ECS-first as the initial AWS runtime target. This is a target decision only; no ECS deployment or task definitions exist in this repository yet.

The first ECS runtime boundary is captured in [docs/ecs-deployment-design.md](ecs-deployment-design.md). That document is also a design/readiness artifact only, not an implemented AWS deployment.

## Current local baseline

The current repo implements a three-service local stack with shared file-backed state under the Compose-mounted `.local/omnistream` directory:

* `producer` runs as an optional one-shot Compose profile service. In the default Compose path it uses `OUTPUT_MODE=file` and appends raw support events to `events/events.jsonl`. The emitted local event mix includes `support_ticket` and `customer_chat_message` records, controlled by environment variables such as `TENANT_ID`, `EVENT_TYPES`, `EVENTS_PER_SECOND`, and `MAX_EVENTS`.
* `processing-agent` runs continuously by default. It polls the append-only JSONL input file, reads from its checkpoint, validates raw events, routes them, enriches them, creates chunks, embeds those chunks, appends enriched records to `enriched/enriched_events.jsonl`, updates the local vector store, and saves the next checkpoint.
* The local vector store is shared through the Compose mount `./.local/omnistream:/workspace/local-data`. Both `processing-agent` and `query-api` use `/workspace/local-data/vector_store`, and both are configured with the same embedding model name so the query API can fail loudly if it reads a vector store created with a different model.
* `query-api` is a FastAPI service exposed on the local host port configured by `QUERY_API_PORT`, defaulting to `8000`. It exposes `/health`, `/metrics`, `/status`, `/search`, `/ask`, and `/ingest`.
* The three active service images run as the non-root `omnistream` user, with UID/GID `1000` by default, while preserving the existing Compose commands and shared local mount.
* `/status` combines query-api runtime state, vector store summary, and local dependency visibility from status files such as `state/processing-agent-metrics.json` and `state/producer-metrics.json`. Missing, unreadable, invalid, or stale status files are represented explicitly instead of being hidden.
* `/metrics` returns query-api JSON counters, timings, uptime, and vector store summary. The producer and processing-agent also write local metrics/status snapshots for the query API to read.
* LLM-backed `/ask` behavior is opt-in through `ENABLE_LLM_RAG=true` and an API key. The default local path uses the deterministic local fallback and `hashing-local-v1` embeddings.
* CI runs the Python test suite with `bash scripts/run_tests.sh`, validates the Compose configuration with `docker compose config`, and builds the `query-api`, `processing-agent`, and `producer` Docker images.
* A separate manual-only GitHub Actions workflow can publish immutable `query-api`, `processing-agent`, and `producer` image tags to pre-existing Amazon ECR repositories using GitHub Actions OIDC. It does not deploy services or create AWS resources.

## Local-to-AWS mapping table

| Current local implementation | Future AWS resource direction | Migration note |
| --- | --- | --- |
| `producer` JSONL file output to `.local/omnistream/events/events.jsonl` | Kinesis Data Streams or Amazon MSK producer | Preserve the current event schema and tenant partitioning; replace file append semantics with stream publishing. |
| `processing-agent` file polling and `processing-checkpoint.json` | Kinesis/MSK consumer on ECS first, with EKS or Lambda still possible later | Replace line-number checkpoints with stream offsets, shard iterators, or consumer group state. Keep validation, routing, enrichment, chunking, and embedding logic as the portable core. |
| Local `vector_store/` directory shared by Compose | OpenSearch Serverless, pgvector, or Milvus on EKS | Keep explicit model-name compatibility checks; choose the backend based on vector dimension, filtering needs, tenant isolation, and operational budget. |
| `query-api` FastAPI container | ECS service behind an Application Load Balancer first, with EKS still possible later | Reuse `/health` for load balancer and orchestrator health checks; keep API contracts unchanged during the first deployment. |
| Local checkpoint and status files under `.local/omnistream/state` | DynamoDB, S3, CloudWatch metrics, and CloudWatch logs | Split durable processing state from observability. Checkpoints should be owned by the consumer path; status snapshots should become metrics/logs. |
| `.env` and `.env.example` | SSM Parameter Store and AWS Secrets Manager | Keep non-secret configuration in SSM and provider keys in Secrets Manager. Do not carry local host paths into cloud config. |
| Docker Compose services | ECS services/tasks first, with EKS deployments still possible later | Compose remains the local developer runtime. AWS should use published images and cloud-native task/deployment definitions later. |
| GitHub Actions test, Docker build validation, and manual ECR image publishing | CI pipeline for deployment promotion | Keep image publishing separate from environment promotion and deployment steps. The current publish workflow assumes ECR repositories and an OIDC role already exist. |
| Local JSON logs and `/metrics` JSON responses | CloudWatch logs/metrics and optionally Prometheus/Grafana | Preserve structured event names and counters; add dashboards and alarms once services run in AWS. |
| Optional LLM provider key for `/ask` | Secrets Manager external API secret, or a later Bedrock path | Keep LLM enablement behind a feature flag. Bedrock can be evaluated after the first container deployment path is stable. |

## Recommended migration phases

### Phase 0: current local/Compose baseline

Keep the current Compose workflow as the source of truth for local development and demos. The baseline is useful because producer, processing-agent, query-api, shared local state, health, status, metrics, env-driven config, Docker image builds, and CI are already present.

### Phase 1: container hardening and image publishing

Harden the existing Dockerfiles for a future orchestrated runtime, then publish versioned images from CI. Keep the current service commands and API behavior intact while adding production-oriented image hygiene and reproducible tags.

The repository now includes an opt-in manual ECR publishing workflow for immutable service image tags. ECR repository provisioning, OIDC role setup in AWS, runtime task/deployment definitions, and environment promotion remain separate concerns.

### Phase 2: AWS networking/config/secrets skeleton

Define environment names, region conventions, naming/tag boundaries, VPC/subnet boundaries, IAM role shape, SSM parameters, and Secrets Manager entries. The current `infra/` skeleton starts this phase by defining non-deploying environment/provider/naming/tag outputs only; it does not create VPCs, IAM roles, SSM parameters, Secrets Manager secrets, or application services.

### Phase 3: deploy query-api and processing-agent containers on ECS

Run the existing containers on ECS with the local file transport still abstracted behind temporary cloud-safe state choices. Use `/health`, logs, and metrics to verify service lifecycle behavior before replacing major dependencies. EKS remains a possible later runtime option if the project needs Kubernetes-specific operations.

### Phase 4: replace local file transport with Kinesis/MSK

Move raw event flow from JSONL append/polling to a managed stream. This is where ordering, partition keys, retries, dead-letter behavior, and checkpoint semantics need explicit design.

### Phase 5: replace local vector store/state with managed services

Move vector search and durable state out of local mounted directories. Select OpenSearch Serverless, pgvector, or Milvus on EKS based on retrieval quality, metadata filtering, operational effort, and cost.

### Phase 6: production observability and CI/CD promotion

Promote structured logs, metrics, deployment status, and release gates into AWS-native monitoring and CI/CD. Add alarms, dashboards, rollback expectations, and environment promotion only after the service dependencies are no longer local-file based.

## Readiness checklist

### Already present

* Three independently containerized services: `producer`, `processing-agent`, and `query-api`.
* Docker Compose wiring with shared local state under `.local/omnistream`.
* Environment-driven configuration with a committed `.env.example` template.
* Non-root container runtime users for the active service images.
* Local raw event generation for `support_ticket` and `customer_chat_message`.
* Processing-agent polling, checkpointing, routing, enrichment, chunking, embedding, enriched JSONL output, and vector store upsert.
* Query API endpoints for `/health`, `/metrics`, `/status`, `/search`, `/ask`, and `/ingest`.
* Local dependency visibility through producer and processing-agent status files.
* Embedding model-name compatibility checks between vector store contents and service configuration.
* CI test execution, Compose validation, and Docker image build validation.
* Documented container image naming/tagging contract for `query-api`, `processing-agent`, and `producer`.
* Manual ECR image publishing workflow for the three active service images, using GitHub Actions OIDC and immutable app-version plus git-SHA tags.
* Initial ECS runtime boundary design for `query-api` and `processing-agent`, with `producer` deferred from the first always-on ECS runtime.

### Missing before first AWS deployment

* Pre-existing ECR repositories and a GitHub Actions OIDC role in the target AWS account, if they have not already been configured outside this repository.
* Additional runtime hardening such as explicit resource limits and production image tagging.
* Real AWS account, networking, IAM, config, and secrets boundaries beyond the current non-deploying Terraform naming/tag skeleton.
* ECS task definitions, EKS manifests, or another runtime deployment implementation for the published images.
* Cloud-safe replacement for local file paths used by event input, enriched output, checkpoints, status files, and vector store storage.
* Stream checkpoint and retry semantics for Kinesis or MSK.
* Managed vector database selection and migration plan for current local vector store metadata.
* Cloud log, metric, dashboard, and alarm definitions.
* Deployment rollback and promotion process.

### Intentionally deferred

* Deploying Terraform resources, Helm, or other runtime infrastructure implementation.
* Kinesis/MSK runtime integration.
* Managed vector database provisioning.
* Bedrock integration or replacement of the optional external LLM path.
* Multi-region deployment.
* Full production tenant isolation model.
* Automated model drift detection, retraining, and MLOps workflows.

## Deployment assumptions

* Region and environment naming: use one primary AWS region for the first deployment, with explicit environment names such as `dev`, `staging`, and `prod`. The local `.env.example` defaults to `AWS_REGION=us-east-1`, but the actual deployment region should be chosen before infrastructure work starts.
* Runtime target: ECS is the first AWS runtime target. EKS remains a later option if the project needs Kubernetes-specific scheduling, release, operator, or cluster operations.
* Config and secrets: non-secret values from `.env.example` should map to SSM Parameter Store. Provider API keys such as `GEMINI_API_KEY` and `GOOGLE_API_KEY` should map to Secrets Manager. Long-lived AWS access keys should not be stored in `.env`.
* Image registry: the first AWS deployment should use published, immutable container image tags in ECR instead of building images on the target runtime. The current manual workflow publishes images only; it does not create repositories or deploy services.
* State and checkpoint ownership: processing checkpoints should be owned by the stream consumer path, not by the query API. Status/metrics should become observable telemetry rather than shared local files.
* Vector database compatibility: the selected vector database must preserve the embedding model name and vector dimension expectations currently captured in the local vector store manifest. Changing `OMNISTREAM_EMBEDDING_MODEL_NAME` requires a deliberate reindex or migration.
* Health checks: `/health` is the initial load balancer and orchestrator health-check candidate for `query-api`. Processing-agent needs an equivalent cloud lifecycle signal through logs, metrics, or task health.
* Logs and metrics: structured service logs and JSON metrics should map to CloudWatch first. Prometheus/Grafana can be added later if the deployment platform and operating model justify it.
* Tenant isolation: current local demos rely on tenant IDs in event and query payloads. AWS deployment must define whether tenant isolation is enforced by identity, stream partitioning, vector index strategy, metadata filters, or separate data stores.
* Cost controls: portfolio/demo usage should default to small service sizes, bounded stream retention, explicit vector database limits, disabled LLM calls unless intentionally enabled, and alarms for unexpected spend.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Premature AWS coupling makes the local prototype harder to run and test. | Keep Compose as the local baseline and add AWS boundaries through documentation, image publishing, and infrastructure skeletons before changing runtime dependencies. |
| Local file path assumptions leak into cloud configuration. | Replace `INPUT_FILE`, `OUTPUT_FILE`, `CHECKPOINT_FILE`, `METRICS_FILE`, and `VECTOR_STORE_DIR` with stream, state-store, telemetry, and vector database configuration as part of the AWS migration. |
| Vector store and embedding model mismatch causes search failures or poor retrieval. | Preserve and enforce model name and vector dimension metadata during any managed vector database migration. Reindex when changing models. |
| Event ordering and checkpoint semantics change when moving from JSONL polling to streams. | Define partition keys, consumer group behavior, retries, duplicate handling, and dead-letter policy before replacing local file transport. |
| Secrets leak through local files, logs, or CI output. | Keep `.env` untracked, leave placeholders in `.env.example`, move deployed secrets to Secrets Manager, and avoid logging secret values. |
| Observability gaps hide processing-agent failures after deployment. | Promote local status snapshots and structured logs into CloudWatch metrics, alarms, and dashboards before relying on the cloud deployment. |
| Cost surprises from streams, vector search, always-on containers, or LLM calls. | Start with demo-sized limits, explicit alarms, disabled LLM RAG by default, and a documented teardown path for non-production environments. |

## Suggested next AWS-readiness step

Create an infrastructure skeleton for the documented ECS boundary, including networking, IAM role names and permissions, SSM parameter names, Secrets Manager secret names, log groups, and placeholders for ECS services, without deploying the services or changing service source code.
