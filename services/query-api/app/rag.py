def synthesize_answer(query: str, results: list[dict]) -> str:
    if not results:
        return "No relevant tickets were found for this query."

    top_results = results[:3]

    summary_lines = [f"Query: {query}", "", "Top relevant findings:"]
    for idx, result in enumerate(top_results, start=1):
        metadata = result["metadata"]
        summary_lines.append(
            f"{idx}. [{result['ticket_id']}] "
            f"{metadata['severity']} {metadata['product']} issue: "
            f"{result['text']}"
        )

    return "\n".join(summary_lines)