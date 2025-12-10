# Optional Features Guide - Step-by-Step Instructions

This guide provides detailed, step-by-step instructions for configuring and using optional features in AfundiOS.

## Table of Contents

1. [Switching Vector Stores](#switching-vector-stores) (Chroma ↔ FAISS ↔ Pinecone)
2. [Using Local LLMs](#using-local-llms) (Ollama, LM Studio, Hugging Face)
3. [Enabling Encryption](#enabling-encryption) (Data at rest)
4. [Memory Compaction](#memory-compaction) (Automated maintenance)
5. [Daily Briefings](#daily-briefings) (Automatic summaries)
6. [Reranking](#reranking) (Improving retrieval quality)

---

## Switching Vector Stores

Vector stores are where your embeddings are stored. Choose the one that fits your use case.

### Overview

| Store | Best For | Setup Complexity | Scalability |
|-------|----------|-----------------|-------------|
| **Chroma** | Local development | ⭐ Easy | Single machine |
| **FAISS** | Fast local search | ⭐⭐ Medium | Single machine |
| **Pinecone** | Production scale | ⭐⭐⭐ Complex | Highly scalable |
| **Weaviate** | Advanced features | ⭐⭐⭐ Complex | Scalable |

### Default: Chroma (Local, Embedded)

Chroma is the default and requires no additional setup:

```bash
# Already configured in .env.example
VECTOR_STORE_TYPE=chroma
VECTOR_STORE_PATH=data/vector_store
```

**Advantages**:
- ✅ Works out of the box
- ✅ No external dependencies
- ✅ Data stays local
- ✅ Perfect for development

**Disadvantages**:
- ❌ Single machine only
- ❌ Not suitable for 100M+ vectors

---

### Option 1: FAISS (Fast Approximate Nearest Neighbor Search)

FAISS is ideal for **local, fast similarity search** without external servers.

#### Step 1: Install FAISS

```bash
# CPU version (most compatible)
pip install faiss-cpu

# OR GPU version (if you have CUDA)
pip install faiss-gpu
```

**Verify installation**:
```bash
python -c "import faiss; print(f'FAISS version: {faiss.__version__}')"
```

#### Step 2: Update Configuration

Edit `.env`:

```bash
# Switch to FAISS
VECTOR_STORE_TYPE=faiss
VECTOR_STORE_PATH=data/faiss_index

# Keep other settings the same
EMBEDDING_MODEL=text-embedding-3-small
```

#### Step 3: Create FAISS Index

FAISS needs an index structure. Create it with:

```bash
# Python script to initialize FAISS
python << 'EOF'
import faiss
import numpy as np
from pathlib import Path

# Create data directory
index_dir = Path("data/faiss_index")
index_dir.mkdir(parents=True, exist_ok=True)

# Create empty index
dimension = 1536  # OpenAI embedding dimension
index = faiss.IndexFlatL2(dimension)

# Save empty index
faiss.write_index(index, str(index_dir / "index.faiss"))
print(f"✓ FAISS index created at {index_dir / 'index.faiss'}")
EOF
```

#### Step 4: Test Configuration

```bash
# Validate configuration
python -m backend.config_validator

# Start backend
python -m backend.main
```

**Expected output**:
```
✓ Vector Store:         faiss
✓ All configuration validations passed
```

#### Step 5: Ingest Data

Upload files to test FAISS:

```bash
# Via API
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.pdf"

# Via frontend
streamlit run frontend/app.py
```

#### Step 6: Verify FAISS is Working

```bash
# Check index file
ls -lh data/faiss_index/

# Check query works
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AfundiOS?"}'
```

#### Switching Back to Chroma

```bash
# Edit .env
VECTOR_STORE_TYPE=chroma
VECTOR_STORE_PATH=data/vector_store

# Restart backend
python -m backend.main
```

---

### Option 2: Pinecone (Cloud Vector Database)

Pinecone is ideal for **production-scale** deployments with millions of vectors.

#### Step 1: Create Pinecone Account

1. Go to https://www.pinecone.io
2. Sign up for free account
3. Create a new project
4. Note your:
   - API Key
   - Environment (e.g., us-west-4-gcp-free)
   - Project ID

#### Step 2: Install Pinecone SDK

```bash
pip install pinecone-client
```

**Verify**:
```bash
python -c "import pinecone; print(f'Pinecone version: {pinecone.__version__}')"
```

#### Step 3: Update Configuration

Edit `.env`:

```bash
# Switch to Pinecone
VECTOR_STORE_TYPE=pinecone

# Pinecone-specific settings
PINECONE_API_KEY=your-api-key-here
PINECONE_ENVIRONMENT=us-west-4-gcp-free
PINECONE_INDEX_NAME=afundios-index

# Keep other settings
EMBEDDING_MODEL=text-embedding-3-small
```

#### Step 4: Create Pinecone Index

Create index in Pinecone console or via API:

```bash
python << 'EOF'
import pinecone

# Initialize
pinecone.init(
    api_key="your-api-key",
    environment="us-west-4-gcp-free"
)

# Create index
index_name = "afundios-index"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embedding dimension
        metric="cosine"
    )
    print(f"✓ Created index: {index_name}")
else:
    print(f"✓ Index already exists: {index_name}")
EOF
```

#### Step 5: Test Pinecone Connection

```bash
# Validate configuration
python -m backend.config_validator

# Start backend
python -m backend.main
```

**Expected output**:
```
✓ Vector Store:         pinecone
✓ All configuration validations passed
```

#### Step 6: Monitor Pinecone Usage

Check Pinecone dashboard:
- Vector count
- Index size
- Query metrics
- Cost estimates

---

## Using Local LLMs

Run language models locally without cloud dependencies. Perfect for privacy-conscious deployments.

### Overview

| LLM | Best For | VRAM Needed | Speed |
|-----|----------|------------|-------|
| **Ollama** | Easy setup | 4-8GB | Fast |
| **LM Studio** | GUI interface | 4-8GB | Fast |
| **Hugging Face** | Maximum control | 6-16GB | Medium |
| **vLLM** | High throughput | 8-24GB | Very fast |

### Option 1: Ollama (Easiest)

Ollama makes running local LLMs incredibly simple.

#### Step 1: Install Ollama

**On macOS/Linux**:
```bash
curl https://ollama.ai/install.sh | sh
```

**On Windows**:
Download from https://ollama.ai/download

**Verify installation**:
```bash
ollama --version
```

#### Step 2: Download a Model

Ollama has a model library. Choose by your hardware:

**Small models (4-6GB VRAM)**:
```bash
# Mistral-7B (fast, good quality)
ollama pull mistral

# Llama 2 (good all-rounder)
ollama pull llama2

# Neural Chat (specialized for chat)
ollama pull neural-chat
```

**Larger models (8-16GB VRAM)**:
```bash
# Llama 2 13B (better quality)
ollama pull llama2:13b

# Mistral 8x7B (mixture of experts, very capable)
ollama pull mistral:8x7b
```

**Verify download**:
```bash
ollama list
```

Example output:
```
NAME                    ID              SIZE      MODIFIED
mistral:latest         2df5b74d4fcb    3.8 GB    2 minutes ago
llama2:latest          abfd8a2f4d58    3.8 GB    10 minutes ago
```

#### Step 3: Start Ollama Server

In a separate terminal:

```bash
# Start Ollama
ollama serve

# This will start at http://localhost:11434
```

**Verify it's running**:
```bash
curl http://localhost:11434/api/tags
```

Expected output (shows available models):
```json
{
  "models": [
    {
      "name": "mistral:latest",
      "modified_at": "2025-01-01T12:00:00.000000000Z",
      "size": 3800000000
    }
  ]
}
```

#### Step 4: Update Configuration

Edit `.env`:

```bash
# Use local LLM
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/api

# Specify which model to use
LLM_MODEL=mistral

# Adjust temperature (0.0 = deterministic, 1.0 = creative)
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=512
```

#### Step 5: Validate Configuration

```bash
# Check configuration
python -m backend.config_validator

# Expected output:
# ✓ LLM Provider: local
# ✓ LOCAL_LLM_URL is set
```

#### Step 6: Start Backend

```bash
python -m backend.main
```

**Expected output**:
```
✓ LLM Provider:       local
✓ LLM Model:          mistral
✓ Configuration valid
```

#### Step 7: Test Local LLM

```bash
# Query endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

**First query will be slow** (model loading) but subsequent queries are fast.

#### Step 8: Monitor Performance

**Check Ollama status**:
```bash
# View running models
ollama ps

# Expected output:
# NAME            ID              SIZE        PROCESSOR         UNTIL
# mistral:latest  2df5b74d4fcb    3.8 GB      100% GPU          4 minutes from now
```

**Monitor memory usage**:
```bash
# On Linux
watch -n 1 free -h

# On macOS
top -l 1 | head -20
```

#### Switching Models

Change the model anytime:

```bash
# Update .env
LLM_MODEL=llama2

# Restart backend
python -m backend.main
```

---

### Option 2: LM Studio (GUI Alternative)

LM Studio provides a graphical interface for managing local models.

#### Step 1: Install LM Studio

Download from https://lmstudio.ai

#### Step 2: Download Model

1. Open LM Studio
2. Click "Search" in left sidebar
3. Search for "mistral" or "llama2"
4. Click "Download"
5. Wait for download to complete

#### Step 3: Start Server

1. Click "Local Server" in left sidebar
2. Select model from dropdown
3. Click "Start Server"
4. Note the API URL (usually `http://localhost:1234/v1`)

#### Step 4: Update Configuration

Edit `.env`:

```bash
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:1234/v1
LLM_MODEL=mistral
```

#### Step 5: Start Backend

```bash
python -m backend.main
```

---

### Option 3: Hugging Face Models (Full Control)

For maximum control, use Hugging Face models directly.

#### Step 1: Install Dependencies

```bash
pip install transformers torch accelerate
```

#### Step 2: Create LLM Server

Create `local_llm_server.py`:

```python
from fastapi import FastAPI
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

# Load model
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)

@app.post("/api/generate")
def generate(prompt: str, max_tokens: int = 512):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=max_tokens)
    response = tokenizer.decode(outputs[0])
    return {"generated_text": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

#### Step 3: Start Server

```bash
python local_llm_server.py

# Runs at http://localhost:8001
```

#### Step 4: Update Configuration

```bash
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:8001
LLM_MODEL=mistral
```

---

## Enabling Encryption

Encrypt your data at rest for added security.

### Step 1: Generate Encryption Key

```bash
# Generate 32-byte hex key
python << 'EOF'
import secrets
key = secrets.token_hex(32)
print(f"ENCRYPTION_KEY={key}")
EOF
```

**Output**:
```
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f
```

### Step 2: Configure Encryption

Edit `.env`:

```bash
# Enable encryption
ENCRYPTION_ENABLED=true

# Option A: Use generated key
ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f

# Option B: Derive from password
# ENCRYPTION_DERIVE_FROM_PASSWORD=true

# Encrypt which fields?
ENCRYPT_VECTOR_TEXTS=true
ENCRYPT_METADATA_FIELDS=source,author,subject
```

### Step 3: Validate Configuration

```bash
python -m backend.config_validator

# Expected:
# ✓ Encryption Enabled:   True
# ✓ Encryption Key:       ✓ Set
```

### Step 4: Restart Backend

```bash
python -m backend.main
```

All new documents will be encrypted automatically.

### Disabling Encryption

To disable (not recommended if data exists):

```bash
# Edit .env
ENCRYPTION_ENABLED=false

# Restart
python -m backend.main
```

---

## Memory Compaction

Automatically clean up old or duplicate data.

### Step 1: Enable Compaction

Edit `.env`:

```bash
# Enable automatic compaction
MEMORY_COMPACTION_ENABLED=true

# Run every 24 hours
MEMORY_COMPACTION_INTERVAL_HOURS=24

# Keep documents from last 365 days
MEMORY_COMPACTION_KEEP_DAYS=365

# Strategy: remove exact duplicates
MEMORY_COMPACTION_STRATEGY=deduplicate_exact
```

### Step 2: Configure Strategy

**Strategy 1: Deduplicate Exact** (Remove identical documents)

```bash
MEMORY_COMPACTION_STRATEGY=deduplicate_exact
```

**When to use**: When you upload the same file multiple times

**Strategy 2: Age-Based** (Remove old documents)

```bash
MEMORY_COMPACTION_STRATEGY=age_based
MEMORY_COMPACTION_KEEP_DAYS=180  # Keep last 6 months
```

**When to use**: When you want to retain only recent knowledge

### Step 3: Validate

```bash
python -m backend.config_validator

# Expected:
# ✓ Memory Compaction:    True
# ✓ Memory Compaction Interval: 24 hours
```

### Step 4: Start Backend

```bash
python -m backend.main
```

**Backend will**:
- Start compaction scheduler
- Run first cleanup after interval
- Log results

### Manual Compaction

Trigger compaction immediately:

```bash
# Via API
curl -X POST http://localhost:8000/compact \
  -H "Content-Type: application/json" \
  -d '{"strategy": "deduplicate_exact", "dry_run": false}'
```

---

## Daily Briefings

Get automatic summaries of your knowledge base.

### Step 1: Enable Briefings

Edit `.env`:

```bash
# Enable daily briefings
DAILY_BRIEFING_ENABLED=true

# Generate every 24 hours
DAILY_BRIEFING_INTERVAL_HOURS=24

# Summarize last 1 day of documents
DAILY_BRIEFING_LOOKBACK_DAYS=1

# Style of summary
DAILY_BRIEFING_SUMMARY_STYLE=executive
```

### Step 2: Choose Summary Style

**Style 1: Bullet Points** (Quick read)

```bash
DAILY_BRIEFING_SUMMARY_STYLE=bullet_points
```

Example output:
```
• Added 5 new documents about AI trends
• Main topics: LLMs, RAG, embeddings
• 23 new semantic chunks indexed
• 3 key insights from latest papers
```

**Style 2: Executive Summary** (Formal)

```bash
DAILY_BRIEFING_SUMMARY_STYLE=executive
```

Example output:
```
DAILY BRIEFING — December 9, 2025

SUMMARY:
The knowledge base grew by 5 documents today, primarily 
covering advances in retrieval-augmented generation...

KEY FINDINGS:
1. Vector embeddings show improved relevance
2. Chunking strategy reducing token waste by 15%
3. Reranking improving top-1 accuracy

METRICS:
Total documents: 245
New documents: 5
Avg chunk quality: 8.2/10
```

**Style 3: Narrative** (Detailed)

```bash
DAILY_BRIEFING_SUMMARY_STYLE=narrative
```

Example output:
```
Today was a productive day for the knowledge base...
```

### Step 3: Set Max Length

```bash
# Maximum characters in briefing (default 4000)
DAILY_BRIEFING_MAX_CHARS=4000
```

### Step 4: Configure

```bash
python -m backend.config_validator
```

### Step 5: View Briefing

Briefings appear in:
- **Dashboard**: `/stats` endpoint
- **Frontend**: Stats tab
- **Logs**: `backend.log`

---

## Reranking

Improve retrieval quality by reranking search results.

### Step 1: Choose Reranking Method

**Method 1: CrossEncoder (Best Quality)**

Reranks by measuring relevance between query and document.

```bash
pip install sentence-transformers
```

**Method 2: LLM-based (Most Accurate)**

Uses your LLM to score relevance.

**Method 3: Hybrid (Balanced)**

Combines embeddings and keyword matching.

### Step 2: Enable in Code

Edit `backend/core/retriever.py`:

```python
from sentence_transformers import CrossEncoder

# Initialize reranker
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def retrieve_and_rerank(query, top_k=10, rerank_k=3):
    # Get initial candidates
    candidates = vector_store.search(query, top_k=top_k)
    
    # Rerank with CrossEncoder
    scores = reranker.predict([
        [query, doc.text] for doc in candidates
    ])
    
    # Return top reranked
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in ranked[:rerank_k]]
```

### Step 3: Configure Parameters

```bash
# In .env or config
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_K=3  # Return top 3 after reranking
```

### Step 4: Test

```bash
# Query will now use reranking
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'
```

**Results will be**:
- ✅ More relevant
- ✅ Better ordered
- ⚠️ Slightly slower (2-3s added)

---

## Complete Example: Production Setup

Here's a complete `.env` for a production-grade setup:

```bash
# Environment
ENVIRONMENT=production

# LLM: Local with good balance
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/api
LLM_MODEL=mistral
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1024

# Vector Store: FAISS for speed
VECTOR_STORE_TYPE=faiss
VECTOR_STORE_PATH=data/faiss_index
EMBEDDING_MODEL=text-embedding-3-small

# Security: Full encryption
ENCRYPTION_ENABLED=true
ENCRYPTION_KEY=<your-key-here>
ENCRYPT_VECTOR_TEXTS=true
ENCRYPT_METADATA_FIELDS=source,author,url

# Maintenance: Automated cleanup
MEMORY_COMPACTION_ENABLED=true
MEMORY_COMPACTION_INTERVAL_HOURS=24
MEMORY_COMPACTION_STRATEGY=deduplicate_exact

# Briefings: Daily updates
DAILY_BRIEFING_ENABLED=true
DAILY_BRIEFING_INTERVAL_HOURS=24
DAILY_BRIEFING_LOOKBACK_DAYS=7
DAILY_BRIEFING_SUMMARY_STYLE=executive

# Database
METADATA_DB_URL=sqlite:///data/metadata.db
```

## Troubleshooting

### Local LLM Not Responding

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
killall ollama
ollama serve
```

### FAISS Index Errors

```bash
# Rebuild FAISS index
rm -rf data/faiss_index
python -c "import faiss; ..."  # Create new index
```

### Encryption Key Lost

```bash
# Generate new key and update .env
# WARNING: Old encrypted data will be unreadable
python -c "import secrets; print(secrets.token_hex(32))"
```

### High Memory Usage

```bash
# Use smaller LLM model
LLM_MODEL=neural-chat  # Smaller than mistral

# Or reduce vector store
VECTOR_STORE_TYPE=chroma  # More memory-efficient than FAISS
```

## Next Steps

Now that you've configured optional features:

1. ✅ Choose vector store (Chroma/FAISS/Pinecone)
2. ✅ Set up LLM (Cloud/Local)
3. ✅ Enable encryption for sensitive data
4. ✅ Schedule maintenance with compaction
5. ✅ Get daily briefings
6. ✅ Improve retrieval with reranking

**For more help**:
- Check `CONFIGURATION_MANAGEMENT.md` for all config options
- Run `python -m backend.config_validator` to validate setup
- Check logs: `tail -f backend.log`
