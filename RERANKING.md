# Reranking Implementation

## Overview

The retrieval pipeline now includes optional **cross-encoder reranking** to improve result quality. After the initial vector similarity search, results can be reranked using a cross-encoder model to better match semantic relevance.

## How It Works

### Traditional Flow (Vector Search Only)
```
User Query
    ↓
Query Embedding
    ↓
Vector Similarity Search (k=5)
    ↓
Return Top 5 Results
```

### With Reranking
```
User Query
    ↓
Query Embedding
    ↓
Vector Similarity Search (k=15, get more candidates)
    ↓
Cross-Encoder Reranking (compare query with each chunk)
    ↓
Return Top 5 Reranked Results
```

## Architecture

### `backend/core/reranker.py`
New module providing reranking functionality:

- **`rerank_results()`** - Core reranking function using cross-encoder
- **`rerank_and_filter()`** - Wrapper that optionally applies reranking
- **`_get_reranker()`** - Lazy-loads the cross-encoder model on first use

### Model Used
- **`cross-encoder/mmarco-MiniLMv2-L12-H384-v1`**
  - Lightweight and fast
  - Multilingual support
  - 384 embedding dimensions
  - ~12 layers, ~110M parameters

### Why Reranking?

1. **Semantic Precision** - Vector similarity can miss nuanced relevance
2. **Query-Document Matching** - Cross-encoders directly score query-document pairs
3. **Ranking Quality** - Better ordering than pure vector similarity
4. **Minimal Overhead** - Only reranks top N candidates (not entire index)

## API Usage

### Without Reranking (Default)
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5,
    "enable_rerank": false
  }'
```

### With Reranking
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5,
    "enable_rerank": true,
    "rerank_threshold": 0.5
  }'
```

### Parameters

- **`enable_rerank`** (bool, default: `false`)
  - Enable cross-encoder reranking

- **`rerank_threshold`** (float, default: `0.0`)
  - Minimum relevance score (typically -1 to 1)
  - Only results above threshold are returned
  - Set higher for stricter filtering

## Implementation Details

### QueryRequest Model
```python
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    session_id: Optional[str] = None
    chat_history: Optional[List[Tuple[str, str]]] = None
    enable_rerank: bool = False
    rerank_threshold: float = 0.0
```

### Retriever Pipeline
```python
def retrieve_relevant_chunks(
    query: str,
    k: int = 5,
    enable_rerank: bool = False,
    rerank_threshold: float = 0.0,
) -> List[Dict]:
    # 1. Vector search (k*3 candidates if reranking enabled)
    # 2. Optional reranking and filtering
    # 3. Return top k results
```

## Performance Characteristics

### Vector Search Only
- Speed: ~10-50ms (depends on index size)
- Retrieval: Returns top k by similarity score

### With Reranking (enabled=True, k=5)
- Vector search: ~10-50ms (searches for k*3=15 candidates)
- Reranking: ~100-500ms (ranks 15 chunks with cross-encoder)
- Total: ~110-550ms per query
- Quality: Higher semantic precision

## When to Use Reranking

### Enable Reranking When:
- ✅ Quality is more important than speed
- ✅ Complex queries with multiple facets
- ✅ Small to medium result sets (k ≤ 10)
- ✅ User is willing to wait 100-500ms

### Disable Reranking When:
- ✅ Real-time requirements (< 50ms)
- ✅ Simple keyword queries
- ✅ Very large result sets (k > 50)
- ✅ Resource-constrained environments

## Configuration

### Installation
Sentence-transformers is in `requirements.txt`:
```bash
pip install sentence-transformers
```

### Model Caching
The cross-encoder model is downloaded on first use and cached locally (~350MB).

### Custom Models
To use a different cross-encoder:
```python
# In reranker.py, modify _get_reranker():
_reranker = CrossEncoder("cross-encoder/your-model-here", max_length=512)
```

Popular alternatives:
- `cross-encoder/qnli-distilroberta-base` - Faster, smaller
- `cross-encoder/ms-marco-MiniLM-L-12-v2` - Balanced
- `cross-encoder/ms-marco-TinyBERT-L-2-v2` - Fastest

## Error Handling

If cross-encoder fails:
1. Logs warning
2. Falls back to original vector search order
3. Returns results without reranking
4. No breaking errors

## Example: Improving Search Quality

**Without Reranking:**
```
Query: "How do neural networks learn?"

Results (by vector similarity):
1. "Introduction to ML" (high similarity but generic)
2. "Deep Learning Guide" (lower similarity)
3. "Backpropagation Algorithm" (lower similarity)
```

**With Reranking:**
```
Query: "How do neural networks learn?"

Results (by cross-encoder relevance):
1. "Backpropagation Algorithm" (directly answers question)
2. "Deep Learning Guide" (detailed explanation)
3. "Introduction to ML" (provides context)
```

## Future Enhancements

1. **Ensemble Reranking** - Combine multiple cross-encoders
2. **Batch Reranking** - Process multiple queries in batch
3. **Adaptive Thresholding** - Dynamic score thresholds
4. **Result Fusion** - Combine vector and reranker scores
5. **Caching** - Cache reranker results for repeated queries
6. **Monitoring** - Track reranking impact on answer quality
