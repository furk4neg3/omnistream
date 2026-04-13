import traceback
from functools import lru_cache
from time import perf_counter

from fastapi import APIRouter, FastAPI

from app.config import Settings, load_settings
from app.ingestion import build_chunk_records, transform_raw_to_enriched
from app.llm import GeminiClient
from app.models import (
    HealthResponse,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    RawEvent,
    Timing,
)
from app.rag import fallback_answer
from app.retrieval import QueryEngine


@lru_cache
def get_settings() -> Settings:
    return load_settings()


@lru_cache
def get_query_engine() -> QueryEngine:
    settings = get_settings()
    return QueryEngine(
        vector_store_dir=settings.vector_store_dir,
        embedding_model_name=settings.embedding_model_name,
    )


@lru_cache
def get_llm_client() -> GeminiClient | None:
    settings = get_settings()

    if not settings.enable_llm_rag:
        return None

    if not settings.gemini_api_key:
        return None

    return GeminiClient(
        api_key=settings.gemini_api_key,
        model_name=settings.llm_model_name,
        max_context_chunks=settings.max_context_chunks,
        max_context_chars=settings.max_context_chars,
        temperature=settings.llm_temperature,
        max_output_tokens=settings.llm_max_output_tokens,
    )


settings = get_settings()
print(f"Gemini configuration status: {settings.llm_ready_reason}")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    engine = get_query_engine()
    llm_client = get_llm_client()

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_version=settings.app_version,
        model_name=engine.manifest.get("model_name") or settings.embedding_model_name,
        record_count=engine.manifest.get("record_count", 0),
        embedding_dim=engine.manifest.get("embedding_dim", 0),
        vector_store_dir=settings.vector_store_dir,
        llm_enabled=llm_client is not None,
        llm_model_name=settings.llm_model_name if llm_client else None,
        llm_reason=settings.llm_ready_reason,
        llm_api_key_source=settings.gemini_api_key_source,
        env_files_checked=list(settings.env_files_checked),
    )


@router.post("/ingest", response_model=IngestResponse)
def ingest(event: RawEvent) -> IngestResponse:
    engine = get_query_engine()

    enriched_event = transform_raw_to_enriched(
        raw_event=event,
        settings=settings,
    )
    chunk_records = build_chunk_records(enriched_event)
    manifest = engine.ingest_chunk_records(chunk_records)

    return IngestResponse(
        status="ingested",
        event_id=enriched_event["event_id"],
        ticket_id=enriched_event["ticket_id"],
        tenant_id=enriched_event["tenant_id"],
        chunks_created=len(chunk_records),
        vector_record_count=manifest["record_count"],
        summary=enriched_event["metadata"]["summary"],
    )


@router.post("/search", response_model=QueryResponse)
def search(request: QueryRequest) -> QueryResponse:
    engine = get_query_engine()

    start = perf_counter()
    results = engine.search(
        query=request.query,
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        filters=request.filters,
    )
    total_ms = (perf_counter() - start) * 1000

    return QueryResponse(
        query=request.query,
        tenant_id=request.tenant_id,
        answer=None,
        short_summary=None,
        used_rag=False,
        answer_status="fallback",
        confidence=None,
        citations=[],
        results=results,
        timing_ms=Timing(
            retrieval=round(total_ms, 2),
            total=round(total_ms, 2),
        ),
    )


@router.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest) -> QueryResponse:
    engine = get_query_engine()
    llm_client = get_llm_client()

    total_start = perf_counter()

    retrieval_start = perf_counter()
    results = engine.search(
        query=request.query,
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        filters=request.filters,
    )
    retrieval_ms = (perf_counter() - retrieval_start) * 1000

    generation_start = perf_counter()

    if request.use_rag and llm_client is not None:
        try:
            answer_payload = llm_client.answer(request.query, results)
            used_rag = answer_payload["answer_status"] == "grounded"
        except Exception as e:
            print(f"Gemini RAG failed: {e}")
            traceback.print_exc()
            answer_payload = fallback_answer(request.query, results)
            used_rag = False
    else:
        answer_payload = fallback_answer(request.query, results)
        used_rag = False

    generation_ms = (perf_counter() - generation_start) * 1000
    total_ms = (perf_counter() - total_start) * 1000

    return QueryResponse(
        query=request.query,
        tenant_id=request.tenant_id,
        answer=answer_payload["answer"],
        short_summary=answer_payload["short_summary"],
        used_rag=used_rag,
        answer_status=answer_payload["answer_status"],
        confidence=answer_payload["confidence"],
        citations=answer_payload["citations"],
        results=results,
        timing_ms=Timing(
            retrieval=round(retrieval_ms, 2),
            generation=round(generation_ms, 2),
            total=round(total_ms, 2),
        ),
    )


app.include_router(router)