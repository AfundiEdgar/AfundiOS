"""
Cache management API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from backend.core.cache import get_cache

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheStatsResponse(BaseModel):
    enabled: bool
    connected: Optional[bool] = None
    memory_used: Optional[str] = None
    total_keys: Optional[int] = None
    key_counts: Optional[Dict[str, int]] = None
    redis_version: Optional[str] = None
    error: Optional[str] = None


class CacheOperationResponse(BaseModel):
    success: bool
    message: str


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get Redis cache statistics and health information."""
    cache = get_cache()
    stats = cache.get_cache_stats()
    return CacheStatsResponse(**stats)


@router.delete("/clear", response_model=CacheOperationResponse)
async def clear_all_cache():
    """Clear all cache entries."""
    cache = get_cache()
    
    if not cache.enabled:
        raise HTTPException(status_code=503, detail="Redis cache is not enabled")
    
    try:
        success = cache.clear_cache()
        if success:
            return CacheOperationResponse(
                success=True,
                message="All cache entries cleared successfully"
            )
        else:
            return CacheOperationResponse(
                success=False,
                message="Failed to clear cache entries"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.delete("/clear/{cache_type}", response_model=CacheOperationResponse)
async def clear_cache_by_type(cache_type: str):
    """
    Clear cache entries by type.
    
    Args:
        cache_type: Type of cache to clear (embedding, llm, vector, conversation)
    """
    cache = get_cache()
    
    if not cache.enabled:
        raise HTTPException(status_code=503, detail="Redis cache is not enabled")
    
    valid_types = ['embedding', 'llm', 'vector', 'conversation']
    if cache_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cache type. Must be one of: {', '.join(valid_types)}"
        )
    
    try:
        success = cache.clear_cache(cache_type)
        if success:
            return CacheOperationResponse(
                success=True,
                message=f"{cache_type.title()} cache cleared successfully"
            )
        else:
            return CacheOperationResponse(
                success=False,
                message=f"Failed to clear {cache_type} cache"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing {cache_type} cache: {str(e)}"
        )


@router.get("/health")
async def cache_health():
    """Check Redis cache health."""
    cache = get_cache()
    
    if not cache.enabled:
        return {"status": "disabled", "message": "Redis cache is disabled"}
    
    stats = cache.get_cache_stats()
    
    if stats.get("connected"):
        return {
            "status": "healthy",
            "message": "Redis cache is running",
            "version": stats.get("redis_version", "Unknown")
        }
    else:
        return {
            "status": "unhealthy",
            "message": "Redis cache is not connected",
            "error": stats.get("error", "Unknown error")
        }