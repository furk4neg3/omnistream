import hashlib
import re
from typing import Sequence

import numpy as np


HASHING_DIMENSION = 384
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


def uses_hashing_backend(model_name: str) -> bool:
    return model_name == "hashing-local-v1" or model_name.startswith("hashing:")


class HashingEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def encode(self, texts: Sequence[str], **_: object) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype="float32")

        embeddings = np.zeros((len(texts), HASHING_DIMENSION), dtype="float32")
        for row, text in enumerate(texts):
            for token in TOKEN_PATTERN.findall(text.lower()):
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                index = int.from_bytes(digest[:4], "little") % HASHING_DIMENSION
                sign = 1.0 if digest[4] & 1 else -1.0
                embeddings[row, index] += sign

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms


class LocalEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        if uses_hashing_backend(model_name):
            self.model = HashingEmbedder(model_name)
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                f"Embedding model '{model_name}' requires sentence-transformers.\n"
                "Use EMBEDDING_MODEL_NAME=hashing-local-v1 for the lightweight local backend, "
                "or install processing-agent dependencies with:\n"
                "pip install -r services/processing-agent/requirements.txt"
            ) from exc

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype="float32")

        embeddings = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype("float32")

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return embeddings / norms
