"""
Cached Embedder that wraps the existing embedder with Redis caching.
"""

import logging
from typing import List, Optional
from .embedder import Embedder
from .cache import get_cache

logger = logging.getLogger(__name__)


class CachedEmbedder:
    """Embedder wrapper that adds Redis caching for embedding generation."""
    
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.cache = get_cache()
        
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a query text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        # Try to get from cache first
        cached_embedding = self.cache.get_embedding(text)
        if cached_embedding is not None:
            logger.debug(f"Cache hit for query embedding: {text[:50]}...")
            return cached_embedding
        
        # Generate embedding using the original embedder
        logger.debug(f"Cache miss for query embedding: {text[:50]}...")
        embedding = self.embedder.embed_query(text)
        
        # Cache the result
        if embedding:
            self.cache.set_embedding(text, embedding)
        
        return embedding
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents with caching.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding lists
        """
        embeddings = []
        cache_misses = []
        miss_indices = []
        
        # Check cache for each document
        for i, text in enumerate(texts):
            cached_embedding = self.cache.get_embedding(text)
            if cached_embedding is not None:
                logger.debug(f"Cache hit for document embedding: {text[:50]}...")
                embeddings.append(cached_embedding)
            else:
                logger.debug(f"Cache miss for document embedding: {text[:50]}...")
                embeddings.append(None)  # Placeholder
                cache_misses.append(text)
                miss_indices.append(i)
        
        # Generate embeddings for cache misses
        if cache_misses:
            logger.info(f"Generating {len(cache_misses)} embeddings (cache misses)")
            new_embeddings = self.embedder.embed_documents(cache_misses)
            
            # Fill in the placeholders and cache the results
            for j, embedding in enumerate(new_embeddings):
                original_index = miss_indices[j]
                embeddings[original_index] = embedding
                
                # Cache the new embedding
                if embedding:
                    self.cache.set_embedding(cache_misses[j], embedding)
        else:
            logger.info("All embeddings found in cache")
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.embedder.get_embedding_dimension()
    
    def clear_cache(self) -> bool:
        """Clear the embedding cache."""
        return self.cache.clear_cache('embedding')
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_cache_stats()


def create_cached_embedder() -> CachedEmbedder:
    """Create a cached embedder instance."""
    from .embedder import embedder  # Import the global embedder instance
    return CachedEmbedder(embedder)