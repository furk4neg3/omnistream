import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=True)


def env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "OmniStream Query API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    vector_store_dir: str = os.getenv(
        "VECTOR_STORE_DIR",
        str(REPO_ROOT / "services" / "indexer" / "local_vector_store"),
    )
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "all-MiniLM-L6-v2",
    )

    enable_llm_rag: bool = env_bool("ENABLE_LLM_RAG", "true")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    llm_model_name: str = os.getenv("LLM_MODEL_NAME", "gemini-3-flash-preview")

    max_context_chunks: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "5"))
    max_context_chars: int = int(os.getenv("MAX_CONTEXT_CHARS", "6000"))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_output_tokens: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "800"))