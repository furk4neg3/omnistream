# OmniStream

![Status: Work in Progress](https://img.shields.io/badge/Status-Work_in_Progress-orange.svg)
![Architecture: Microservices](https://img.shields.io/badge/Architecture-Microservices-blue.svg)
![Deployment: Cloud-Native](https://img.shields.io/badge/Deployment-Cloud--Native-lightgrey.svg)

**A Real-Time, Multi-Modal RAG & Agentic Workflow Engine with Automated MLOps**

OmniStream is an enterprise-grade, cloud-native platform designed to ingest real-time data streams (text, audio, image metadata), process them using a fleet of autonomous AI agents, and route the refined data into a continuously updated vector database for Retrieval-Augmented Generation (RAG). 

Crucially, the system features a self-healing MLOps pipeline that monitors its own embedding models for data drift and automatically triggers fine-tuning pipelines when performance degrades, ensuring high accuracy over time without manual intervention.

---

## Key Features

* **Real-Time Data Streaming:** Event-driven ingestion pipeline handling live continuous data rather than static batches.
* **Agentic Orchestration:** Specialized AI agents for classifying, routing, processing, and summarizing incoming data streams.
* **Dynamic Multi-Modal RAG:** Continuously updated vector stores backed by caching layers for low-latency, high-accuracy generation.
* **Automated Drift Detection & Retraining:** Built-in statistical monitoring of incoming distributions against training data, triggering automated fine-tuning and shadow deployments.
* **Infrastructure as Code (IaC):** Entirely provisioned via Terraform for reproducible, scalable, and secure deployments.

---

## Architecture Design (AWS blueprint)

OmniStream is decoupled into four highly scalable layers:

### 1. Infrastructure & Deployment Layer
* **Provisioning:** Terraform
* **Container Orchestration:** Amazon EKS (Kubernetes)
* **CI/CD:** GitHub Actions (Automated testing, containerization, and deployment)

### 2. Data Ingestion & Streaming Layer
* **Stream Processing:** Amazon MSK (Managed Kafka) / Amazon Kinesis
* **Event Triggers:** AWS Lambda (Serverless)
* **Object Storage:** Amazon S3

### 3. AI Core & Orchestration Layer
* **Agent Framework:** LangChain / AutoGen (Python-based microservices)
* **Vector Database:** Milvus (on EKS) / Amazon OpenSearch Serverless
* **Caching Layer:** Amazon ElastiCache (Redis) to reduce LLM API latency and costs

### 4. MLOps & Model Monitoring Layer
* **Model Hosting:** Amazon SageMaker
* **Experiment Tracking:** MLflow (Deployed on EKS)
* **Pipeline Orchestration:** Apache Airflow / Scheduled Cron
* **Self-Healing Loop:** Automated drift detection triggering SageMaker Training Pipelines and shadow testing.

---

## Current Project Status: Active Development

OmniStream is currently a **Work in Progress**. The architecture is defined, and core microservices are actively being built and integrated. 

**Current Focus Areas:**
- [ ] Provisioning base AWS infrastructure via Terraform.
- [ ] Setting up the MSK/Kinesis data ingestion topics.
- [ ] Developing the Router and Processing Agent logic.
- [ ] Implementing the MLflow tracking server and data drift baseline metrics.

### AWS Migration Readiness

The local prototype is ready enough to begin AWS-readiness work, but no AWS deployment is implemented yet. See [docs/aws-readiness.md](docs/aws-readiness.md) for the first bounded migration-readiness artifact mapping the current Compose services, local state, config, CI, and API surfaces to future AWS resources and gaps.

---

## Local Docker Compose

The local stack is intentionally file-backed so it maps cleanly to managed services later:

* `producer` appends raw support events to a JSONL file, analogous to a future Kinesis/MSK producer.
* `processing-agent` polls that append-only file, checkpoints progress, enriches/chunks events, embeds them, and updates the local vector store incrementally.
* `query-api` serves `/health`, `/status`, `/search`, `/ask`, and `/ingest` over HTTP using the same vector store mount.

### Prerequisites

* Docker with Compose v2
* Optional: `jq` for prettier verification output
* Optional: `GEMINI_API_KEY` or `GOOGLE_API_KEY` when intentionally enabling grounded LLM answers

The first run may take a few minutes because the images install Python dependencies. Compose uses a lightweight deterministic local embedding backend by default so the stack can run without model downloads.

### Local Configuration

Create a local `.env` from the committed template before adding overrides:

```bash
cp .env.example .env
```

`.env` is ignored and is only for local secrets and machine-specific settings. Keep real API keys and cloud credentials out of git; `.env.example` must contain placeholders only. See `docs/configuration.md` for the local variables and their future AWS configuration or secrets-store mapping.

### Automated Tests

Run the local automated test suite from the repository root:

```bash
make test
```

The test runner scopes `PYTHONPATH` per service so each Python service can use its own `app` package namespace.

The Gemini smoke check is manual-only and is not part of automated tests:

```bash
PYTHONPATH=services/query-api python services/query-api/scripts/check_gemini.py
```

It requires the query-api dependencies plus `GEMINI_API_KEY` or `GOOGLE_API_KEY`, and may call the Gemini API.

### Start the Core Stack

```bash
docker compose up --build
```

This starts:

* `query-api` on `http://localhost:8000`
* `processing-agent`, polling `.local/omnistream/events/events.jsonl`

Shared local state is mounted at `.local/omnistream`:

* `events/events.jsonl` for raw events
* `enriched/enriched_events.jsonl` for processed event output
* `state/processing-checkpoint.json` for the consumer checkpoint
* `state/processing-agent-metrics.json` and `state/producer-metrics.json` for local service status snapshots
* `vector_store/` for embeddings, records, and manifest files
* `model-cache/` for downloaded embedding model files when optional model dependencies are enabled

### Generate Events

The producer is a controlled one-shot service under the `producer` profile:

```bash
docker compose --profile producer run --rm producer
```

Override event volume and rate as needed:

```bash
MAX_EVENTS=25 EVENTS_PER_SECOND=5 docker compose --profile producer run --rm producer
```

The processing-agent should pick up those events automatically and update the vector store without restarting the query-api.

By default the producer emits a mix of `support_ticket` and `customer_chat_message` raw events. Limit the mix with `EVENT_TYPES` when you want deterministic demos:

```bash
EVENT_TYPES=customer_chat_message MAX_EVENTS=3 docker compose --profile producer run --rm producer
```

The processing-agent routes each raw event before enrichment:

* `support_ticket` records keep their ticket ID as the canonical support record ID.
* `customer_chat_message` records use `conversation_id` as the canonical support record ID and `message_id` as the source payload ID.
* Enriched chunks include route metadata such as `event_type`, `record_id`, `source_payload_id`, and `router_label`.

### Embedding Backend

Compose defaults to `hashing-local-v1`, a deterministic local embedding backend that keeps container builds small and still records the embedding model name in the vector store manifest. The query-api and processing-agent will fail loudly if they point at a vector store built with a different model name.

To opt into `sentence-transformers` inside Docker, rebuild with the optional dependency and set the Compose-specific model variable:

```bash
INSTALL_SENTENCE_TRANSFORMERS=true OMNISTREAM_EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2 docker compose up --build
```

When switching embedding models, reset `.local/omnistream/vector_store` and `.local/omnistream/state` so the checkpoint and stored embeddings stay consistent.

### Verify Health And Search

```bash
curl -s http://localhost:8000/health | jq
```

```bash
curl -s http://localhost:8000/metrics | jq
```

```bash
curl -s http://localhost:8000/status | jq
```

`/status` combines query-api uptime, vector store summary, and the latest producer and processing-agent status snapshots. Missing snapshots are reported with `available: false`. Running dependency snapshots also include `fresh` and `age_seconds`; if a running snapshot is older than `DEPENDENCY_STATUS_MAX_AGE_SECONDS` (default `30` in Compose), `/status` reports that dependency as stale. Completed producer snapshots remain valid because the producer is a one-shot service.

```bash
curl -s http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"What issue is affecting mobile checkout?","tenant_id":"acme","top_k":5}' | jq
```

```bash
curl -s http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"query":"What are the most important auth issues?","tenant_id":"acme","top_k":5,"use_rag":false}' | jq
```

Use Compose status and logs for operational visibility:

```bash
docker compose ps
docker compose logs -f processing-agent
docker compose logs -f query-api
cat .local/omnistream/state/processing-agent-metrics.json | jq
cat .local/omnistream/state/producer-metrics.json | jq
```

### Optional LLM RAG

LLM-backed RAG is opt-in. Without a shell or `.env` override, `ENABLE_LLM_RAG=false`, so `/ask` returns the safe local fallback. To enable grounded LLM answers, set both the feature flag and a real provider key in your shell or untracked `.env`:

```bash
ENABLE_LLM_RAG=true docker compose up --build
```

### Stop Or Reset

```bash
docker compose down
```

Compose preserves local data in `.local/omnistream`. Remove that directory when you want a fresh event log, checkpoint, vector store, and model cache.
