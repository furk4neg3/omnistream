# ECS Task Definition Templates

This directory contains static ECS task-definition templates for OmniStream's first always-on ECS service set:

* `query-api`
* `processing-agent`

These files are AWS-readiness artifacts only. They do not deploy OmniStream, register task definitions, create ECS services, or create any AWS resources. Docker Compose remains the implemented local runtime.

## Layout

```text
infra/ecs/
  README.md
  task-definitions/
    query-api.taskdef.json
    processing-agent.taskdef.json
```

## Relationship To The ECS-First Path

The templates follow the ECS-first direction in `docs/adr/0001-initial-aws-runtime-target.md` and the service boundary in `docs/ecs-deployment-design.md`. They model only the two long-running containers that would be part of the first always-on ECS runtime:

* `query-api` as the future ALB-facing API task on container port `8000`.
* `processing-agent` as the future internal worker task.

The `producer` service is intentionally deferred. It is a one-shot/demo Compose profile workload today, not part of the first always-on ECS service set. If needed later, it should get its own explicitly designed one-shot task template rather than being added to this always-on set.

## Assumptions

| Service | Fargate CPU | Fargate memory | Notes |
| --- | --- | --- | --- |
| `query-api` | `256` CPU units | `512` MiB | Matches the low end of the current ECS design guidance for the FastAPI service. |
| `processing-agent` | `512` CPU units | `1024` MiB | Matches the current worker guidance for polling, enrichment, chunking, embedding, and vector-store updates. |

Both templates use:

* `requiresCompatibilities: ["FARGATE"]`
* `networkMode: "awsvpc"`
* separate execution-role and application task-role placeholders
* immutable image placeholder strings that follow `docs/container-images.md`
* CloudWatch `awslogs` configuration placeholders
* existing container commands from the Dockerfiles
* existing container health-check behavior

## Placeholders

The JSON files intentionally contain placeholder strings. Replace them in a future deployment step before registering task definitions.

Common placeholders include:

* `${AWS_ACCOUNT_ID}`
* `${AWS_REGION}`
* `${OMNISTREAM_ENVIRONMENT}`
* `${OMNISTREAM_IMAGE_REGISTRY}`
* `${OMNISTREAM_IMAGE_NAMESPACE}`
* `${APP_VERSION}`
* `${GIT_SHA_SHORT}`
* `${SECRET_RANDOM_SUFFIX}`

The image placeholders match the current image contract:

```text
${OMNISTREAM_IMAGE_REGISTRY}/${OMNISTREAM_IMAGE_NAMESPACE}/query-api:${APP_VERSION}-${GIT_SHA_SHORT}
${OMNISTREAM_IMAGE_REGISTRY}/${OMNISTREAM_IMAGE_NAMESPACE}/processing-agent:${APP_VERSION}-${GIT_SHA_SHORT}
```

The log group, role, and secret ARNs are placeholders only. Do not commit real AWS account IDs, role ARNs, registry URLs, secret ARNs, API keys, or credentials in these templates.

## Configuration And Secrets

Non-secret environment variables are included as literal readiness defaults based on Docker Compose and `docs/configuration.md`.

`query-api` includes placeholders only for the optional LLM provider keys:

* `GOOGLE_API_KEY`
* `GEMINI_API_KEY`

`processing-agent` does not currently require runtime secrets, so its template does not include secret placeholders.

In a later deployment implementation, non-secret values can move to SSM Parameter Store and secret values can move to Secrets Manager. That wiring is intentionally not implemented here.

## Local File-Backed State Limitations

The templates preserve the current local path names under `/workspace/local-data` only as temporary container-local placeholders. These paths are not durable cloud storage and are not shared between independent ECS tasks.

Before these templates can represent a production-ready ECS deployment, OmniStream still needs cloud-safe replacements for:

* raw JSONL input files
* enriched JSONL output files
* checkpoint files
* metrics and status snapshot files
* the local vector-store directory
* optional model-cache directories

The current local file-backed paths are useful for Compose and first-shape readiness, but they should be replaced or deliberately adapted before relying on ECS.

## Non-Goals

This directory does not:

* deploy OmniStream
* register ECS task definitions
* create ECS services, clusters, load balancers, target groups, VPCs, subnets, IAM roles, log groups, SSM parameters, Secrets Manager secrets, ECR repositories, streams, buckets, tables, or vector stores
* add Terraform resources
* require AWS credentials
* introduce AWS SDK or runtime dependencies
* change service source code, API contracts, Dockerfiles, Docker Compose behavior, or local image build behavior

## Verification

These templates can be checked locally without AWS credentials:

```bash
python3 -m json.tool infra/ecs/task-definitions/query-api.taskdef.json >/dev/null
python3 -m json.tool infra/ecs/task-definitions/processing-agent.taskdef.json >/dev/null
```
