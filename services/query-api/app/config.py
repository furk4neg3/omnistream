import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "OmniStream Query API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    vector_store_dir: str = os.getenv("VECTOR_STORE_DIR", "../indexer/local_vector_store")
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")