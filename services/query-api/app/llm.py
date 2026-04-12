from typing import Any, Literal

from google import genai
from pydantic import BaseModel, Field, ValidationError


class CitationItem(BaseModel):
    chunk_id: str = Field(description="Chunk ID from the retrieved context.")
    ticket_id: str = Field(description="Ticket ID from the retrieved context.")
    reason: str = Field(
        description="Short explanation of why this citation supports the answer."
    )


class StructuredRagAnswer(BaseModel):
    answer: str = Field(
        description="Direct answer to the user's query based only on retrieved context."
    )
    short_summary: str = Field(description="One short summary sentence.")
    answer_status: Literal["grounded", "insufficient_context"]
    confidence: Literal["low", "medium", "high"]
    citations: list[CitationItem]


def build_context(results: list[dict[str, Any]], max_chunks: int, max_chars: int) -> str:
    sections: list[str] = []
    current_chars = 0

    for idx, result in enumerate(results[:max_chunks], start=1):
        metadata = result["metadata"]
        block = (
            f"[SOURCE {idx}]\n"
            f"ticket_id={result['ticket_id']}\n"
            f"chunk_id={result['chunk_id']}\n"
            f"severity={metadata['severity']}\n"
            f"product={metadata['product']}\n"
            f"customer_tier={metadata['customer_tier']}\n"
            f"timestamp={metadata['timestamp']}\n"
            f"text={result['text']}\n"
        )

        if current_chars + len(block) > max_chars:
            break

        sections.append(block)
        current_chars += len(block)

    return "\n\n".join(sections).strip()


def validate_citations(
    answer: StructuredRagAnswer, results: list[dict[str, Any]]
) -> StructuredRagAnswer:
    valid_pairs = {
        (item["chunk_id"], item["ticket_id"])
        for item in results
    }

    filtered_citations = []
    for citation in answer.citations:
        if (citation.chunk_id, citation.ticket_id) in valid_pairs:
            filtered_citations.append(citation)

    answer.citations = filtered_citations

    if answer.answer_status == "grounded" and not answer.citations:
        answer.answer_status = "insufficient_context"
        answer.confidence = "low"
        answer.short_summary = (
            "Model answer did not contain valid citations from retrieved context."
        )
        answer.answer = (
            "I found potentially relevant results, but I could not verify a grounded "
            "answer from the retrieved context."
        )

    return answer


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        max_context_chunks: int,
        max_context_chars: int,
        temperature: float,
        max_output_tokens: int,
    ) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.max_context_chunks = max_context_chunks
        self.max_context_chars = max_context_chars
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def _call_once(
        self,
        query: str,
        context: str,
        max_output_tokens: int,
    ) -> StructuredRagAnswer:
        prompt = f"""
User query:
{query}

Retrieved context:
{context}

Rules:
- Use only the retrieved context.
- Do not invent facts.
- If the context is insufficient, set answer_status to "insufficient_context".
- Every grounded answer must include citations that exactly match chunk_id and ticket_id values from the retrieved context.
- Do not cite anything that is not explicitly present above.
- Keep the answer under 120 words.
- Keep short_summary under 25 words.
- Use at most 3 citations.
""".strip()

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "system_instruction": (
                    "You are OmniStream, a retrieval-augmented support intelligence assistant. "
                    "Return only grounded, structured JSON answers."
                ),
                "response_mime_type": "application/json",
                "response_json_schema": StructuredRagAnswer.model_json_schema(),
                "temperature": self.temperature,
                "max_output_tokens": max_output_tokens,
            },
        )

        raw_text = getattr(response, "text", None)
        if not raw_text or not raw_text.strip():
            raise RuntimeError("Gemini returned an empty response body.")

        try:
            return StructuredRagAnswer.model_validate_json(raw_text)
        except ValidationError as e:
            preview = raw_text[:500]
            raise RuntimeError(
                f"Gemini returned invalid JSON. First 500 chars: {preview}"
            ) from e

    def answer(self, query: str, results: list[dict[str, Any]]) -> dict[str, Any]:
        context = build_context(
            results=results,
            max_chunks=self.max_context_chunks,
            max_chars=self.max_context_chars,
        )

        if not context:
            return {
                "answer": "I could not find enough relevant retrieved context to answer this query.",
                "short_summary": "No relevant retrieved tickets were found.",
                "answer_status": "insufficient_context",
                "confidence": "low",
                "citations": [],
            }

        last_error: Exception | None = None
        token_budgets = [
            self.max_output_tokens,
            max(self.max_output_tokens * 2, 1200),
        ]

        for token_budget in token_budgets:
            try:
                parsed = self._call_once(
                    query=query,
                    context=context,
                    max_output_tokens=token_budget,
                )
                validated = validate_citations(parsed, results)

                return {
                    "answer": validated.answer,
                    "short_summary": validated.short_summary,
                    "answer_status": validated.answer_status,
                    "confidence": validated.confidence,
                    "citations": [
                        citation.model_dump() for citation in validated.citations
                    ],
                }
            except Exception as e:
                last_error = e

        raise RuntimeError(f"Gemini structured output failed after retry: {last_error}")