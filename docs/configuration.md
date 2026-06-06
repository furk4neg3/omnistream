# Configuration

OmniStream loads local configuration from process environment variables and, for local development, a root `.env` file. Commit `.env.example` as the safe template, copy it to `.env` for local overrides, and never commit real API keys or cloud credentials.

```bash
cp .env.example .env
```

## Secret Handling

`GEMINI_API_KEY` and `GOOGLE_API_KEY` are optional local secrets for grounded LLM answers. Keep placeholder values in `.env.example`; put real values only in your untracked `.env` or your shell environment. `ENABLE_LLM_RAG=false` is the safe default, so `/ask` uses the local fallback unless LLM RAG is explicitly enabled.

For AWS deployment, store non-secret configuration separately from secrets:

| Local variable | Local default | Future AWS home | Notes |
| --- | --- | --- | --- |
| `APP_NAME` | `OmniStream Query API` | SSM Parameter Store | Service display name for query-api. |
| `APP_VERSION` | `0.1.0` | Container image tag or SSM Parameter Store | Keep aligned with release metadata. |
| `QUERY_API_PORT` | `8000` | ECS/EKS service and load balancer config | Local host port only; container still listens on `8000`. |
| `TENANT_ID` | `acme` | SSM Parameter Store | Local demo tenant. Production tenant routing should come from event payloads or identity context. |
| `EVENT_TYPES` | `support_ticket,customer_chat_message` | SSM Parameter Store | Producer demo event mix. |
| `EVENTS_PER_SECOND` | `1` | SSM Parameter Store | Producer throttle for local/demo runs. |
| `MAX_EVENTS` | `10` | SSM Parameter Store | Producer one-shot event count for local/demo runs. |
| `POLL_INTERVAL_SECONDS` | `1.0` | SSM Parameter Store | Processing-agent polling interval until the local file source is replaced by a managed stream consumer. |
| `LOOP_FOREVER` | `true` | SSM Parameter Store | Local processing-agent loop control. |
| `BATCH_SIZE` | `32` | SSM Parameter Store | Processing-agent batch size. |
| `CHUNK_SIZE_WORDS` | `80` | SSM Parameter Store | Enrichment chunking parameter shared by processing-agent and query-api. |
| `CHUNK_OVERLAP_WORDS` | `20` | SSM Parameter Store | Enrichment chunk overlap parameter shared by processing-agent and query-api. |
| `SCHEMA_VERSION` | `v1` | SSM Parameter Store | Version stamp written into enriched records. |
| `PROCESSING_VERSION` | `v1` | SSM Parameter Store | Processing version stamp written into enriched records. |
| `DEPENDENCY_STATUS_MAX_AGE_SECONDS` | `30` | SSM Parameter Store | Query-api staleness threshold for local status snapshots. |
| `INSTALL_SENTENCE_TRANSFORMERS` | `false` | Build pipeline variable | Docker build toggle for optional model dependency installation. |
| `OMNISTREAM_EMBEDDING_MODEL_NAME` | `hashing-local-v1` | SSM Parameter Store | Compose maps this to service-level `EMBEDDING_MODEL_NAME`. Reset the local vector store when changing models. |
| `ENABLE_LLM_RAG` | `false` | SSM Parameter Store | Feature flag; must be explicitly true before the query-api calls an LLM. |
| `LLM_MODEL_NAME` | `gemini-3-flash-preview` | SSM Parameter Store | Non-secret model selection. |
| `GEMINI_API_KEY` | placeholder only | AWS Secrets Manager | Optional provider key for local/future LLM RAG. |
| `GOOGLE_API_KEY` | placeholder only | AWS Secrets Manager | Alternate provider key; query-api checks `GOOGLE_API_KEY` before `GEMINI_API_KEY`. |
| `MAX_CONTEXT_CHUNKS` | `5` | SSM Parameter Store | Query-api context assembly limit. |
| `MAX_CONTEXT_CHARS` | `6000` | SSM Parameter Store | Query-api context character budget. |
| `LLM_TEMPERATURE` | `0.2` | SSM Parameter Store | Query-api generation setting. |
| `LLM_MAX_OUTPUT_TOKENS` | `400` | SSM Parameter Store | Query-api generation setting. |
| `AWS_REGION` | `us-east-1` | AWS runtime environment | Region for future managed services. |
| `KINESIS_STREAM_NAME` | `omnistream-raw-events` | SSM Parameter Store | Future stream name when the producer writes to Kinesis. |

Local file paths such as `VECTOR_STORE_DIR`, `INPUT_FILE`, `OUTPUT_FILE`, `CHECKPOINT_FILE`, and `METRICS_FILE` are wired by Docker Compose to `.local/omnistream`. In AWS, replace those local mounts with managed storage, stream offsets, service metrics, and vector database configuration instead of carrying over host paths.

Avoid storing long-lived AWS access keys in `.env`. Prefer local AWS profiles for development and task or pod IAM roles for deployed services.
