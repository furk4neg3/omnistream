import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

CANDIDATE_ENV_FILES = (
    Path.cwd() / ".env",
    SERVICE_ROOT / ".env",
    REPO_ROOT / ".env",
)


def _clean_env_value(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def resolve_env(name: str, default: str | None = None) -> tuple[str | None, str | None]:
    process_value = _clean_env_value(os.getenv(name))
    if process_value is not None:
        return process_value, "process_env"

    for env_file in CANDIDATE_ENV_FILES:
        if not env_file.exists():
            continue

        file_value = _clean_env_value(dotenv_values(env_file).get(name))
        if file_value is not None:
            return file_value, str(env_file)

    return default, None


def env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


def resolve_gemini_api_key() -> tuple[str | None, str | None]:
    precedence = (
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
    )

    for name in precedence:
        value = _clean_env_value(os.getenv(name))
        if value is not None:
            return value, "process_env"

    for env_file in CANDIDATE_ENV_FILES:
        if not env_file.exists():
            continue

        values = dotenv_values(env_file)
        for name in precedence:
            value = _clean_env_value(values.get(name))
            if value is not None:
                return value, str(env_file)

    return None, None


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    vector_store_dir: str
    embedding_model_name: str
    processing_agent_metrics_file: str
    producer_metrics_file: str
    dependency_status_max_age_seconds: int

    enable_llm_rag: bool
    llm_model_name: str
    gemini_api_key: str | None
    gemini_api_key_source: str | None

    max_context_chunks: int
    max_context_chars: int
    llm_temperature: float
    llm_max_output_tokens: int

    chunk_size_words: int
    chunk_overlap_words: int
    schema_version: str
    processing_version: str

    env_files_checked: tuple[str, ...]

    @property
    def llm_ready_reason(self) -> str:
        if not self.enable_llm_rag:
            return "LLM RAG is disabled because ENABLE_LLM_RAG=false."

        if not self.gemini_api_key:
            return (
                "No Gemini API key was found. Checked process environment first, then .env files. "
                "Set GEMINI_API_KEY or GOOGLE_API_KEY."
            )

        if self.gemini_api_key_source == "process_env":
            return "Gemini API key loaded from the process environment."

        return f"Gemini API key loaded from {self.gemini_api_key_source}."


def load_settings() -> Settings:
    app_name, _ = resolve_env("APP_NAME", "OmniStream Query API")
    app_version, _ = resolve_env("APP_VERSION", "0.1.0")
    vector_store_dir, _ = resolve_env(
        "VECTOR_STORE_DIR",
        str(REPO_ROOT / "services" / "indexer" / "local_vector_store"),
    )
    embedding_model_name, _ = resolve_env(
        "EMBEDDING_MODEL_NAME",
        "all-MiniLM-L6-v2",
    )
    processing_agent_metrics_file, _ = resolve_env(
        "PROCESSING_AGENT_METRICS_FILE",
        str(REPO_ROOT / ".local" / "omnistream" / "state" / "processing-agent-metrics.json"),
    )
    producer_metrics_file, _ = resolve_env(
        "PRODUCER_METRICS_FILE",
        str(REPO_ROOT / ".local" / "omnistream" / "state" / "producer-metrics.json"),
    )
    dependency_status_max_age_seconds_raw, _ = resolve_env(
        "DEPENDENCY_STATUS_MAX_AGE_SECONDS",
        "30",
    )

    enable_llm_rag_raw, _ = resolve_env("ENABLE_LLM_RAG", "true")
    llm_model_name, _ = resolve_env("LLM_MODEL_NAME", "gemini-3-flash-preview")
    gemini_api_key, gemini_api_key_source = resolve_gemini_api_key()

    max_context_chunks_raw, _ = resolve_env("MAX_CONTEXT_CHUNKS", "5")
    max_context_chars_raw, _ = resolve_env("MAX_CONTEXT_CHARS", "6000")
    llm_temperature_raw, _ = resolve_env("LLM_TEMPERATURE", "0.2")
    llm_max_output_tokens_raw, _ = resolve_env("LLM_MAX_OUTPUT_TOKENS", "400")

    chunk_size_words_raw, _ = resolve_env("CHUNK_SIZE_WORDS", "80")
    chunk_overlap_words_raw, _ = resolve_env("CHUNK_OVERLAP_WORDS", "20")
    schema_version, _ = resolve_env("SCHEMA_VERSION", "v1")
    processing_version, _ = resolve_env("PROCESSING_VERSION", "v1")

    return Settings(
        app_name=app_name or "OmniStream Query API",
        app_version=app_version or "0.1.0",
        vector_store_dir=vector_store_dir
        or str(REPO_ROOT / "services" / "indexer" / "local_vector_store"),
        embedding_model_name=embedding_model_name or "all-MiniLM-L6-v2",
        processing_agent_metrics_file=processing_agent_metrics_file
        or str(REPO_ROOT / ".local" / "omnistream" / "state" / "processing-agent-metrics.json"),
        producer_metrics_file=producer_metrics_file
        or str(REPO_ROOT / ".local" / "omnistream" / "state" / "producer-metrics.json"),
        dependency_status_max_age_seconds=int(dependency_status_max_age_seconds_raw or "30"),
        enable_llm_rag=env_bool(enable_llm_rag_raw, True),
        llm_model_name=llm_model_name or "gemini-3-flash-preview",
        gemini_api_key=gemini_api_key,
        gemini_api_key_source=gemini_api_key_source,
        max_context_chunks=int(max_context_chunks_raw or "5"),
        max_context_chars=int(max_context_chars_raw or "6000"),
        llm_temperature=float(llm_temperature_raw or "0.2"),
        llm_max_output_tokens=int(llm_max_output_tokens_raw or "400"),
        chunk_size_words=int(chunk_size_words_raw or "80"),
        chunk_overlap_words=int(chunk_overlap_words_raw or "20"),
        schema_version=schema_version or "v1",
        processing_version=processing_version or "v1",
        env_files_checked=tuple(str(path) for path in CANDIDATE_ENV_FILES),
    )
