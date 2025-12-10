from typing import List
from config import settings

# This is a stub. Replace with real OpenAI embeddings or another provider.
def embed_texts(texts: List[str]) -> List[List[float]]:
    # Deterministic fake embeddings for skeleton purposes
    return [[float((hash(t) % 1000))] for t in texts]


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]
