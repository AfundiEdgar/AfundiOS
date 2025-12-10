# Contributor Quick Start Guide

Welcome to AfundiOS! This guide gets new developers productive in 15 minutes.

## 📋 Prerequisites Check

Before starting, verify you have:

```bash
# Python 3.11+
python --version

# Git
git --version

# pip (Python package manager)
pip --version
```

## ⏱️ 15-Minute Setup

### Minute 1-2: Clone & Environment

```bash
# Clone repository
git clone https://github.com/yourname/afundios.git
cd afundios

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### Minute 3-5: Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import streamlit; print('✓ All dependencies installed')"
```

### Minute 6-8: Configure

```bash
# Copy configuration template
cp .env.example .env

# Open .env in your editor and add:
# 1. LLM_PROVIDER=openai (or another)
# 2. OPENAI_API_KEY=sk-your-key
# 3. Save file

echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=sk-your-key" >> .env  # Replace with real key
```

### Minute 9-12: Validate & Start

```bash
# Terminal 1: Validate configuration
python -m backend.config_validator

# Expected: ✅ Configuration is valid

# Start backend
python -m backend.main
```

```bash
# Terminal 2: Start frontend
streamlit run frontend/app.py

# Opens at http://localhost:8501
```

### Minute 13-15: Test It!

1. Open http://localhost:8501
2. Upload a test file (PDF, TXT, or webpage)
3. Ask a question about it
4. See AI-powered answer with sources

**Done!** ✅ You're running AfundiOS locally.

---

## 🎯 What You Just Built

```
┌─────────────────────────────────────────┐
│  Streamlit Web Interface (Port 8501)    │
└──────────────────┬──────────────────────┘
                   │
        REST API (FastAPI)
                   │
┌──────────────────┴──────────────────────┐
│        Backend Core Pipeline            │
├──────────────┬──────────────┬───────────┤
│ Ingestion    │ Retrieval    │ LLM       │
│ - Extract    │ - Embedding  │ - Query   │
│ - Chunk      │ - Vector DB  │ - Answer  │
│ - Embed      │ - Rerank     │ - Cite    │
└──────────────┴──────────────┴───────────┘
```

---

## 📁 Key Files for Development

### Backend Core
```
backend/
├── main.py                 # FastAPI app entry point
├── config.py               # Configuration with validation
├── core/
│   ├── extractor.py        # Text extraction (PDF, Web, etc.)
│   ├── chunker.py          # Text chunking strategies
│   ├── embedder.py         # Convert text to embeddings
│   ├── vectorstore.py      # Vector database (Chroma/FAISS)
│   ├── retriever.py        # Semantic search + reranking
│   └── llm.py              # LLM API calls
├── api/
│   ├── ingest.py           # POST /ingest endpoint
│   ├── query.py            # POST /query endpoint
│   └── router.py           # API route setup
└── tests/                  # Unit tests
```

### Frontend
```
frontend/
├── app.py                  # Streamlit main app
├── components/             # Reusable UI components
├── pages/                  # Multi-page sections
└── utils/                  # Helper functions
```

---

## 🔧 Common Development Tasks

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_api.py -v

# Specific test function
pytest tests/test_api.py::test_ingest_pdf -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

### Check Configuration

```bash
# Validate your .env
python -m backend.config_validator
```

### View API Documentation

1. Start backend: `python -m backend.main`
2. Open http://localhost:8000/docs
3. See all endpoints and try them interactively

### Check Code Quality

```bash
# Linting (if you installed it)
flake8 backend/ --max-line-length=100

# Type checking
mypy backend/

# Format code
black backend/
```

### Add Debug Logging

```python
# In your code
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing document: {filename}")
logger.debug(f"Chunks created: {len(chunks)}")
logger.error(f"Error: {e}")
```

View logs:
```bash
# From backend terminal
# Logs appear in real-time

# Or check log file
tail -f backend.log
```

---

## 🚀 Common Development Workflows

### Workflow 1: Add Support for New File Type

Example: Support `.docx` files

**Step 1**: Add extractor
```python
# In backend/core/extractor.py
def extract_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return '\n'.join([p.text for p in doc.paragraphs])
```

**Step 2**: Register in ingest
```python
# In backend/api/ingest.py
if file.filename.endswith('.docx'):
    text = extract_docx(temp_file.name)
```

**Step 3**: Add test
```python
# In tests/test_ingestion.py
def test_ingest_docx():
    response = client.post('/ingest', files={'file': ...})
    assert response.status_code == 200
```

**Step 4**: Document it
```bash
# Update README
# Add to supported formats list
```

### Workflow 2: Change Vector Store

See [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md#switching-vector-stores)

Quick version:
```bash
# Edit .env
VECTOR_STORE_TYPE=faiss

# Restart backend
python -m backend.main
```

### Workflow 3: Switch to Local LLM

See [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md#using-local-llms)

Quick version:
```bash
# Install Ollama
# Download model: ollama pull mistral
# Start server: ollama serve

# Edit .env
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:11434/api
LLM_MODEL=mistral

# Restart backend
python -m backend.main
```

---

## 🐛 Debugging Tips

### Issue: "Configuration Error"

```bash
# Validate configuration
python -m backend.config_validator

# Check .env exists
ls -la .env

# Verify API key format
grep OPENAI_API_KEY .env
```

### Issue: Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Check for port conflicts
lsof -i :8000  # On macOS/Linux
```

### Issue: Frontend Shows Errors

```bash
# Check backend is running
curl http://localhost:8000/health

# Check Streamlit logs
# Should see output in terminal
```

### Issue: Slow Performance

```bash
# Check which LLM you're using
grep LLM_PROVIDER .env

# Switch to faster model
# Edit LLM_MODEL in .env

# Restart backend
python -m backend.main
```

---

## 📚 Next Steps After Setup

### 1. Understand the Architecture

Read the Project Structure section in [README.md](./README.md)

### 2. Explore Optional Features

See [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md):
- [ ] Try FAISS vector store
- [ ] Set up local LLM with Ollama
- [ ] Enable encryption
- [ ] Configure daily briefings

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Read Configuration Guide

[CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md)

### 5. Make Your First Change

Pick something small:
- Add a new extractor
- Improve error messages
- Add a test
- Update documentation

### 6. Create a Pull Request

When ready:
```bash
git checkout -b feature/my-feature
# Make changes...
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
# Create PR on GitHub
```

---

## ❓ Getting Help

### Check Existing Docs

- **Quick reference**: README.md
- **Optional features**: OPTIONAL_FEATURES_GUIDE.md
- **Configuration**: CONFIGURATION_MANAGEMENT.md
- **API docs**: http://localhost:8000/docs (when running)

### Validate Configuration

```bash
python -m backend.config_validator
```

### Check Logs

Backend logs show what's happening:
```bash
# Terminal running backend shows logs
# Or check file:
tail -f backend.log
```

### Test Your Changes

```bash
# Before submitting PR
pytest tests/ -v

# Check code quality
flake8 backend/ --max-line-length=100
```

---

## 🎓 Learning Resources

### Understanding RAG

RAG = Retrieval-Augmented Generation

1. **Retrieval**: Search knowledge base for relevant documents
2. **Augmentation**: Add context to LLM prompt
3. **Generation**: LLM answers with cited sources

See: https://python.langchain.com/docs/use_cases/question_answering/

### Understanding Embeddings

Embeddings = vectors that capture semantic meaning

```python
# Text becomes vector
"What is AI?" → [0.1, 0.2, 0.3, ..., 0.9]

# Similar texts have similar vectors
"What is artificial intelligence?" → [0.1, 0.2, 0.3, ..., 0.9]
```

### Understanding Vector Databases

Store and search embeddings efficiently

```
Query embedding → Find similar document embeddings → Return documents
```

---

## ✅ Success Criteria

You've successfully set up AfundiOS when:

- ✅ `python -m backend.config_validator` shows green checks
- ✅ Backend starts at `http://localhost:8000/docs`
- ✅ Frontend opens at `http://localhost:8501`
- ✅ You can upload a file
- ✅ You can ask a question
- ✅ You get an answer with sources
- ✅ `pytest tests/ -v` shows all tests passing

---

## 🎉 Ready to Contribute?

Great! Here's the workflow:

1. ✅ Setup complete (you are here)
2. Pick an issue or feature
3. Create a branch: `git checkout -b feature/name`
4. Make changes + test
5. Commit: `git commit -m "Description"`
6. Push: `git push origin feature/name`
7. Create Pull Request

---

## 📞 Questions?

Check these in order:

1. This guide (Contributor Quick Start)
2. README.md (Overview)
3. OPTIONAL_FEATURES_GUIDE.md (Specific features)
4. CONFIGURATION_MANAGEMENT.md (Configuration)
5. API docs: http://localhost:8000/docs (When running)
6. Check logs/errors from `python -m backend.config_validator`

---

**Welcome to AfundiOS! Happy coding!** 🚀
