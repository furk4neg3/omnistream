import argparse
import json

from app.config import Settings
from app.embedder import LocalEmbedder
from app.vector_store import load_local_vector_store, search_local_vector_store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--tenant-id", default=None)
    args = parser.parse_args()

    settings = Settings()
    embedder = LocalEmbedder(settings.embedding_model_name)

    embeddings, records, manifest = load_local_vector_store(settings.vector_store_dir)
    query_embedding = embedder.encode([args.query])[0]

    results = search_local_vector_store(
        embeddings=embeddings,
        records=records,
        query_embedding=query_embedding,
        top_k=args.top_k,
        tenant_id=args.tenant_id,
    )

    print(json.dumps({"manifest": manifest, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()