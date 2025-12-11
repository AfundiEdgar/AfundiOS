"""
Cached LLM that wraps the existing LLM with Redis caching.
"""

import logging
from typing import List, Tuple, Optional
from .llm import LLM
from .cache import get_cache

logger = logging.getLogger(__name__)


class CachedLLM:
    """LLM wrapper that adds Redis caching for responses."""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.cache = get_cache()
        
    def generate_response(self, query: str, context: str = "", 
                         history: Optional[List[Tuple[str, str]]] = None) -> str:
        """
        Generate response with caching.
        
        Args:
            query: User query
            context: Retrieved context
            history: Conversation history
            
        Returns:
            Generated response
        """
        # Try to get from cache first
        cached_response = self.cache.get_llm_response(query, context, history)
        if cached_response is not None:
            logger.debug(f"Cache hit for LLM response: {query[:50]}...")
            return cached_response
        
        # Generate response using the original LLM
        logger.debug(f"Cache miss for LLM response: {query[:50]}...")
        response = self.llm.generate_response(query, context, history)
        
        # Cache the result
        if response:
            self.cache.set_llm_response(query, context, response, history)
        
        return response
    
    def stream_response(self, query: str, context: str = "", 
                       history: Optional[List[Tuple[str, str]]] = None):
        """
        Stream response - not cached as it's meant for real-time interaction.
        """
        # For streaming, we don't cache as users expect real-time responses
        return self.llm.stream_response(query, context, history)
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.llm.get_model_name()
    
    def clear_cache(self) -> bool:
        """Clear the LLM response cache."""
        return self.cache.clear_cache('llm')
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_cache_stats()


def create_cached_llm() -> CachedLLM:
    """Create a cached LLM instance."""
    from .llm import llm  # Import the global LLM instance
    return CachedLLM(llm)