from functools import lru_cache
from time import perf_counter

from fastapi import APIRouter, FastAPI

from app.config import Settings
from app.models import HealthResponse, QueryRequest, QueryResponse, Timing
from app.rag import synthesize_answer
from app.retrieval import QueryEngine


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_query_engine() -> QueryEngine:
    settings = get_settings()
    return QueryEngine(
        vector_store_dir=settings.vector_store_dir,
        embedding_model_name=settings.embedding_model_name,
    )


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    engine = get_query_engine()
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_version=settings.app_version,
        model_name=engine.manifest["model_name"],
        record_count=engine.manifest["record_count"],
        embedding_dim=engine.manifest["embedding_dim"],
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
        used_rag=False,
        results=results,
        timing_ms=Timing(
            retrieval=round(total_ms, 2),
            total=round(total_ms, 2),
        ),
    )


@router.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest) -> QueryResponse:
    engine = get_query_engine()

    start = perf_counter()

    retrieval_start = perf_counter()
    results = engine.search(
        query=request.query,
        tenant_id=request.tenant_id,
        top_k=request.top_k,
        filters=request.filters,
    )
    retrieval_ms = (perf_counter() - retrieval_start) * 1000

    generation_start = perf_counter()
    answer = synthesize_answer(request.query, results)
    generation_ms = (perf_counter() - generation_start) * 1000

    total_ms = (perf_counter() - start) * 1000

    return QueryResponse(
        query=request.query,
        tenant_id=request.tenant_id,
        answer=answer,
        used_rag=True,
        results=results,
        timing_ms=Timing(
            retrieval=round(retrieval_ms, 2),
            generation=round(generation_ms, 2),
            total=round(total_ms, 2),
        ),
    )


app.include_router(router)