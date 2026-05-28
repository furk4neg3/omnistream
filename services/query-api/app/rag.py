from typing import Any


def fallback_answer(query: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {
            "answer": "I could not find enough relevant retrieved context to answer this query.",
            "short_summary": "No relevant retrieved support records were found.",
            "answer_status": "insufficient_context",
            "confidence": "low",
            "citations": [],
        }

    top_results = results[:3]
    citations = []

    lines = ["Top relevant findings:"]
    for idx, result in enumerate(top_results, start=1):
        metadata = result["metadata"]
        record_label = metadata.get("event_type") or metadata.get("source") or "support_record"
        lines.append(
            f"{idx}. {record_label} {result['ticket_id']} "
            f"({metadata['severity']} / {metadata['product']}): "
            f"{result['text']}"
        )
        citations.append(
            {
                "chunk_id": result["chunk_id"],
                "ticket_id": result["ticket_id"],
                "reason": "Fallback answer used this retrieved chunk as supporting evidence.",
            }
        )

    return {
        "answer": "\n".join(lines),
        "short_summary": f"Fallback summary built from {len(top_results)} retrieved chunks.",
        "answer_status": "fallback",
        "confidence": "low",
        "citations": citations,
    }
