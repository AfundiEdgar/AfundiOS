"""
Cached Retriever that wraps the existing retriever with Redis caching.
"""

import logging
from typing import List, Dict
from .cache import get_cache
from .cached_embedder import create_cached_embedder

logger = logging.getLogger(__name__)


class CachedRetriever:
    """Retriever wrapper that adds Redis caching for vector search results."""
    
    def __init__(self):
        self.cache = get_cache()
        self.cached_embedder = create_cached_embedder()
        
        # Import here to avoid circular imports
        from .retriever import vector_store
        from .reranker import rerank_and_filter
        self.vector_store = vector_store
        self.rerank_and_filter = rerank_and_filter
    
    def retrieve_relevant_chunks(
        self,
        query: str,
        k: int = 5,
        enable_rerank: bool = False,
        rerank_threshold: float = 0.0,
    ) -> List[Dict]:
        """
        Retrieve relevant chunks with caching.
        
        Args:
            query: The user's query
            k: Number of results to return
            enable_rerank: Whether to use cross-encoder reranking
            rerank_threshold: Minimum reranking score threshold
            
        Returns:
            List of top k chunks, optionally reranked
        """
        # Generate cache key based on query parameters
        cache_key_data = {
            "query": query,
            "k": k,
            "enable_rerank": enable_rerank,
            "rerank_threshold": rerank_threshold if enable_rerank else None
        }
        
        # Get query embedding (cached)
        q_emb = self.cached_embedder.embed_query(query)
        
        # Try to get results from cache
        cache_key_data["embedding"] = q_emb  # Include embedding in cache key
        cached_results = self.cache.get_vector_search(q_emb, k)
        
        if cached_results is not None:
            logger.debug(f"Cache hit for vector search: {query[:50]}...")
            return cached_results
        
        logger.debug(f"Cache miss for vector search: {query[:50]}...")
        
        # Get more results from vector search if reranking is enabled
        search_k = k * 3 if enable_rerank else k
        results = self.vector_store.search(q_emb, k=search_k)
        
        chunks = [
            {
                "id": _id,
                "text": text,
                "metadata": meta or {},
            }
            for _id, text, meta in results
        ]
        
        # Apply optional reranking
        if enable_rerank and chunks:
            chunks = self.rerank_and_filter(
                query=query,
                chunks=chunks,
                k=k,
                enable_rerank=True,
                rerank_threshold=rerank_threshold,
            )
        else:
            chunks = chunks[:k]
        
        # Cache the results
        if chunks:
            self.cache.set_vector_search(q_emb, k, chunks)
        
        return chunks
    
    def clear_cache(self) -> bool:
        """Clear the vector search cache."""
        return self.cache.clear_cache('vector')
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_cache_stats()


# Global cached retriever instance
cached_retriever = CachedRetriever()


def retrieve_relevant_chunks(
    query: str,
    k: int = 5,
    enable_rerank: bool = False,
    rerank_threshold: float = 0.0,
) -> List[Dict]:
    """
    Cached version of retrieve_relevant_chunks.
    
    This function maintains the same interface as the original function
    but adds Redis caching for improved performance.
    """
    return cached_retriever.retrieve_relevant_chunks(
        query=query,
        k=k,
        enable_rerank=enable_rerank,
        rerank_threshold=rerank_threshold
    )