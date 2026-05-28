from functools import lru_cache
from time import perf_counter

from fastapi import APIRouter, FastAPI, Request

from app.config import Settings, load_settings
from app.ingestion import build_chunk_records, transform_raw_to_enriched
from app.llm import GeminiClient
from app.models import (
    HealthResponse,
    IngestResponse,
    MetricsResponse,
    QueryRequest,
    QueryResponse,
    RawEvent,
    Timing,
)
from app.observability import log_event, runtime_metrics
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
log_event(
    "query_api_configured",
    app_name=settings.app_name,
    app_version=settings.app_version,
    vector_store_dir=settings.vector_store_dir,
    embedding_model_name=settings.embedding_model_name,
    llm_ready_reason=settings.llm_ready_reason,
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
router = APIRouter()


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        runtime_metrics.increment("request_errors_total")
        log_event(
            "request_failed",
            level="error",
            method=request.method,
            path=request.url.path,
            error_type=type(e).__name__,
            error=str(e),
        )
        raise
    finally:
        duration_ms = (perf_counter() - start) * 1000
        runtime_metrics.increment("requests_total")
        runtime_metrics.increment(f"http_{status_code}_responses_total")
        runtime_metrics.observe("http_request_ms", duration_ms)
        log_event(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
        )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    engine = get_query_engine()
    engine.reload_if_changed()
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


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    engine = get_query_engine()
    engine.reload_if_changed()
    snapshot = runtime_metrics.snapshot()

    return MetricsResponse(
        service="query-api",
        app_name=settings.app_name,
        app_version=settings.app_version,
        uptime_seconds=snapshot["uptime_seconds"],
        started_at=snapshot["started_at"],
        counters=snapshot["counters"],
        timings_ms=snapshot["timings_ms"],
        vector_store={
            "model_name": engine.manifest.get("model_name") or settings.embedding_model_name,
            "record_count": engine.manifest.get("record_count", 0),
            "embedding_dim": engine.manifest.get("embedding_dim", 0),
            "vector_store_dir": settings.vector_store_dir,
        },
    )


@router.post("/ingest", response_model=IngestResponse)
def ingest(event: RawEvent) -> IngestResponse:
    engine = get_query_engine()
    start = perf_counter()

    enriched_event = transform_raw_to_enriched(
        raw_event=event,
        settings=settings,
    )
    chunk_records = build_chunk_records(enriched_event)
    manifest = engine.ingest_chunk_records(chunk_records)
    ingest_ms = (perf_counter() - start) * 1000

    runtime_metrics.increment("ingest_requests_total")
    runtime_metrics.increment("ingest_events_total")
    runtime_metrics.increment("ingest_chunks_total", len(chunk_records))
    runtime_metrics.observe("ingest_ms", ingest_ms)
    log_event(
        "ingest_completed",
        event_id=enriched_event["event_id"],
        ticket_id=enriched_event["ticket_id"],
        tenant_id=enriched_event["tenant_id"],
        chunks_created=len(chunk_records),
        vector_record_count=manifest["record_count"],
        duration_ms=round(ingest_ms, 2),
    )

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
    runtime_metrics.increment("search_requests_total")
    runtime_metrics.increment("search_results_total", len(results))
    runtime_metrics.observe("retrieval_ms", total_ms)
    log_event(
        "search_completed",
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        results_returned=len(results),
        retrieval_ms=round(total_ms, 2),
    )

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
            runtime_metrics.increment("llm_errors_total")
            log_event(
                "rag_generation_failed",
                level="error",
                tenant_id=request.tenant_id,
                error_type=type(e).__name__,
                error=str(e),
            )
            answer_payload = fallback_answer(request.query, results)
            used_rag = False
    else:
        answer_payload = fallback_answer(request.query, results)
        used_rag = False

    generation_ms = (perf_counter() - generation_start) * 1000
    total_ms = (perf_counter() - total_start) * 1000
    runtime_metrics.increment("ask_requests_total")
    runtime_metrics.increment("ask_results_total", len(results))
    runtime_metrics.increment("ask_rag_grounded_total" if used_rag else "ask_fallback_total")
    runtime_metrics.observe("retrieval_ms", retrieval_ms)
    runtime_metrics.observe("generation_ms", generation_ms)
    runtime_metrics.observe("ask_total_ms", total_ms)
    log_event(
        "ask_completed",
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        results_returned=len(results),
        used_rag=used_rag,
        answer_status=answer_payload["answer_status"],
        retrieval_ms=round(retrieval_ms, 2),
        generation_ms=round(generation_ms, 2),
        total_ms=round(total_ms, 2),
    )

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
