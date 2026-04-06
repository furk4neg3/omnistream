# OmniStream v1

## Project goal
Build a cloud-native system that ingests real-time support ticket events, processes them, stores embeddings in a vector database, and answers user questions with a RAG API.

## Why this use case
Support tickets are easy to simulate, easy to evaluate, and naturally fit streaming + RAG + routing.

## Users
- internal support engineers
- product ops teams
- incident response teams

## Input data
Incoming JSON events with:
- ticket_id
- timestamp
- product
- severity
- title
- body
- customer_tier

## System behavior
1. Receive ticket events in real time
2. Clean and enrich the text
3. Generate embeddings
4. Store chunks + metadata + vectors
5. Let users search and ask questions over the indexed data

## v1 components
- event producer
- streaming layer
- indexer service
- vector store
- query API
- basic retrieval pipeline

## Success metrics
- ingestion latency under 5 seconds
- searchable indexed tickets
- RAG answers with sources
- infrastructure provisioned with Terraform
- services containerized and deployable

## Out of scope for v1
- audio ingestion
- image ingestion
- multi-agent collaboration loops
- automated retraining
- drift-triggered deployment
- advanced UI

## Demo story
A simulated stream of support tickets arrives in real time. The system indexes them automatically. A user asks:
“Which high-severity payment issues happened this week?”
The API returns an answer with retrieved source chunks.