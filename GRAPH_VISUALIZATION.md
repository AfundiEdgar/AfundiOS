# Graph-Based Memory Visualization

## Overview

The graph visualization system transforms your document collection into an interactive knowledge graph that reveals relationships between chunks and documents. This enables users to:

- **Explore document relationships** - Discover which chunks are semantically related
- **Find key information** - Identify the most important chunks in your collection
- **Discover topics** - Automatically cluster similar content
- **Navigate documents** - Find paths between related information
- **Analyze patterns** - Understand the structure of your knowledge base

## Architecture

### Core Components

#### 1. **KnowledgeGraph** (`backend/core/graph.py`)
The in-memory graph data structure representing chunks as nodes and relationships as edges.

**Nodes (Documents/Chunks)**
```python
@dataclass
class Node:
    id: str                          # Unique identifier
    text: str                        # Chunk content
    type: str = "chunk"             # "chunk" or "document"
    metadata: Dict = {}              # Source, tags, timestamps
    embedding: Optional[List[float]] # Optional embedding vector
```

**Edges (Relationships)**
```python
@dataclass
class Edge:
    source: str                  # Source node ID
    target: str                  # Target node ID
    weight: float = 1.0         # Relationship strength (0-1)
    relationship_type: str      # "similar", "mentioned", "hierarchical"
    metadata: Dict = {}          # Additional edge properties
```

**Graph Operations**
- `add_node(node)` - Add a chunk to the graph
- `add_edge(edge)` - Add a relationship
- `get_node_neighbors(node_id, distance)` - Find nearby chunks
- `get_edges_for_node(node_id)` - Get all relationships for a chunk
- `get_connected_components()` - Find disconnected graph regions
- `calculate_statistics()` - Compute graph metrics
- `find_semantic_clusters(threshold)` - Cluster similar content

#### 2. **GraphBuilder** (`backend/core/graph.py`)
Constructs graphs from document chunks using multiple relationship types.

**Relationship Types**
- **Semantic Similarity** (embedding-based)
  - Uses cosine similarity of chunk embeddings
  - Configurable threshold (default: 0.6)
  - Weight: similarity score (0-1)

- **Text-Based Similarity** (fallback when embeddings unavailable)
  - Keyword overlap between chunks
  - Weight: overlap ratio (0-1)

- **Hierarchical Relationships** (document structure)
  - Sequential chunks from same document
  - Weight: 0.9 (strong sequential connection)

- **Mention Relationships** (explicit references)
  - Chunks that reference other chunks
  - Weight: 0.8 (explicit connection)

**Building a Graph**
```python
builder = GraphBuilder(similarity_threshold=0.6)
graph = builder.build_from_chunks(chunks, embeddings)
builder.add_document_hierarchy(doc_chunks)
builder.add_mention_edges(chunk_mentions)
```

#### 3. **GraphAnalyzer** (`backend/core/graph_analysis.py`)
Analyzes graph properties and identifies patterns.

**Node Analysis**
```python
analysis = analyzer.analyze_node(node_id)
# Returns:
# - degree: number of connections
# - betweenness_centrality: bridging importance
# - closeness_centrality: average distance to others
# - clustering_coefficient: local density
# - importance_score: combined metric
```

**Key Capabilities**
- **Find Similar Nodes** - Get top N chunks similar to a given chunk
- **Find Key Nodes** - Identify most important chunks (hubs)
- **Find Topic Clusters** - Automatic community detection
- **Recommend Connections** - Suggest missing relationships
- **Path Finding** - Find shortest path between chunks
- **Subgraph Extraction** - Extract local neighborhood around chunk

**Graph Metrics**
- **Density** - How interconnected the graph is (0-1)
- **Average Degree** - Average connections per chunk
- **Clustering Coefficient** - Local triangle formation
- **Connected Components** - Number of isolated subgraphs
- **Betweenness Centrality** - How often a chunk bridges others
- **Closeness Centrality** - Average distance to all other chunks

## API Endpoints

All graph endpoints are available at `/api/graph/`.

### Graph Access

#### Initialize Graph
```bash
POST /api/graph/initialize
```
Rebuild the knowledge graph from stored chunks.

**Response:**
```json
{
  "status": "initialized",
  "nodes": 150,
  "edges": 342,
  "components": 3
}
```

#### Get All Nodes
```bash
GET /api/graph/nodes?node_type=chunk
```
Retrieve all nodes in the graph.

**Parameters:**
- `node_type` (optional): Filter by "chunk" or "document"

**Response:**
```json
[
  {
    "id": "chunk_001",
    "text": "Machine learning is a subset of...",
    "type": "chunk",
    "metadata": {
      "source": "document_1.pdf",
      "doc_id": "doc_001"
    }
  }
]
```

#### Get All Edges
```bash
GET /api/graph/edges?min_weight=0.5
```
Retrieve all relationships in the graph.

**Parameters:**
- `min_weight`: Minimum relationship strength (0-1)

**Response:**
```json
[
  {
    "source": "chunk_001",
    "target": "chunk_042",
    "weight": 0.78,
    "type": "similar"
  }
]
```

#### Get Complete Graph
```bash
GET /api/graph
```
Retrieve the entire graph (all nodes and edges).

### Statistics & Analysis

#### Get Graph Statistics
```bash
GET /api/graph/statistics
```
Returns overall graph metrics.

**Response:**
```json
{
  "node_count": 150,
  "edge_count": 342,
  "density": 0.031,
  "avg_degree": 4.56,
  "clustering_coefficient": 0.42,
  "connected_components": 3,
  "largest_component_size": 145
}
```

#### Analyze Node
```bash
GET /api/graph/nodes/{node_id}/analysis
```
Get detailed analysis of a specific chunk.

**Response:**
```json
{
  "node_id": "chunk_001",
  "text": "Machine learning fundamentals...",
  "degree": 12,
  "centrality": 0.67,
  "related_nodes": [
    ["chunk_042", 0.78],
    ["chunk_088", 0.75],
    ["chunk_015", 0.72]
  ]
}
```

#### Find Similar Nodes
```bash
GET /api/graph/nodes/{node_id}/similar?limit=5&min_weight=0.0
```
Find chunks most similar to a given chunk.

**Parameters:**
- `limit`: Number of results (1-20, default: 5)
- `min_weight`: Minimum similarity (0-1, default: 0.0)

**Response:**
```json
[
  {
    "node_id": "chunk_042",
    "text": "Deep learning applications...",
    "similarity": 0.78
  }
]
```

#### Get Node Neighbors
```bash
GET /api/graph/nodes/{node_id}/neighbors?distance=2
```
Get all chunks within specified distance.

**Parameters:**
- `distance`: Search radius (1-5, default: 1)

**Response:** Array of GraphNodeResponse

### Key Insights

#### Get Key Nodes
```bash
GET /api/graph/key-nodes?top_k=5
```
Find the most important chunks in your collection.

**Response:**
```json
[
  {
    "node_id": "chunk_001",
    "text": "Core concept summary...",
    "degree": 25,
    "centrality": 0.89,
    "related_nodes": [...]
  }
]
```

#### Get Topic Clusters
```bash
GET /api/graph/topics
```
Automatically discover topic clusters.

**Response:**
```json
{
  "clusters": [
    ["chunk_001", "chunk_042", "chunk_088"],
    ["chunk_015", "chunk_023", "chunk_067"]
  ],
  "cluster_count": 8
}
```

#### Get Recommendations
```bash
GET /api/graph/recommendations?limit=10
```
Suggest relationships that should exist.

**Response:**
```json
[
  {
    "source": "chunk_001",
    "target": "chunk_150",
    "score": 3.5,
    "reason": "Shared 5 common neighbors"
  }
]
```

### Navigation

#### Find Path
```bash
GET /api/graph/paths/{source}/to/{target}
```
Find the shortest path between two chunks.

**Response:**
```json
{
  "path": ["chunk_001", "chunk_042", "chunk_088", "chunk_150"],
  "length": 3,
  "nodes": [
    {"id": "chunk_001", "text": "..."},
    {"id": "chunk_042", "text": "..."}
  ]
}
```

#### Get Subgraph
```bash
GET /api/graph/subgraph/{node_id}?distance=2
```
Extract local neighborhood around a chunk.

**Parameters:**
- `distance`: Radius to extract (1-5, default: 2)

**Response:** GraphResponse (nodes and edges)

### Search

#### Search Graph
```bash
POST /api/graph/search?query=machine+learning&limit=10
```
Find graph nodes related to a text query.

**Response:**
```json
{
  "query": "machine learning",
  "nodes": [
    {
      "id": "chunk_001",
      "text": "Machine learning fundamentals...",
      "type": "chunk",
      "metadata": {}
    }
  ],
  "count": 7
}
```

## Usage Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/graph"

# Initialize graph
response = requests.post(f"{BASE_URL}/initialize")
print(response.json())

# Get statistics
stats = requests.get(f"{BASE_URL}/statistics").json()
print(f"Nodes: {stats['node_count']}, Edges: {stats['edge_count']}")

# Find similar chunks
similar = requests.get(
    f"{BASE_URL}/nodes/chunk_001/similar",
    params={"limit": 5}
).json()

# Find key nodes
key_nodes = requests.get(f"{BASE_URL}/key-nodes?top_k=10").json()

# Find path between chunks
path = requests.get(f"{BASE_URL}/paths/chunk_001/to/chunk_150").json()
print(f"Path length: {path['length']}")

# Search by text
results = requests.post(
    f"{BASE_URL}/search",
    params={"query": "machine learning", "limit": 10}
).json()
```

### JavaScript/Frontend

```javascript
const API_BASE = '/api/graph';

// Get complete graph for visualization
async function loadGraph() {
  const response = await fetch(`${API_BASE}`);
  return response.json();
}

// Find similar chunks
async function findSimilar(nodeId, limit = 5) {
  const response = await fetch(
    `${API_BASE}/nodes/${nodeId}/similar?limit=${limit}`
  );
  return response.json();
}

// Get node analysis
async function analyzeNode(nodeId) {
  const response = await fetch(
    `${API_BASE}/nodes/${nodeId}/analysis`
  );
  return response.json();
}

// Get topic clusters
async function getTopics() {
  const response = await fetch(`${API_BASE}/topics`);
  return response.json();
}

// Search graph
async function searchGraph(query, limit = 10) {
  const response = await fetch(
    `${API_BASE}/search?query=${encodeURIComponent(query)}&limit=${limit}`
  );
  return response.json();
}
```

## Configuration

Graph behavior is controlled via environment variables in `.env`:

```bash
# Graph similarity threshold for building relationships (0-1)
GRAPH_SIMILARITY_THRESHOLD=0.6

# Enable/disable graph visualization
GRAPH_ENABLED=true

# Maximum graph size (number of nodes)
GRAPH_MAX_NODES=5000

# Cache graph in memory (faster but uses more RAM)
GRAPH_CACHE_ENABLED=true
```

## Performance Considerations

### Scalability
- **Recommended max size**: 5,000 chunks
- **Graph initialization**: ~100ms per 100 chunks
- **Query operations**: <100ms for typical queries

### Optimization Tips

1. **Use Thresholds**
   ```python
   # Only show strong relationships
   edges = requests.get(f"{API_BASE}/edges?min_weight=0.7").json()
   ```

2. **Limit Search Depth**
   ```python
   # Don't search beyond distance 2 for large graphs
   neighbors = requests.get(
       f"{API_BASE}/nodes/{id}/neighbors?distance=2"
   ).json()
   ```

3. **Lazy Initialization**
   ```python
   # Graph is built on first access, not during startup
   # Subsequent requests are fast
   ```

4. **Caching**
   - Graph statistics are cached
   - Node analysis results are cached
   - Cache is invalidated on graph rebuild

## Future Enhancements

- **Dynamic Updates**: Incrementally update graph when new chunks added
- **Temporal Analysis**: Track how relationships evolve over time
- **Influence Tracking**: Identify which chunks are most cited/referenced
- **Recommendation Engine**: ML-based suggestions for related content
- **Export Formats**: GraphML, JSON-LD for third-party visualization
- **Graph Algorithms**: Community detection, influence propagation
- **Visualization UI**: D3.js, Cytoscape.js integration in frontend

## Troubleshooting

### Graph not initializing
```
Error: "No chunks available to build graph"
```
**Solution**: Ingest documents first via `/api/ingest` endpoint

### Slow graph operations
```
Error: Query taking > 1 second
```
**Solutions**:
- Reduce `top_k` in find requests
- Increase `distance` threshold
- Rebuild graph with higher similarity threshold

### Memory issues
```
Error: "Graph exceeds maximum size"
```
**Solutions**:
- Increase `GRAPH_MAX_NODES` limit
- Filter to subset of documents
- Archive old chunks

## Related Features

- **[LLM Integration](./LLM_PROVIDERS.md)** - Context enhancement with graph insights
- **[Reranking](./RERANKING.md)** - Use graph relationships to rerank results
- **[Encryption](./ENCRYPTION.md)** - Secure graph node content
