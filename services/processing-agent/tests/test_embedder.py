import numpy as np

from app.embedder import LocalEmbedder


def test_hashing_embedder_is_deterministic_and_normalized():
    embedder = LocalEmbedder("hashing-local-v1")

    first = embedder.encode(["mobile checkout timeout", "auth login failure"])
    second = embedder.encode(["mobile checkout timeout", "auth login failure"])

    assert first.shape == (2, 384)
    assert np.allclose(first, second)
    assert np.allclose(np.linalg.norm(first, axis=1), [1.0, 1.0])
