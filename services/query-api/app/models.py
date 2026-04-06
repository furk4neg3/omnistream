from datetime import datetime

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


class Timing(BaseModel):
    retrieval: float
    generation: float | None = None
    total: float


class QueryResponse(BaseModel):
    query: str
    tenant_id: str
    answer: str | None = None
    used_rag: bool
    results: list[SearchResult]
    timing_ms: Timing


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    model_name: str
    record_count: int
    embedding_dim: int