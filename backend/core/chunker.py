from typing import List


def simple_chunk(text: str, max_tokens: int = 512) -> List[str]:
    words = text.split()
    chunks = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= max_tokens:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks
