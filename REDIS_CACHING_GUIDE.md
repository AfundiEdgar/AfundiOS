# Redis Caching Implementation Guide

## Overview

This guide explains how to implement and use Redis caching in AfundiOS to significantly improve performance. The caching system provides multiple layers of optimization:

- **Embedding Cache**: Cache expensive embedding generation operations
- **LLM Response Cache**: Cache responses for identical queries and contexts
- **Vector Search Cache**: Cache vector database search results
- **Conversation Cache**: Store conversation history in Redis for session management

## Quick Start

### 1. Install Redis

**Option A: Automatic Setup (Recommended)**
```bash
# Run the setup script
./scripts/setup_redis.sh
```

**Option B: Docker (Production/Containers)**
```bash
# Start Redis with Docker Compose
docker-compose -f docker-compose.redis.yml up -d

# Check if Redis is running
docker exec afundios-redis redis-cli ping
```

**Option C: Manual Installation**
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y redis-server

# macOS with Homebrew
brew install redis

# Start Redis
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS
```

### 2. Install Python Dependencies

```bash
pip install redis redis-py-cluster
# or if using requirements.txt
pip install -r requirements.txt
```

### 3. Configure Environment

Update your `.env` file:
```env
# Redis Cache Configuration
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Cache TTL Configuration (in seconds)
CACHE_EMBEDDING_TTL=3600      # 1 hour
CACHE_LLM_RESPONSE_TTL=1800   # 30 minutes
CACHE_VECTOR_SEARCH_TTL=600   # 10 minutes
CACHE_CONVERSATION_TTL=86400  # 24 hours
```

### 4. Start Your Application

```bash
# Backend
cd backend && python main.py

# Frontend (in separate terminal)
cd frontend && streamlit run app.py
```

## Architecture

### Cache Layers

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  Embedding      │───▶│  Vector Search  │
└─────────────────┘    │  Cache          │    │  Cache          │
                       └─────────────────┘    └─────────────────┘
                                ▲                        │
                                │                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LLM Response   │◀───│  Cache Manager  │◀───│  Retrieved      │
│  Cache          │    │  (Redis)        │    │  Context        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │  Conversation   │
                       │  Cache          │
                       └─────────────────┘
```

### Component Integration

1. **CachedEmbedder**: Wraps the original embedder with caching
2. **CachedLLM**: Wraps the LLM with response caching  
3. **CachedRetriever**: Adds caching to vector search operations
4. **RedisCache**: Core cache manager with Redis operations

## Usage Examples

### Basic Usage (Automatic)

The caching is transparent - just use your existing code:

```python
# This will automatically use cached embeddings and responses
from backend.api.query import query_documents

response = await query_documents(
    query="What are the main features?",
    k=5
)
```

### Direct Cache Usage

```python
from backend.core.cache import get_cache

cache = get_cache()

# Manual cache operations
embedding = cache.get_embedding("sample text")
if embedding is None:
    # Generate and cache embedding
    embedding = generate_embedding("sample text")
    cache.set_embedding("sample text", embedding)
```

### Cache Management via API

```bash
# Check cache health
curl http://localhost:8000/cache/health

# Get cache statistics
curl http://localhost:8000/cache/stats

# Clear specific cache type
curl -X DELETE http://localhost:8000/cache/clear/embedding

# Clear all caches
curl -X DELETE http://localhost:8000/cache/clear
```

## Configuration Options

### Redis Connection

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_ENABLED` | `true` | Enable/disable Redis caching |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_PASSWORD` | (empty) | Redis password (if auth enabled) |
| `REDIS_DB` | `0` | Redis database number |

### Redis Cluster (High Availability)

```env
REDIS_CLUSTER_ENABLED=true
REDIS_CLUSTER_NODES=redis1:7000,redis2:7001,redis3:7002
```

### Cache TTL Settings

| Cache Type | Variable | Default | Purpose |
|------------|----------|---------|---------|
| Embeddings | `CACHE_EMBEDDING_TTL` | 3600s (1h) | Embedding vectors rarely change |
| LLM Responses | `CACHE_LLM_RESPONSE_TTL` | 1800s (30m) | Balance freshness vs performance |
| Vector Search | `CACHE_VECTOR_SEARCH_TTL` | 600s (10m) | Search results change frequently |
| Conversations | `CACHE_CONVERSATION_TTL` | 86400s (24h) | Session management |

## Performance Benefits

### Before Redis Caching
```
Query: "What is machine learning?"
├─ Generate embedding: 150ms
├─ Vector search: 50ms  
├─ LLM response: 2000ms
└─ Total: ~2200ms
```

### With Redis Caching  
```
Query: "What is machine learning?" (cached)
├─ Get embedding from cache: 5ms
├─ Get vector results from cache: 2ms
├─ Get LLM response from cache: 3ms  
└─ Total: ~10ms (220x faster!)
```

### Cache Hit Rates (Typical)
- **Embeddings**: 80-90% (same queries repeated)
- **Vector Search**: 60-70% (similar queries)  
- **LLM Responses**: 40-60% (exact matches)
- **Overall Performance**: 5-20x improvement

## Monitoring and Debugging

### Cache Statistics

```python
from backend.core.cache import get_cache

cache = get_cache()
stats = cache.get_cache_stats()
print(stats)
```

Output:
```json
{
  "enabled": true,
  "connected": true,
  "memory_used": "12.5M",
  "total_keys": 1247,
  "key_counts": {
    "embedding_keys": 432,
    "llm_keys": 123,
    "vector_keys": 89,
    "conversation_keys": 15
  },
  "redis_version": "7.2.0"
}
```

### Redis Commander UI

If using Docker setup, access Redis Commander at:
- URL: http://localhost:8081
- Features: Browse keys, monitor memory, execute commands

### Logging

Enable debug logging in your `.env`:
```env
LOG_LEVEL=debug
```

You'll see cache hit/miss logs:
```
DEBUG - Cache hit for query embedding: What is machine learning?...
DEBUG - Cache miss for vector search: Tell me about AI...
```

## Production Considerations

### Redis High Availability

For production, consider Redis cluster or sentinel setup:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  redis-master:
    image: redis:7.2-alpine
    command: redis-server --appendonly yes
    
  redis-replica:
    image: redis:7.2-alpine  
    command: redis-server --replicaof redis-master 6379
    depends_on:
      - redis-master
```

### Security

1. **Enable Redis AUTH**:
```bash
# In redis.conf
requirepass your-secure-password
```

2. **Update .env**:
```env
REDIS_PASSWORD=your-secure-password
```

3. **Network Security**:
- Bind Redis to private networks only
- Use firewall rules to restrict access
- Consider Redis over TLS for encrypted connections

### Memory Management

Monitor Redis memory usage:

```bash
# Check memory info
redis-cli info memory

# Set memory limit
redis-cli config set maxmemory 1gb
redis-cli config set maxmemory-policy allkeys-lru
```

### Backup and Persistence

Redis is configured for persistence by default:
- **RDB**: Point-in-time snapshots
- **AOF**: Append-only file for durability

## Troubleshooting

### Common Issues

**1. Redis Connection Failed**
```bash
# Check if Redis is running
redis-cli ping

# Check logs
sudo journalctl -u redis-server -f
```

**2. Cache Not Working**
- Verify `REDIS_ENABLED=true` in `.env`
- Check Redis connection with `curl http://localhost:8000/cache/health`
- Enable debug logging to see cache operations

**3. Memory Issues**
```bash
# Check Redis memory usage
redis-cli info memory

# Clear specific cache type
curl -X DELETE http://localhost:8000/cache/clear/embedding
```

**4. Performance Not Improved**
- Check cache hit rates in logs
- Verify TTL settings aren't too low
- Monitor for cache eviction due to memory pressure

### Recovery Steps

1. **Reset All Caches**:
```bash
curl -X DELETE http://localhost:8000/cache/clear
```

2. **Restart Redis**:
```bash
sudo systemctl restart redis-server
# or
docker-compose -f docker-compose.redis.yml restart
```

3. **Disable Caching Temporarily**:
```env
REDIS_ENABLED=false
```

## Integration with Existing Code

The Redis caching is designed to be a drop-in enhancement. Your existing code will automatically benefit from caching without changes.

### Before (Original Code)
```python
# backend/api/query.py
from backend.core.embedder import embed_query
from backend.core.retriever import retrieve_relevant_chunks
from backend.core.llm import generate_response

# This uses original components
result = retrieve_relevant_chunks(query, k=5)
```

### After (With Caching)
The same code now uses cached versions automatically through the import system.

Need help with implementation? Check the cache health endpoint or review the logs for debugging information.

---

For more advanced configuration and troubleshooting, see the [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md).