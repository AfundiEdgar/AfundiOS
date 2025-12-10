from typing import List, Dict, Tuple
from config import settings

# Lazy import to avoid dependency issues if cross-encoder not installed
_reranker = None


def _get_reranker():
    """Lazy load the cross-encoder model."""
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            # Using a fast, efficient cross-encoder
            _reranker = CrossEncoder("cross-encoder/mmarco-MiniLMv2-L12-H384-v1", max_length=512)
        except ImportError:
            raise ImportError(
                "sentence-transformers package required for reranking. "
                "Install with: pip install sentence-transformers"
            )
    return _reranker


def rerank_results(
    query: str,
    chunks: List[Dict],
    k: int = 5,
    threshold: float = 0.0,
) -> List[Tuple[Dict, float]]:
    """
    Rerank retrieved chunks using a cross-encoder model.

    Args:
        query: The user's query
        chunks: List of retrieved chunks with 'text' and 'id' keys
        k: Number of top results to return
        threshold: Minimum reranking score to include a result

    Returns:
        List of tuples (chunk, score) sorted by score descending
    """
    if not chunks:
        return []

    try:
        reranker = _get_reranker()

        # Prepare pairs for cross-encoder: [(query, text), ...]
        pairs = [(query, chunk.get("text", "")) for chunk in chunks]

        # Get relevance scores
        scores = reranker.predict(pairs)

        # Create tuples and filter by threshold
        ranked = [
            (chunk, float(score))
            for chunk, score in zip(chunks, scores)
            if float(score) >= threshold
        ]

        # Sort by score descending and return top k
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:k]

    except Exception as e:
        # If reranking fails, fall back to original order with scores
        import logging
        logging.warning(f"Reranking failed: {e}. Returning original results.")
        return [(chunk, 0.0) for chunk in chunks[:k]]


def rerank_and_filter(
    query: str,
    chunks: List[Dict],
    k: int = 5,
    enable_rerank: bool = True,
    rerank_threshold: float = 0.0,
) -> List[Dict]:
    """
    Optionally rerank results and return top k chunks.

    Args:
        query: The user's query
        chunks: Retrieved chunks from vector search
        k: Number of results to return
        enable_rerank: Whether to apply reranking
        rerank_threshold: Minimum score threshold for reranked results

    Returns:
        List of top k chunks (with reranking if enabled)
    """
    if not enable_rerank:
        # No reranking, just return top k
        return chunks[:k]

    # Apply reranking
    ranked = rerank_results(query=query, chunks=chunks, k=k, threshold=rerank_threshold)

    # Convert back to original format (drop scores)
    return [chunk for chunk, _ in ranked]
