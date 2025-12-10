

🧠 AfundiOS — Your Personal AI Operating System
A full-stack RAG platform that ingests your knowledge, stores it, and answers with context.

AfundiOS is a personal AI memory engine that lets you upload files, scrape websites, ingest YouTube videos, and build your own private knowledge base. It retrieves what you’ve learned, synthesizes it using LLMs, and behaves like an AI assistant that “remembers everything you feed it.”

This project demonstrates production-grade AI engineering, including:

Retrieval-Augmented Generation (RAG)

Vector databases

Embedding pipelines

Agent-style reasoning

Full-stack architecture (FastAPI + Streamlit/Next.js)

Document ingestion + text extraction

Docker containerization

Clean API design
🚀 Features
🔍 Intelligent RAG Query Engine

Ask natural language questions and get:

synthesized answers

citations

source documents and highlighted chunks

📥 Multi-Source Ingestion

Upload or link:

PDFs

Markdown

Text files

Entire webpages

YouTube videos (Whisper transcript)

🧩 Modular AI Pipeline

Automatic text extraction

Semantic chunking

Embedding generation

Vector storage (Chroma/FAISS)

Reranking

LLM synthesis

📊 Knowledge Dashboard

See:

total documents

total chunks

timeline of ingestion

topic distribution

most queried themes

💬 Real-Time Chat Interface

A clean interface for conversational interaction with your knowledge base.

🔐 Private by Default

Local vector stores, optional encryption, no cloud syncing.

                ┌───────────────────┐
                │     Frontend      │
                │ Streamlit/Next.js │
                └─────────┬─────────┘
                          │ REST API
                ┌─────────▼─────────┐
                │      FastAPI       │
                │  (Backend Layer)    │
                └─────────┬─────────┘
           ┌──────────────┼────────────────┐
           │               │                │
 ┌─────────▼──────┐ ┌─────▼────────┐ ┌─────▼────────┐
 │  Extraction     │ │  Embeddings   │ │   LLM Layer  │
 │ (PDF, Web, YT)  │ │ (Chroma/FAISS)│ │ (OpenAI etc.)│
 └─────────┬──────┘ └─────┬────────┘ └─────┬────────┘
           │               │                │
           └───────────────┴────────────────┘
               End-to-End RAG Pipeline
📚 Tech Stack
Backend

Python

FastAPI

LangChain / LlamaIndex

ChromaDB or FAISS

OpenAI APIs

Whisper for transcription

Frontend

Streamlit (simple)
or

Next.js + Tailwind (polished)

Deployment

Docker

Render / Vercel
📦 Project Structure
afundios/
│
├── backend/
│   ├── api/
│   │   ├── ingest.py
│   │   ├── query.py
│   │   ├── health.py
│   │   └── models.py
│   ├── core/
│   │   ├── extractor.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── retriever.py
│   │   ├── llm.py
│   │   └── config.py
│   ├── db/
│   │   ├── vector_store.py
│   │   └── metadata.py
│   └── main.py
│
├── frontend/
│   ├── pages/
│   ├── components/
│   └── utils/
│
├── scripts/
│   ├── ingest_folder.py
│   └── rebuild_index.py
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_query.py
│   └── test_api.py
│
└── docker-compose.yml
⚙️ API Endpoints
POST /ingest

Uploads a file or URL into the knowledge base.

POST /query

Runs full RAG retrieval + LLM synthesis.

GET /stats

Returns DB statistics and memory analytics.
🔥 How It Works (RAG Pipeline)
1. Ingestion
File/URL → Extract → Clean → Chunk → Embed → Store

2. Retrieval
Query → Embed → Retrieve top-K → Rerank

3. Synthesis
Chunks → LLM → Structured Answer + Citations

🧪 Quick Start

### Prerequisites
- Python 3.11+
- pip or conda
- 4GB RAM minimum

### 1. Clone & Setup

```bash
git clone https://github.com/yourname/afundios.git
cd afundios

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy configuration template
cp .env.example .env

# Edit with your API keys
nano .env  # or use your editor

# Validate configuration
python -m backend.config_validator
```

**Required for basic usage**:
- `OPENAI_API_KEY` (or other LLM provider key)
- `ENVIRONMENT=local`
- `VECTOR_STORE_TYPE=chroma` (default)

### 3. Run Backend

```bash
# Terminal 1: Start backend API
python -m backend.main
# or
uvicorn backend.main:app --reload
```

**Expected output**:
```
✓ Configuration valid
✓ Vector store initialized
✓ Uvicorn running on http://127.0.0.1:8000
```

### 4. Run Frontend

**Option A: Streamlit (Simple & Fast)**

```bash
# Terminal 2: Start Streamlit
streamlit run frontend/app.py
```

Open http://localhost:8501

**Option B: Next.js (Polished UI)**

```bash
# Terminal 2
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### 5. Test the System

**Via Frontend**:
1. Upload a PDF or text file
2. Ask a question about it
3. See cited sources

**Via API**:
```bash
# Upload a file
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.pdf"

# Ask a question
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# Get statistics
curl http://localhost:8000/stats
```

---

## 📖 Getting Started for Contributors

### For New Developers

1. **Start here**: Read this README for overview
2. **Setup**: Follow Quick Start above
3. **Optional Features**: Read [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md)
   - Switching vector stores (Chroma → FAISS → Pinecone)
   - Using local LLMs (Ollama, LM Studio)
   - Enabling encryption
   - Setting up automated maintenance

4. **Configuration**: Check [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md)
   - All available options
   - Validation rules
   - Error messages

5. **Testing**: Run tests
   ```bash
   pytest tests/ -v
   ```

6. **Architecture**: See Project Structure section below

### Common Development Tasks

#### Run Tests
```bash
pytest tests/ -v
pytest tests/test_api.py -k "ingest" -v
pytest tests/ --cov=backend
```

#### Check Configuration
```bash
python -m backend.config_validator
```

#### View API Documentation
```
http://localhost:8000/docs
```

#### Check Code Quality
```bash
# Linting (if installed)
flake8 backend/
pylint backend/

# Type checking (if installed)
mypy backend/
```

#### Add a New Feature

Example: Add support for a new file type

1. **Add extractor** in `backend/core/extractor.py`
   ```python
   def extract_xyz(file_path: str) -> str:
       """Extract text from .xyz files"""
       # Implementation
       return text
   ```

2. **Add to ingest pipeline** in `backend/api/ingest.py`
   ```python
   if file.filename.endswith('.xyz'):
       text = extract_xyz(temp_file.name)
   ```

3. **Add test** in `tests/test_ingestion.py`
   ```python
   def test_ingest_xyz():
       # Test implementation
       assert result.chunks > 0
   ```

4. **Update docs** in README.md

---

## 🛠️ Advanced Configuration

Not sure which features to enable? Here are preset configurations:

### 🚀 Production Setup
```bash
# See OPTIONAL_FEATURES_GUIDE.md: "Complete Example: Production Setup"
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/api
VECTOR_STORE_TYPE=faiss
ENCRYPTION_ENABLED=true
MEMORY_COMPACTION_ENABLED=true
DAILY_BRIEFING_ENABLED=true
```

### 🎓 Development Setup
```bash
# Fast iteration with cloud LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
VECTOR_STORE_TYPE=chroma
ENCRYPTION_ENABLED=false
MEMORY_COMPACTION_ENABLED=false
```

### 🔬 Experimental Setup
```bash
# Test new features
VECTOR_STORE_TYPE=pinecone
LLM_PROVIDER=anthropic
ENCRYPTION_ENABLED=true
DAILY_BRIEFING_ENABLED=true
```

---

## 📚 Complete Documentation Index

**See [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) for complete reference of all 37 documentation files (15,000+ lines)**

### Essential Reading (Start Here!)

1. **[README.md](./README.md)** ← You are here
2. **[CONTRIBUTOR_QUICK_START.md](./CONTRIBUTOR_QUICK_START.md)** — 15-minute setup
3. **[GETTING_HELP.md](./GETTING_HELP.md)** — Help & navigation guide

### Core Documentation

| Document | Purpose | Time |
|----------|---------|------|
| [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) | Configure API keys & settings | 20 min |
| [API_REFERENCE.md](./API_REFERENCE.md) | All REST endpoints with examples | 30 min |
| [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md) | Advanced features (vector stores, local LLMs, etc.) | 30-60 min |
| [FEATURE_IMPLEMENTATION_GUIDE.md](./FEATURE_IMPLEMENTATION_GUIDE.md) | How to add new features | 20 min read |
| [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) | Fix 50+ common issues | 5-30 min |
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | Deploy to production (AWS, GCP, Docker) | 1-2 hrs |

### Quick Reference by Use Case

| I want to... | Read... | Time |
|-------------|---------|------|
| Get started in 15 min | [CONTRIBUTOR_QUICK_START.md](./CONTRIBUTOR_QUICK_START.md) | 15 min |
| Configure system | [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) | 20 min |
| Find help | [GETTING_HELP.md](./GETTING_HELP.md) | 5 min |
| Understand API | [API_REFERENCE.md](./API_REFERENCE.md) | 30 min |
| Use advanced features | [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md) | 30-60 min |
| Add a feature | [FEATURE_IMPLEMENTATION_GUIDE.md](./FEATURE_IMPLEMENTATION_GUIDE.md) | 20 min |
| Fix a problem | [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) | 5-30 min |
| Deploy to production | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | 2-4 hrs |
| See all docs | [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) | 10 min |

---

## 🧪 Running Locally (Legacy)

For quick reference, the minimal setup:

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run backend
python -m backend.main

# 4. Run frontend
streamlit run frontend/app.py
```

📈 Roadmap / Stretch Features

🌐 Offline mode using local Llama models

🔐 Encrypted vector store

🧠 Graph-based memory visualization

✨ Agents (Planner + Critic + Summarizer)

🌓 Automatic long-term memory compression

🔁 Scheduled daily briefings
👤 Author

Michael Edgar Afundi Malongo
AI Engineer — Focused on RAG, autonomous agents, and knowledge systems.
backend/
│
├── main.py
├── config.py
│
├── api/
│   ├── ingest.py
│   ├── query.py
│   ├── health.py
│   └── router.py
│
├── core/
│   ├── extractor.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── vectorstore.py
│   ├── retriever.py
│   ├── llm.py
│   └── pipeline.py
│
├── db/
│   ├── schemas.py
│   ├── metadata_store.py
│   └── vector_store/
│
├── utils/
│   ├── file_utils.py
│   ├── text_utils.py
│   ├── yt_utils.py
│   └── web_utils.py
│
└── models/
    ├── request_models.py
    ├── response_models.py
    └── llm_models.py
