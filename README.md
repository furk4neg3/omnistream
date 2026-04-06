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

---

## Getting Started (Draft)

*(Instructions will be updated as the CI/CD pipeline and IaC configurations are finalized).*

### Prerequisites
* AWS CLI configured with appropriate IAM permissions
* Terraform `>= 1.5.0`
* Docker & Kubernetes (kubectl, helm)
* Python `>= 3.10`

### Local Development Setup
```bash
# Clone the repository
git clone [https://github.com/yourusername/OmniStream.git](https://github.com/yourusername/OmniStream.git)
cd OmniStream

# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt