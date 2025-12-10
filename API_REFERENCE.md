# API Reference

Complete documentation for all AfundiOS REST API endpoints.

## Base URL

```
http://localhost:8000  # Development
https://api.example.com  # Production
```

## Authentication

Most endpoints don't require authentication. Some sensitive endpoints may require API keys (configure in `.env`).

## Table of Contents

1. [Health & Status](#health--status)
2. [Ingestion](#ingestion)
3. [Query](#query)
4. [Vector Store](#vector-store)
5. [Configuration](#configuration)
6. [Statistics](#statistics)

---

## Health & Status

### Health Check

Check if backend is healthy and responsive.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0"
}
```

**Status Codes**:
- `200 OK` - Backend is healthy
- `503 Service Unavailable` - Backend is down or unhealthy

**Example**:
```bash
curl http://localhost:8000/health
```

---

## Ingestion

### Ingest File

Upload and ingest a document.

**Endpoint**: `POST /ingest`

**Request**:
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.pdf" \
  -F "metadata={\"source\": \"user\"}"
```

**Request Body**:
- `file` (required): File to ingest (PDF, TXT, MD, DOCX, XLSX)
- `metadata` (optional): JSON metadata
- `chunk_size` (optional): Override default chunk size
- `chunk_overlap` (optional): Overlap between chunks

**Response**:
```json
{
  "success": true,
  "document_id": "doc_12345",
  "filename": "document.pdf",
  "file_size": 102400,
  "chunks": 5,
  "preview": "This is the first 200 characters of the document...",
  "processing_time": 2.5
}
```

**Status Codes**:
- `200 OK` - File ingested successfully
- `400 Bad Request` - Invalid file format or metadata
- `413 Payload Too Large` - File exceeds size limit (default 100MB)
- `500 Internal Server Error` - Processing error

**Supported Formats**:
- `.pdf` - PDF documents
- `.txt` - Plain text
- `.md` - Markdown
- `.docx` - Word documents
- `.xlsx` - Excel spreadsheets
- URLs - Web pages
- YouTube links - Video transcripts

**Example**:
```bash
# Upload PDF
curl -X POST http://localhost:8000/ingest \
  -F "file=@paper.pdf" \
  -F "metadata={\"source\": \"arxiv\", \"author\": \"Smith\"}"

# Expected response:
# {
#   "success": true,
#   "document_id": "doc_12345",
#   "chunks": 10,
#   "preview": "Abstract: This paper presents..."
# }
```

### Ingest URL

Ingest content from a web URL.

**Endpoint**: `POST /ingest_url`

**Request**:
```bash
curl -X POST http://localhost:8000/ingest_url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

**Request Body**:
```json
{
  "url": "https://example.com/article",
  "metadata": {
    "source": "web",
    "category": "news"
  }
}
```

**Response**:
```json
{
  "success": true,
  "document_id": "doc_12346",
  "url": "https://example.com/article",
  "title": "Article Title",
  "chunks": 3,
  "preview": "Article content preview...",
  "processing_time": 1.8
}
```

**Status Codes**:
- `200 OK` - URL ingested successfully
- `400 Bad Request` - Invalid URL
- `404 Not Found` - URL not reachable
- `500 Internal Server Error` - Processing error

**Example**:
```bash
curl -X POST http://localhost:8000/ingest_url \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Machine_learning",
    "metadata": {"source": "wikipedia"}
  }'
```

### Ingest YouTube

Ingest video transcript from YouTube.

**Endpoint**: `POST /ingest_youtube`

**Request**:
```bash
curl -X POST http://localhost:8000/ingest_youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
```

**Request Body**:
```json
{
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "metadata": {
    "source": "youtube",
    "channel": "ExampleChannel"
  }
}
```

**Response**:
```json
{
  "success": true,
  "document_id": "doc_12347",
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "duration": 180,
  "chunks": 4,
  "preview": "Transcript: Welcome to this video...",
  "processing_time": 3.2
}
```

**Status Codes**:
- `200 OK` - Video ingested successfully
- `400 Bad Request` - Invalid video URL
- `404 Not Found` - Video not found
- `500 Internal Server Error` - Transcript extraction failed

**Example**:
```bash
curl -X POST http://localhost:8000/ingest_youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtu.be/9bZkp7q19f0"}'
```

---

## Query

### Query Documents

Search for relevant documents and get LLM-generated response.

**Endpoint**: `POST /query`

**Request**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

**Request Body**:
```json
{
  "question": "What is machine learning?",
  "top_k": 5,
  "rerank": true,
  "context_length": 2000
}
```

**Parameters**:
- `question` (required): User's question
- `top_k` (optional): Number of documents to retrieve (default: 5)
- `rerank` (optional): Whether to rerank results (default: true)
- `context_length` (optional): Max context to send to LLM (default: 2000)

**Response**:
```json
{
  "success": true,
  "question": "What is machine learning?",
  "answer": "Machine learning is a subset of artificial intelligence...",
  "sources": [
    {
      "document_id": "doc_12345",
      "filename": "paper.pdf",
      "excerpt": "ML algorithms learn patterns from data...",
      "relevance_score": 0.95,
      "page": 1
    }
  ],
  "retrieval_time": 0.5,
  "generation_time": 2.1,
  "total_time": 2.6
}
```

**Status Codes**:
- `200 OK` - Query successful
- `400 Bad Request` - Invalid question
- `503 Service Unavailable` - Vector store or LLM unavailable
- `500 Internal Server Error` - Processing error

**Example**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does neural networks work?",
    "top_k": 3
  }'
```

---

## Vector Store

### Get Vector Store Info

Get information about the current vector store.

**Endpoint**: `GET /vector_store/info`

**Response**:
```json
{
  "type": "chroma",
  "path": "backend/data/vector_store",
  "documents": 42,
  "vectors": 128,
  "dimensions": 384,
  "size_mb": 15.3,
  "created_at": "2024-01-01T12:00:00Z",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**Status Codes**:
- `200 OK` - Success
- `500 Internal Server Error` - Vector store error

**Example**:
```bash
curl http://localhost:8000/vector_store/info
```

### Search Vector Store

Search directly in vector store (advanced).

**Endpoint**: `POST /vector_store/search`

**Request**:
```bash
curl -X POST http://localhost:8000/vector_store/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 5}'
```

**Request Body**:
```json
{
  "query": "machine learning",
  "top_k": 5,
  "min_score": 0.5
}
```

**Response**:
```json
{
  "query": "machine learning",
  "results": [
    {
      "document_id": "doc_12345",
      "content": "Machine learning is...",
      "similarity_score": 0.92,
      "metadata": {
        "source": "paper.pdf",
        "page": 1
      }
    }
  ],
  "search_time": 0.3
}
```

**Status Codes**:
- `200 OK` - Search successful
- `400 Bad Request` - Invalid query
- `500 Internal Server Error` - Vector store error

**Example**:
```bash
curl -X POST http://localhost:8000/vector_store/search \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "top_k": 3}'
```

### Rebuild Vector Store

Rebuild vector store index.

**Endpoint**: `POST /vector_store/rebuild`

**Request**:
```bash
curl -X POST http://localhost:8000/vector_store/rebuild
```

**Response**:
```json
{
  "success": true,
  "documents_processed": 42,
  "vectors_created": 128,
  "time_seconds": 15.3,
  "status": "completed"
}
```

**Status Codes**:
- `200 OK` - Rebuild started
- `400 Bad Request` - Invalid request
- `500 Internal Server Error` - Build error

**Example**:
```bash
curl -X POST http://localhost:8000/vector_store/rebuild
```

### Clear Vector Store

Clear all documents from vector store.

**Endpoint**: `DELETE /vector_store`

**Request**:
```bash
curl -X DELETE http://localhost:8000/vector_store
```

**Response**:
```json
{
  "success": true,
  "message": "Vector store cleared",
  "documents_deleted": 42
}
```

**⚠️ WARNING**: This action deletes all data. Use with caution!

**Status Codes**:
- `200 OK` - Vector store cleared
- `500 Internal Server Error` - Clear error

**Example**:
```bash
curl -X DELETE http://localhost:8000/vector_store
```

---

## Configuration

### Get Models

Get available LLM models.

**Endpoint**: `GET /models`

**Response**:
```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "available_models": [
      "gpt-3.5-turbo",
      "gpt-4",
      "gpt-4-turbo"
    ],
    "max_tokens": 4096
  },
  "embedder": {
    "model": "all-MiniLM-L6-v2",
    "dimensions": 384
  },
  "reranker": {
    "enabled": true,
    "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
  }
}
```

**Status Codes**:
- `200 OK` - Success
- `500 Internal Server Error` - Configuration error

**Example**:
```bash
curl http://localhost:8000/models
```

### Get Configuration

Get current configuration (non-sensitive).

**Endpoint**: `GET /config`

**Response**:
```json
{
  "environment": "production",
  "debug": false,
  "log_level": "INFO",
  "version": "1.0.0",
  "vector_store": {
    "type": "chroma",
    "path": "backend/data/vector_store"
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7
  },
  "embedder": {
    "model": "all-MiniLM-L6-v2",
    "batch_size": 128
  }
}
```

**Status Codes**:
- `200 OK` - Success
- `500 Internal Server Error` - Configuration error

**Example**:
```bash
curl http://localhost:8000/config
```

---

## Statistics

### Get Statistics

Get usage and performance statistics.

**Endpoint**: `GET /stats`

**Response**:
```json
{
  "uptime_seconds": 86400,
  "documents": {
    "total": 42,
    "by_source": {
      "pdf": 20,
      "web": 15,
      "youtube": 7
    },
    "by_date": {
      "2024-01-15": 5,
      "2024-01-14": 3
    }
  },
  "vectors": {
    "total": 128,
    "dimensions": 384
  },
  "queries": {
    "total": 256,
    "today": 32,
    "average_time": 2.5,
    "errors": 2
  },
  "cache": {
    "hits": 156,
    "misses": 100,
    "hit_rate": 0.61
  },
  "memory": {
    "used_mb": 512,
    "available_mb": 8192,
    "percent": 6.25
  }
}
```

**Status Codes**:
- `200 OK` - Success
- `500 Internal Server Error` - Stats error

**Example**:
```bash
curl http://localhost:8000/stats
```

### Get Daily Statistics

Get statistics for a specific day.

**Endpoint**: `GET /stats/daily/<date>`

**Parameters**:
- `date`: Date in YYYY-MM-DD format

**Response**:
```json
{
  "date": "2024-01-15",
  "documents_ingested": 5,
  "queries": 32,
  "avg_query_time": 2.3,
  "errors": 1,
  "uptime_percent": 99.5
}
```

**Status Codes**:
- `200 OK` - Success
- `400 Bad Request` - Invalid date format
- `500 Internal Server Error` - Stats error

**Example**:
```bash
curl http://localhost:8000/stats/daily/2024-01-15
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "INVALID_INPUT",
  "details": {
    "field": "question",
    "message": "Question cannot be empty"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_INPUT` | 400 | Invalid request parameters |
| `FILE_NOT_FOUND` | 404 | File or document not found |
| `VECTOR_STORE_ERROR` | 500 | Vector store operation failed |
| `LLM_ERROR` | 500 | LLM API call failed |
| `TIMEOUT` | 408 | Request timeout |
| `RATE_LIMIT` | 429 | Rate limit exceeded |
| `UNAUTHORIZED` | 401 | Authentication required |
| `SERVER_ERROR` | 500 | Internal server error |

### Example Error

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'

# Response:
# {
#   "success": false,
#   "error": "Invalid input",
#   "error_code": "INVALID_INPUT",
#   "details": {
#     "field": "question",
#     "message": "Question cannot be empty"
#   }
# }
```

---

## Rate Limiting

Default rate limits:
- **Ingest**: 10 requests per minute
- **Query**: 30 requests per minute
- **Search**: 100 requests per minute

When rate limited, you'll get:
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT",
  "retry_after_seconds": 60
}
```

HTTP Status: `429 Too Many Requests`

Headers:
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## Examples

### Complete Query Flow

```bash
#!/bin/bash

# 1. Check health
curl http://localhost:8000/health

# 2. Ingest a document
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.pdf"

# 3. Query the document
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# 4. Get statistics
curl http://localhost:8000/stats
```

### Using with Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Ingest a file
files = {'file': open('document.pdf', 'rb')}
response = requests.post(f"{BASE_URL}/ingest", files=files)
print(response.json())

# Query
query_data = {
    "question": "What is machine learning?",
    "top_k": 5
}
response = requests.post(
    f"{BASE_URL}/query",
    json=query_data
)
answer = response.json()
print(f"Answer: {answer['answer']}")
print(f"Sources: {answer['sources']}")
```

### Using with JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";

// Query
async function askQuestion(question) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question})
  });
  
  const data = await response.json();
  return data;
}

// Usage
askQuestion("What is AI?")
  .then(result => console.log(result.answer));
```

### Using with cURL

```bash
# Complex query with options
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do transformers work?",
    "top_k": 3,
    "rerank": true,
    "context_length": 3000
  }' | jq .

# Pretty print JSON
curl -s http://localhost:8000/stats | jq .
```

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Health, ingestion, query endpoints
- Vector store management
- Statistics and monitoring

---

## Support

- **Issues**: Open a GitHub issue
- **Questions**: Check FAQ or documentation
- **Bugs**: Submit with reproduction steps

Good luck! 🚀
