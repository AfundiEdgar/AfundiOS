"""
Redis Cache Manager for AfundiOS

Provides caching for embeddings, LLM responses, vector search results, and conversations.
Supports both standalone Redis and Redis cluster configurations.
"""

import json
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass
import redis
from redis.exceptions import RedisError
from config import settings

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Configuration for cache TTL and key prefixes"""
    def __init__(self, settings):
        # TTL in seconds from settings
        self.embedding_ttl: int = settings.cache_embedding_ttl
        self.llm_response_ttl: int = settings.cache_llm_response_ttl
        self.vector_search_ttl: int = settings.cache_vector_search_ttl
        self.conversation_ttl: int = settings.cache_conversation_ttl
        
        # Key prefixes
        self.embedding_prefix: str = "embed:"
        self.llm_prefix: str = "llm:"
        self.vector_prefix: str = "vector:"
        self.conversation_prefix: str = "conv:"


class RedisCache:
    """Redis-based cache manager with fallback handling."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and settings.redis_enabled
        self.config = CacheConfig(settings)
        self._client: Optional[redis.Redis] = None
        
        if self.enabled:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Redis client with connection pooling."""
        try:
            if settings.redis_cluster_enabled:
                from rediscluster import RedisCluster
                startup_nodes = [
                    {"host": host.split(':')[0], "port": int(host.split(':')[1])} 
                    for host in settings.redis_cluster_nodes.split(',')
                ]
                self._client = RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                    password=settings.redis_password
                )
            else:
                self._client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    db=settings.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    connection_pool=redis.ConnectionPool(
                        host=settings.redis_host,
                        port=settings.redis_port,
                        password=settings.redis_password,
                        db=settings.redis_db,
                        max_connections=20
                    )
                )
            
            # Test connection
            self._client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self.enabled = False
            self._client = None
    
    def _generate_key(self, prefix: str, data: Union[str, Dict, List]) -> str:
        """Generate a consistent cache key from input data."""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        key_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{prefix}{key_hash}"
    
    def _safe_operation(self, operation_name: str, operation_func, *args, **kwargs) -> Any:
        """Execute Redis operation with error handling."""
        if not self.enabled or not self._client:
            return None
        
        try:
            return operation_func(*args, **kwargs)
        except RedisError as e:
            logger.warning(f"Redis {operation_name} failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Redis {operation_name}: {e}")
            return None
    
    # ================== Embedding Cache ==================
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        key = self._generate_key(self.config.embedding_prefix, text)
        result = self._safe_operation("get_embedding", self._client.get, key)
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in embedding cache for key: {key}")
        return None
    
    def set_embedding(self, text: str, embedding: List[float]) -> bool:
        """Cache embedding for text."""
        key = self._generate_key(self.config.embedding_prefix, text)
        value = json.dumps(embedding)
        
        result = self._safe_operation(
            "set_embedding", 
            self._client.setex, 
            key, 
            self.config.embedding_ttl, 
            value
        )
        return result is True
    
    # ================== LLM Response Cache ==================
    
    def get_llm_response(self, query: str, context: str, history: Optional[List[Tuple[str, str]]] = None) -> Optional[str]:
        """Get cached LLM response."""
        cache_data = {
            "query": query,
            "context": context,
            "history": history or []
        }
        key = self._generate_key(self.config.llm_prefix, cache_data)
        
        return self._safe_operation("get_llm_response", self._client.get, key)
    
    def set_llm_response(self, query: str, context: str, response: str, 
                        history: Optional[List[Tuple[str, str]]] = None) -> bool:
        """Cache LLM response."""
        cache_data = {
            "query": query,
            "context": context,
            "history": history or []
        }
        key = self._generate_key(self.config.llm_prefix, cache_data)
        
        result = self._safe_operation(
            "set_llm_response",
            self._client.setex,
            key,
            self.config.llm_response_ttl,
            response
        )
        return result is True
    
    # ================== Vector Search Cache ==================
    
    def get_vector_search(self, query_embedding: List[float], k: int) -> Optional[List[Dict]]:
        """Get cached vector search results."""
        cache_data = {
            "embedding": query_embedding,
            "k": k
        }
        key = self._generate_key(self.config.vector_prefix, cache_data)
        result = self._safe_operation("get_vector_search", self._client.get, key)
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in vector search cache for key: {key}")
        return None
    
    def set_vector_search(self, query_embedding: List[float], k: int, results: List[Dict]) -> bool:
        """Cache vector search results."""
        cache_data = {
            "embedding": query_embedding,
            "k": k
        }
        key = self._generate_key(self.config.vector_prefix, cache_data)
        value = json.dumps(results)
        
        result = self._safe_operation(
            "set_vector_search",
            self._client.setex,
            key,
            self.config.vector_search_ttl,
            value
        )
        return result is True
    
    # ================== Conversation Cache ==================
    
    def get_conversation(self, session_id: str) -> Optional[List[Dict]]:
        """Get conversation history from cache."""
        key = f"{self.config.conversation_prefix}{session_id}"
        result = self._safe_operation("get_conversation", self._client.get, key)
        
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in conversation cache for session: {session_id}")
        return None
    
    def set_conversation(self, session_id: str, messages: List[Dict]) -> bool:
        """Cache conversation history."""
        key = f"{self.config.conversation_prefix}{session_id}"
        value = json.dumps(messages)
        
        result = self._safe_operation(
            "set_conversation",
            self._client.setex,
            key,
            self.config.conversation_ttl,
            value
        )
        return result is True
    
    def delete_conversation(self, session_id: str) -> bool:
        """Delete conversation from cache."""
        key = f"{self.config.conversation_prefix}{session_id}"
        result = self._safe_operation("delete_conversation", self._client.delete, key)
        return result == 1
    
    def list_conversations(self) -> List[str]:
        """List all conversation session IDs."""
        pattern = f"{self.config.conversation_prefix}*"
        keys = self._safe_operation("list_conversations", self._client.keys, pattern)
        
        if keys:
            return [key.replace(self.config.conversation_prefix, "") for key in keys]
        return []
    
    # ================== Cache Management ==================
    
    def clear_cache(self, cache_type: Optional[str] = None) -> bool:
        """Clear cache by type or all caches."""
        if cache_type:
            pattern = f"{getattr(self.config, f'{cache_type}_prefix', cache_type)}*"
        else:
            pattern = "*"
        
        keys = self._safe_operation("clear_cache_keys", self._client.keys, pattern)
        if keys:
            result = self._safe_operation("clear_cache_delete", self._client.delete, *keys)
            logger.info(f"Cleared {result or 0} cache keys with pattern: {pattern}")
            return result is not None
        return True
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled or not self._client:
            return {"enabled": False}
        
        try:
            info = self._client.info()
            
            # Count keys by prefix
            key_counts = {}
            for prefix_attr in ['embedding_prefix', 'llm_prefix', 'vector_prefix', 'conversation_prefix']:
                prefix = getattr(self.config, prefix_attr)
                keys = self._client.keys(f"{prefix}*")
                key_counts[prefix_attr.replace('_prefix', '_keys')] = len(keys) if keys else 0
            
            return {
                "enabled": True,
                "connected": True,
                "memory_used": info.get('used_memory_human', 'Unknown'),
                "total_keys": info.get('db0', {}).get('keys', 0),
                "key_counts": key_counts,
                "redis_version": info.get('redis_version', 'Unknown')
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}


# Global cache instance
cache = RedisCache()


def get_cache() -> RedisCache:
    """Get the global cache instance."""
    return cache