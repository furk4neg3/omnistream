from typing import Sequence

import numpy as np


class LocalEmbedder:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependency: sentence-transformers.\n"
                "Install processing-agent dependencies with:\n"
                "pip install -r services/processing-agent/requirements.txt\n"
                "Or activate the correct virtual environment before running the agent."
            ) from exc

        self.model_name = model_name
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