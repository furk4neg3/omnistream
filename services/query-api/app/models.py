from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Filters(BaseModel):
    severity: list[str] | None = None
    product: list[str] | None = None
    customer_tier: list[str] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    tenant_id: str
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Filters | None = None
    use_rag: bool = True


class SearchResultMetadata(BaseModel):
    tenant_id: str
    severity: str
    product: str
    timestamp: datetime
    customer_tier: str
    source: str
    event_type: str | None = None
    record_id: str | None = None
    source_payload_id: str | None = None
    router_label: str | None = None


class SearchResult(BaseModel):
    chunk_id: str
    ticket_id: str
    score: float
    text: str
    metadata: SearchResultMetadata


class AnswerCitation(BaseModel):
    chunk_id: str
    ticket_id: str
    reason: str


class Timing(BaseModel):
    retrieval: float
    generation: float | None = None
    total: float


class QueryResponse(BaseModel):
    query: str
    tenant_id: str
    answer: str | None = None
    short_summary: str | None = None
    used_rag: bool
    answer_status: Literal["grounded", "insufficient_context", "fallback"]
    confidence: Literal["low", "medium", "high"] | None = None
    citations: list[AnswerCitation] = Field(default_factory=list)
    results: list[SearchResult]
    timing_ms: Timing


class SupportTicketPayload(BaseModel):
    ticket_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    severity: Literal["low", "medium", "high", "critical"]
    product: str = Field(min_length=1)
    customer_tier: Literal["free", "pro", "enterprise"]
    language: str = "en"
    tags: list[str] = Field(default_factory=list)


class CustomerChatMessagePayload(BaseModel):
    conversation_id: str = Field(min_length=1)
    message_id: str = Field(min_length=1)
    sender: Literal["customer", "agent", "system"]
    message: str = Field(min_length=1)
    severity: Literal["low", "medium", "high", "critical"]
    product: str = Field(min_length=1)
    customer_tier: Literal["free", "pro", "enterprise"]
    sentiment: Literal["negative", "neutral", "positive"] = "neutral"
    language: str = "en"
    tags: list[str] = Field(default_factory=list)


RawEventPayload = SupportTicketPayload


class RawEvent(BaseModel):
    event_id: str = Field(min_length=1)
    source: Literal["support_ticket", "customer_chat_message"]
    timestamp: datetime
    tenant_id: str = Field(min_length=1)
    payload: SupportTicketPayload | CustomerChatMessagePayload

    @model_validator(mode="after")
    def payload_matches_source(self) -> "RawEvent":
        if self.source == "support_ticket" and not isinstance(self.payload, SupportTicketPayload):
            raise ValueError("support_ticket events require a support ticket payload")

        if self.source == "customer_chat_message" and not isinstance(
            self.payload,
            CustomerChatMessagePayload,
        ):
            raise ValueError("customer_chat_message events require a chat message payload")

        return self


class IngestResponse(BaseModel):
    status: Literal["ingested"]
    event_id: str
    ticket_id: str
    tenant_id: str
    chunks_created: int
    vector_record_count: int
    summary: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    model_name: str
    record_count: int
    embedding_dim: int
    vector_store_dir: str | None = None
    llm_enabled: bool
    llm_model_name: str | None = None
    llm_reason: str | None = None
    llm_api_key_source: str | None = None
    env_files_checked: list[str] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    service: str
    app_name: str
    app_version: str
    uptime_seconds: float
    started_at: str
    counters: dict[str, int]
    timings_ms: dict[str, dict[str, float | int]]
    vector_store: dict[str, Any]


class VectorStoreSummary(BaseModel):
    model_name: str
    record_count: int
    embedding_dim: int
    vector_store_dir: str


class DependencyStatus(BaseModel):
    available: bool
    path: str
    reason: str | None = None
    fresh: bool | None = None
    age_seconds: float | None = None
    payload: dict[str, Any] | None = None


class StatusResponse(BaseModel):
    service: Literal["query-api"]
    status: Literal["ok"]
    app_name: str
    app_version: str
    started_at: str
    uptime_seconds: float
    counters: dict[str, int]
    timings_ms: dict[str, dict[str, float | int]]
    vector_store: VectorStoreSummary
    processing_agent: DependencyStatus
    producer: DependencyStatus
