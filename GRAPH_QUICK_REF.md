# Graph API Quick Reference

## Initialization
```bash
# Build graph from stored chunks
curl -X POST http://localhost:8000/api/graph/initialize
```

## Data Access
```bash
# Get complete graph (nodes + edges)
curl http://localhost:8000/api/graph

# List all nodes
curl http://localhost:8000/api/graph/nodes

# List all edges (with min weight filter)
curl "http://localhost:8000/api/graph/edges?min_weight=0.5"

# Get graph statistics
curl http://localhost:8000/api/graph/statistics
```

## Analysis
```bash
# Find most important nodes
curl http://localhost:8000/api/graph/key-nodes?top_k=10

# Analyze specific node
curl http://localhost:8000/api/graph/nodes/{chunk_id}/analysis

# Find similar chunks
curl "http://localhost:8000/api/graph/nodes/{chunk_id}/similar?limit=5"

# Get nodes near chunk (distance=1 or 2)
curl "http://localhost:8000/api/graph/nodes/{chunk_id}/neighbors?distance=2"
```

## Discovery
```bash
# Find topic clusters
curl http://localhost:8000/api/graph/topics

# Get relationship recommendations
curl "http://localhost:8000/api/graph/recommendations?limit=10"

# Find path between two chunks
curl http://localhost:8000/api/graph/paths/{chunk_1}/to/{chunk_2}

# Extract local neighborhood
curl "http://localhost:8000/api/graph/subgraph/{chunk_id}?distance=2"
```

## Search
```bash
# Find chunks by text query
curl "http://localhost:8000/api/graph/search?query=machine+learning&limit=10"
```

## Response Format (Node)
```json
{
  "id": "chunk_001",
  "text": "Full chunk text or truncated...",
  "type": "chunk",
  "metadata": {
    "source": "document.pdf",
    "doc_id": "doc_001"
  }
}
```

## Response Format (Edge)
```json
{
  "source": "chunk_001",
  "target": "chunk_042",
  "weight": 0.78,
  "type": "similar"
}
```

## Response Format (Analysis)
```json
{
  "node_id": "chunk_001",
  "text": "Chunk text...",
  "degree": 12,
  "centrality": 0.67,
  "related_nodes": [
    ["chunk_042", 0.78],
    ["chunk_088", 0.75]
  ]
}
```

## Common Patterns

### Get all related content for chunk
```python
import requests

chunk_id = "chunk_001"
limit = 10

# Get similar chunks
similar = requests.get(
    f"http://localhost:8000/api/graph/nodes/{chunk_id}/similar",
    params={"limit": limit}
).json()

# Get neighbors
neighbors = requests.get(
    f"http://localhost:8000/api/graph/nodes/{chunk_id}/neighbors",
    params={"distance": 2}
).json()

# Get edges
edges = requests.get(
    f"http://localhost:8000/api/graph/nodes/{chunk_id}/analysis"
).json()
```

### Build knowledge map
```python
import requests

# Get key nodes
key_nodes = requests.get(
    "http://localhost:8000/api/graph/key-nodes?top_k=5"
).json()

# For each key node, get neighbors
for node in key_nodes:
    neighbors = requests.get(
        f"http://localhost:8000/api/graph/nodes/{node['node_id']}/neighbors",
        params={"distance": 1}
    ).json()
    print(f"{node['node_id']}: {len(neighbors)} neighbors")
```

### Find conceptual connections
```python
import requests

# Find path between concepts
path = requests.get(
    "http://localhost:8000/api/graph/paths/chunk_001/to/chunk_150"
).json()

if path:
    print(f"Connection found ({path['length']} hops)")
    for node in path['nodes']:
        print(f"  - {node['text']}")
```

### Discover topics
```python
import requests

# Get topic clusters
topics = requests.get(
    "http://localhost:8000/api/graph/topics"
).json()

print(f"Found {topics['cluster_count']} topics:")
for i, cluster in enumerate(topics['clusters']):
    print(f"  Topic {i+1}: {len(cluster)} chunks")
```

### Get recommendations
```python
import requests

# Get suggested relationships
recommendations = requests.get(
    "http://localhost:8000/api/graph/recommendations?limit=10"
).json()

for rec in recommendations:
    print(f"{rec['source']} <-> {rec['target']}: {rec['reason']}")
```

## Parameters

### Query Parameters
- `limit` (int) - Results per page (1-20 for similarity, 1-50 for others)
- `top_k` (int) - Number of top results (1-20)
- `min_weight` (float) - Minimum edge weight (0-1)
- `distance` (int) - Search distance (1-5)
- `query` (str) - Search text
- `node_type` (str) - Filter by type ("chunk" or "document")

### Response Sizes
- Nodes: ~500 bytes each
- Edges: ~100 bytes each
- Complete graph (5000 chunks): ~5MB

## Performance Notes

- **First call**: Initializes graph (~100ms per 100 chunks)
- **Subsequent calls**: <100ms typical
- **Large graphs** (5000+ chunks): May need caching layer
- **Analysis**: Cached results improve performance
- **Memory**: ~1.5 KB per node/edge pair

## Error Handling

```python
import requests

response = requests.get("http://localhost:8000/api/graph/nodes/unknown_id/analysis")

if response.status_code == 404:
    print("Node not found")
elif response.status_code == 500:
    print("Server error - graph may not be initialized")
else:
    data = response.json()
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 404 on graph operations | Call `/graph/initialize` first |
| Empty graph | Ingest documents via `/api/ingest` first |
| Slow queries | Use higher `min_weight` to filter edges |
| Memory issues | Reduce graph size or rebuild less frequently |

## Examples

### JavaScript
```javascript
// Get key nodes
fetch('/api/graph/key-nodes?top_k=10')
  .then(r => r.json())
  .then(nodes => console.log(nodes))

// Find similar
fetch('/api/graph/nodes/chunk_001/similar?limit=5')
  .then(r => r.json())
  .then(similar => console.log(similar))
```

### Python
```python
import requests

BASE = 'http://localhost:8000/api/graph'

# Initialize
requests.post(f'{BASE}/initialize')

# Get stats
stats = requests.get(f'{BASE}/statistics').json()

# Search
results = requests.post(f'{BASE}/search', 
    params={'query': 'machine learning', 'limit': 10}
).json()
```

### cURL
```bash
# Initialize
curl -X POST http://localhost:8000/api/graph/initialize

# Statistics
curl http://localhost:8000/api/graph/statistics

# Key nodes
curl http://localhost:8000/api/graph/key-nodes?top_k=5

# Similar
curl http://localhost:8000/api/graph/nodes/chunk_001/similar?limit=5

# Search
curl "http://localhost:8000/api/graph/search?query=topic&limit=10"
```

## Related Docs

- Full API Reference: `GRAPH_VISUALIZATION.md`
- Integration Guide: `GRAPH_INTEGRATION.md`
- Implementation Summary: `GRAPH_SUMMARY.md`
