from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
    citations: list[AnswerCitation] = []
    results: list[SearchResult]
    timing_ms: Timing


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    model_name: str
    record_count: int
    embedding_dim: int
    llm_enabled: bool
    llm_model_name: str | None = None

    # Optional debug fields so /health works both with and without them
    llm_reason: str | None = None
    llm_api_key_source: str | None = None
    env_files_checked: list[str] = []