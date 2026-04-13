def chunk_text(text: str, chunk_size_words: int, chunk_overlap_words: int) -> list[dict]:
    words = text.split()

    if not words:
        return []

    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be greater than 0")

    if chunk_overlap_words < 0:
        raise ValueError("chunk_overlap_words cannot be negative")

    if chunk_overlap_words >= chunk_size_words:
        raise ValueError("chunk_overlap_words must be smaller than chunk_size_words")

    chunks = []
    start = 0
    chunk_index = 0
    step = chunk_size_words - chunk_overlap_words

    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        chunk_text_value = " ".join(chunk_words)

        chunks.append(
            {
                "chunk_index": chunk_index,
                "text": chunk_text_value,
                "token_count": len(chunk_words),
            }
        )

        chunk_index += 1
        start += step

    return chunks