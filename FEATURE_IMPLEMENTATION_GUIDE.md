# Feature Implementation Guide

Detailed guides for implementing common features in AfundiOS.

## Table of Contents

1. [Adding New File Type Support](#adding-new-file-type-support)
2. [Adding New Vector Store](#adding-new-vector-store)
3. [Adding New LLM Provider](#adding-new-llm-provider)
4. [Adding Reranking](#adding-reranking)
5. [Adding Custom Chunking Strategy](#adding-custom-chunking-strategy)

---

## Adding New File Type Support

Example: Support `.docx` (Word documents)

### Step 1: Create Extractor

File: `backend/core/extractor.py`

Add this function:

```python
def extract_docx(file_path: str) -> str:
    """
    Extract text from DOCX (Word) files.
    
    Args:
        file_path: Path to .docx file
        
    Returns:
        Extracted text
    """
    try:
        from docx import Document
        doc = Document(file_path)
        
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text)
        
        return '\n'.join(text_parts)
    
    except Exception as e:
        raise ValueError(f"Error extracting DOCX: {e}")
```

Install dependency:
```bash
pip install python-docx
```

### Step 2: Register in Ingest

File: `backend/api/ingest.py`

Add to the ingest handler:

```python
# In the file type detection section
if file.filename.endswith('.docx'):
    text = extract_docx(temp_file.name)
elif file.filename.endswith('.xlsx'):
    # Existing Excel handler
    text = extract_xlsx(temp_file.name)
# ... other types
```

### Step 3: Write Tests

File: `tests/test_ingestion.py`

```python
def test_ingest_docx():
    """Test DOCX file ingestion"""
    # Create test DOCX
    from docx import Document
    doc = Document()
    doc.add_paragraph("Test content for DOCX")
    doc.save("test.docx")
    
    # Test ingestion
    with open("test.docx", "rb") as f:
        response = client.post(
            "/ingest",
            files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
    
    assert response.status_code == 200
    assert response.json()["chunks"] > 0
    
    # Cleanup
    os.remove("test.docx")


def test_ingest_docx_with_tables():
    """Test DOCX with tables"""
    from docx import Document
    from docx.shared import Inches
    
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Header 1"
    table.cell(0, 1).text = "Header 2"
    table.cell(1, 0).text = "Data 1"
    table.cell(1, 1).text = "Data 2"
    doc.save("test_table.docx")
    
    with open("test_table.docx", "rb") as f:
        response = client.post("/ingest", files={"file": f})
    
    assert response.status_code == 200
    assert "Data 1" in response.json()["preview"]
```

### Step 4: Update Documentation

Add to README.md:

```markdown
### Supported File Types
- ✅ PDF (.pdf)
- ✅ Text (.txt, .md)
- ✅ Word (.docx) — NEW!
- ✅ Excel (.xlsx)
- ✅ Web URLs
- ✅ YouTube videos
```

### Step 5: Test End-to-End

```bash
# 1. Start backend
python -m backend.main

# 2. Create test DOCX
python << 'EOF'
from docx import Document
doc = Document()
doc.add_paragraph("This is a test Word document")
doc.add_paragraph("It tests DOCX ingestion")
doc.save("test.docx")
EOF

# 3. Upload via API
curl -X POST http://localhost:8000/ingest \
  -F "file=@test.docx"

# 4. Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# 5. Run tests
pytest tests/test_ingestion.py::test_ingest_docx -v
```

---

## Adding New Vector Store

Example: Add Weaviate support

### Step 1: Choose Your Store

| Store | Installation | Configuration |
|-------|--------------|----------------|
| Chroma | `pip install chromadb` | `VECTOR_STORE_TYPE=chroma` |
| FAISS | `pip install faiss-cpu` | `VECTOR_STORE_TYPE=faiss` |
| Pinecone | `pip install pinecone-client` | `VECTOR_STORE_TYPE=pinecone` |
| Weaviate | `pip install weaviate-client` | `VECTOR_STORE_TYPE=weaviate` |

### Step 2: Update Configuration

File: `backend/config.py`

The validator already supports multiple stores:

```python
@validator('vector_store_type')
def validate_vector_store_type(cls, v: str) -> str:
    valid_types = {'chroma', 'pinecone', 'weaviate', 'milvus'}
    # Already supports your store!
```

### Step 3: Create Store Adapter

File: `backend/core/vectorstore.py`

Add store initialization:

```python
def create_vector_store(store_type: str, **kwargs):
    """Factory function to create vector store"""
    
    if store_type == "chroma":
        return ChromaVectorStore(**kwargs)
    elif store_type == "faiss":
        return FAISSVectorStore(**kwargs)
    elif store_type == "weaviate":
        return WeaviateVectorStore(**kwargs)
    elif store_type == "pinecone":
        return PineconeVectorStore(**kwargs)
    else:
        raise ValueError(f"Unknown store: {store_type}")


class WeaviateVectorStore:
    def __init__(self, url: str = "http://localhost:8080"):
        import weaviate
        self.client = weaviate.Client(url)
    
    def add(self, documents: List[Document]):
        for doc in documents:
            self.client.data_object.create(
                class_name="Document",
                data_object={"content": doc.text}
            )
    
    def search(self, query_embedding: List[float], top_k: int = 5):
        # Search logic
        pass
```

### Step 4: Update Initialization

File: `backend/core/retriever.py`

```python
from backend.core.vectorstore import create_vector_store

# Initialize with selected store
vector_store = create_vector_store(
    settings.vector_store_type,
    **store_config
)
```

### Step 5: Test

```bash
# Test with new store
VECTOR_STORE_TYPE=weaviate python -m backend.main
```

---

## Adding New LLM Provider

Example: Add Cohere support (already configured, just implementation details)

### Step 1: Add Provider Support

File: `backend/core/llm.py`

```python
def get_llm(provider: str, **kwargs):
    """Get LLM instance for provider"""
    
    if provider == "openai":
        return OpenAILLM(**kwargs)
    elif provider == "anthropic":
        return AnthropicLLM(**kwargs)
    elif provider == "cohere":
        return CohereLLM(**kwargs)
    elif provider == "local":
        return LocalLLM(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")


class CohereLLM:
    def __init__(self, api_key: str, model: str = "command"):
        import cohere
        self.client = cohere.Client(api_key)
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate response"""
        response = self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            model=self.model
        )
        return response.generations[0].text
```

Install:
```bash
pip install cohere
```

### Step 2: Update Config Validation

Already supported in `backend/config.py`:

```python
if provider == 'cohere' and not values.get('cohere_api_key'):
    raise ValueError("COHERE_API_KEY not set")
```

### Step 3: Add Tests

File: `tests/test_llm.py`

```python
def test_cohere_llm():
    """Test Cohere LLM"""
    llm = CohereLLM(api_key="test-key")
    
    # Mock the API call
    with patch('cohere.Client') as mock_client:
        mock_response = MagicMock()
        mock_response.generations[0].text = "Test response"
        mock_client.return_value.generate.return_value = mock_response
        
        result = llm.generate("Test prompt")
        assert result == "Test response"
```

### Step 4: Configuration

Users can now use:

```bash
# .env
LLM_PROVIDER=cohere
COHERE_API_KEY=your-key
LLM_MODEL=command
```

---

## Adding Reranking

Improve retrieval quality with reranking.

### Step 1: Choose Reranking Method

**Option A: CrossEncoder (Best)**

```bash
pip install sentence-transformers
```

### Step 2: Create Reranker

File: `backend/core/reranker.py`

```python
from sentence_transformers import CrossEncoder
from typing import List, Tuple

class Reranker:
    """Rerank documents by relevance to query"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
    
    def rerank(
        self, 
        query: str, 
        documents: List[str],
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Rerank documents by relevance to query
        
        Args:
            query: Search query
            documents: Candidate documents
            top_k: Return top K documents
            
        Returns:
            List of (document, score) tuples
        """
        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]
        
        # Get relevance scores
        scores = self.model.predict(pairs)
        
        # Sort by score and return top K
        ranked = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return ranked[:top_k]
```

### Step 3: Integrate with Retriever

File: `backend/core/retriever.py`

```python
from backend.core.reranker import Reranker

class Retriever:
    def __init__(self, rerank: bool = True):
        self.vector_store = create_vector_store(...)
        self.reranker = Reranker() if rerank else None
    
    def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
        """Retrieve with optional reranking"""
        
        # Initial retrieval (get more candidates)
        candidates = self.vector_store.search(
            query_embedding=embed(query),
            top_k=top_k * 2  # Get more for reranking
        )
        
        # Rerank if enabled
        if self.reranker:
            documents = [c.text for c in candidates]
            reranked = self.reranker.rerank(query, documents, top_k=top_k)
            return reranked
        
        return candidates[:top_k]
```

### Step 4: Configuration

Add to `.env`:

```bash
# Enable reranking
RERANKER_ENABLED=true
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_K=3
```

### Step 5: Test

```python
def test_reranker():
    reranker = Reranker()
    
    query = "What is machine learning?"
    documents = [
        "Machine learning is a subset of AI",
        "Dogs are animals",
        "ML uses algorithms to learn from data"
    ]
    
    results = reranker.rerank(query, documents, top_k=2)
    
    # Top result should be about ML
    assert "learning" in results[0][0].lower()
    assert results[0][1] > results[1][1]  # First score higher
```

---

## Adding Custom Chunking Strategy

Create your own text chunking approach.

### Step 1: Understand Current Chunking

File: `backend/core/chunker.py`

Current strategies:
- Character-based (fixed size)
- Token-based (by token count)
- Semantic (by meaning changes)

### Step 2: Add New Strategy

```python
class SemanticChunker:
    """Chunk based on semantic boundaries"""
    
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 500):
        self.min_size = min_chunk_size
        self.max_size = max_chunk_size
    
    def chunk(self, text: str) -> List[str]:
        """Chunk text by semantic similarity"""
        from sentence_transformers import SentenceTransformer
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Embed sentences
        embeddings = SentenceTransformer("all-MiniLM-L6-v2").encode(sentences)
        
        # Find boundaries where similarity drops
        chunks = []
        current_chunk = []
        
        for i, sentence in enumerate(sentences):
            current_chunk.append(sentence)
            
            # Check similarity to next sentence
            if i < len(sentences) - 1:
                similarity = self._cosine_similarity(
                    embeddings[i], 
                    embeddings[i + 1]
                )
                
                # Start new chunk if similarity drops
                if similarity < 0.5 and len(' '.join(current_chunk)) > self.min_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
        
        # Add remaining
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        import nltk
        return nltk.sent_tokenize(text)
    
    def _cosine_similarity(self, a, b) -> float:
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### Step 3: Register Strategy

```python
CHUNKING_STRATEGIES = {
    "fixed": FixedSizeChunker,
    "token": TokenChunker,
    "semantic": SemanticChunker,
}

def get_chunker(strategy: str) -> Chunker:
    return CHUNKING_STRATEGIES[strategy]()
```

### Step 4: Configuration

```bash
# .env
CHUNKING_STRATEGY=semantic
CHUNK_MIN_SIZE=100
CHUNK_MAX_SIZE=500
```

### Step 5: Test

```python
def test_semantic_chunker():
    chunker = SemanticChunker()
    
    text = """
    Machine learning is a field of AI. 
    It uses algorithms to learn from data.
    Dogs are animals. They are mammals.
    """
    
    chunks = chunker.chunk(text)
    
    # Should separate ML and dogs sections
    assert len(chunks) >= 2
    assert "machine learning" in chunks[0].lower()
    assert "dogs" in chunks[1].lower()
```

---

## Testing Your Feature

### Unit Tests

```bash
# Test your feature in isolation
pytest tests/test_my_feature.py -v
```

### Integration Tests

```bash
# Test with real backend
python -m backend.main
# Upload files, make queries...
```

### Performance Tests

```python
import time

def test_performance():
    start = time.time()
    result = expensive_operation()
    duration = time.time() - start
    
    assert duration < 5.0  # Should be fast
```

---

## Checklist for New Features

- [ ] Code implemented
- [ ] Configuration options added (if needed)
- [ ] Unit tests written
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] README updated with examples
- [ ] Error handling added
- [ ] Performance acceptable
- [ ] Code reviewed
- [ ] PR created

---

## Getting Help

- Check existing similar features
- Review test examples in `tests/`
- Check type hints and docstrings
- Ask in GitHub issues
- Reference FastAPI/Pydantic docs

Happy coding!
