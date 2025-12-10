# Getting Help

Quick navigation guide for finding answers about AfundiOS.

## 🆘 I Have a Problem

### Choose Your Issue Type

#### 1️⃣ Installation Failed
**Example**: "pip install fails" or "Python version error"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Installation Issues](./TROUBLESHOOTING_GUIDE.md#installation-issues)

**Common solutions**:
- Python 3.11+ required
- Virtual environment issues
- Permission denied errors
- Database lock errors

---

#### 2️⃣ Configuration Error
**Example**: "KeyError: OPENAI_API_KEY" or "Invalid API key"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Configuration Issues](./TROUBLESHOOTING_GUIDE.md#configuration-issues)

**Common solutions**:
- Missing .env file
- API key not set correctly
- Port already in use
- Vector store path not found

**Also helpful**:
- [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) — How to configure
- [CONFIG_QUICK_REFERENCE.md](./CONFIG_QUICK_REFERENCE.md) — All settings listed

---

#### 3️⃣ Backend Won't Start
**Example**: "Uvicorn error" or "Backend crashes"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Backend Issues](./TROUBLESHOOTING_GUIDE.md#backend-issues)

**Common solutions**:
- Syntax errors in code
- Import errors
- Configuration validation failed
- Port conflict

**Debug steps**:
```bash
python -m backend.config_validator  # Check config
python -m py_compile backend/main.py  # Check syntax
PYTHONUNBUFFERED=1 python -m backend.main  # Verbose output
```

---

#### 4️⃣ Frontend Issues
**Example**: "Streamlit won't load" or "Backend unreachable"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Frontend Issues](./TROUBLESHOOTING_GUIDE.md#frontend-issues)

**Common solutions**:
- Backend not running
- Port conflict
- CORS issue
- Cache problem

**Test backend connectivity**:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

---

#### 5️⃣ No Results from Queries
**Example**: "Query returns empty" or "Documents not found"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Data & Vector Store Issues](./TROUBLESHOOTING_GUIDE.md#data--vector-store-issues)

**Common solutions**:
- No documents ingested yet
- Vector store not initialized
- Embedder not working
- Wrong vector store type

**Check vector store**:
```bash
curl http://localhost:8000/vector_store/info
# Should show documents > 0
```

---

#### 6️⃣ Slow Performance
**Example**: "Queries take 30+ seconds" or "Memory usage high"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Performance Issues](./TROUBLESHOOTING_GUIDE.md#performance-issues)

**Common solutions**:
- Using slow embedding model
- Batch size too large
- Reranking enabled (disable for speed)
- High memory usage (reduce chunk size)

---

#### 7️⃣ Docker Issues
**Example**: "Docker build fails" or "Container won't start"

→ Go to: [TROUBLESHOOTING_GUIDE.md - Docker Issues](./TROUBLESHOOTING_GUIDE.md#docker-issues)

**Common solutions**:
- Docker not installed
- Image build error
- Port conflict
- Container exits immediately

---

#### 8️⃣ API Issues
**Example**: "Timeout errors" or "Rate limited"

→ Go to: [TROUBLESHOOTING_GUIDE.md - LLM & API Issues](./TROUBLESHOOTING_GUIDE.md#llm--api-issues)

**Common solutions**:
- API key invalid
- Rate limit exceeded
- Timeout too short
- Network connectivity issue

---

## 🤔 I Have a Question

### Choose Your Question Type

#### "How do I get started?"
→ [CONTRIBUTOR_QUICK_START.md](./CONTRIBUTOR_QUICK_START.md) — 15-minute setup guide

```bash
# Quick start (5 minutes):
1. Clone repo
2. Create virtual environment
3. Install dependencies
4. Configure .env
5. Run backend and frontend
```

---

#### "How do I configure the system?"
→ [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) — Complete config guide

**Includes**:
- All environment variables
- Provider setup (OpenAI, Anthropic, Cohere, Local)
- Vector store configuration
- Validation & testing

**Quick reference**: [CONFIG_QUICK_REFERENCE.md](./CONFIG_QUICK_REFERENCE.md)

---

#### "What API endpoints are available?"
→ [API_REFERENCE.md](./API_REFERENCE.md) — Complete REST API docs

**Includes**:
- All 15+ endpoints documented
- Request/response examples
- Status codes & errors
- Integration code examples

**Example endpoints**:
- `POST /ingest` — Upload files
- `POST /query` — Ask questions
- `GET /health` — Check health
- `GET /stats` — Get statistics

---

#### "How do I use FAISS instead of Chroma?"
→ [OPTIONAL_FEATURES_GUIDE.md - Switching Vector Stores](./OPTIONAL_FEATURES_GUIDE.md#switching-vector-stores)

**Step-by-step**:
1. Install FAISS: `pip install faiss-cpu`
2. Set `VECTOR_STORE_TYPE=faiss` in .env
3. Rebuild index: `python scripts/rebuild_index.py`
4. Test and verify

**Time**: 15 minutes

---

#### "How do I use a local LLM like Ollama?"
→ [OPTIONAL_FEATURES_GUIDE.md - Using Local LLMs](./OPTIONAL_FEATURES_GUIDE.md#using-local-llms)

**Options**:
- **Ollama** (easiest): 20 minutes to set up
- **LM Studio** (GUI): 15 minutes
- **Hugging Face**: 20 minutes

**Steps for Ollama**:
1. Install: `brew install ollama` (macOS)
2. Download model: `ollama pull mistral`
3. Start server: `ollama serve`
4. Configure: Set `LLM_PROVIDER=local` in .env
5. Test

---

#### "How do I add a new feature (new file type, new LLM, etc.)?"
→ [FEATURE_IMPLEMENTATION_GUIDE.md](./FEATURE_IMPLEMENTATION_GUIDE.md)

**Examples**:
- Adding `.docx` file support
- Adding new vector store (Weaviate)
- Adding new LLM provider (Cohere)
- Adding reranking
- Custom chunking strategies

**Process**: Read 20 min + implement 3-8 hours

---

#### "How do I understand the architecture?"
→ [README.md - Architecture](./README.md)

**Or**: [CONTRIBUTOR_QUICK_START.md - What You Built](./CONTRIBUTOR_QUICK_START.md#what-you-built)

**Key components**:
- Backend (FastAPI)
- Frontend (Streamlit)
- Vector store (Chroma/FAISS/Pinecone)
- LLM API (OpenAI/Anthropic/local)
- Retrieval pipeline (RAG)

---

#### "How do I deploy to production?"
→ [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

**Options**:
- Docker & Docker Compose (local)
- AWS App Runner (easiest cloud)
- AWS ECS (more control)
- Google Cloud Run (recommended GCP)
- Google Compute Engine (full control)

**Typical time**: 2-4 hours depending on platform

---

#### "How does error handling work?"
→ [FRONTEND_ERROR_STATUS.md](./FRONTEND_ERROR_STATUS.md)

**Includes**:
- Error types & classification
- Retry logic
- Offline mode
- User-friendly messages
- Monitoring & logging

---

## 🚀 I Want to...

### ...set up the system from scratch
1. [CONTRIBUTOR_QUICK_START.md](./CONTRIBUTOR_QUICK_START.md) (15 min setup)
2. [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) (configure API keys)
3. Run tests to verify

---

### ...understand what I can do
1. [README.md](./README.md) (overview)
2. [API_REFERENCE.md](./API_REFERENCE.md) (endpoints)
3. [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md) (advanced features)

---

### ...implement a new feature
1. [FEATURE_IMPLEMENTATION_GUIDE.md](./FEATURE_IMPLEMENTATION_GUIDE.md) (step-by-step)
2. Follow the example (e.g., new file type support)
3. Write tests
4. Submit PR

---

### ...deploy to production
1. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) (choose platform)
2. [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) (production config)
3. Follow deployment checklist

---

### ...fix a problem
1. [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) (find your issue)
2. Follow solution steps
3. Test that it works
4. Create issue if not solved

---

### ...scale to handle more load
See [DEPLOYMENT_GUIDE.md - Auto-Scaling](./DEPLOYMENT_GUIDE.md#auto-scaling)

---

### ...monitor production systems
See [DEPLOYMENT_GUIDE.md - Monitoring & Maintenance](./DEPLOYMENT_GUIDE.md#monitoring--maintenance)

---

## 📚 Documentation Map

```
README.md (Start here!)
│
├─ CONTRIBUTOR_QUICK_START.md ──→ 15-minute setup
│
├─ CONFIGURATION_MANAGEMENT.md ──→ How to configure
│  ├─ CONFIG_QUICK_REFERENCE.md ──→ Quick lookup
│  └─ CONFIGURATION_CHECKLIST.md ──→ Verify setup
│
├─ OPTIONAL_FEATURES_GUIDE.md ──→ Advanced features
│  ├─ Vector stores (FAISS, Pinecone, etc.)
│  ├─ Local LLMs (Ollama, LM Studio, etc.)
│  └─ Other features (encryption, briefings, etc.)
│
├─ FEATURE_IMPLEMENTATION_GUIDE.md ──→ Build new features
│
├─ API_REFERENCE.md ──→ REST API docs
│
├─ DEPLOYMENT_GUIDE.md ──→ Production deployment
│
├─ TROUBLESHOOTING_GUIDE.md ──→ Fix problems
│
└─ DOCUMENTATION_SUMMARY.md ──→ This overview
```

---

## ⚡ Quick Answers

**Q: What Python version do I need?**  
A: Python 3.11 or higher

**Q: Is this free to use?**  
A: Yes, with API costs for LLM providers

**Q: Can I use it offline?**  
A: Yes, with local LLMs (Ollama)

**Q: How many documents can it handle?**  
A: Depends on vector store, but 1000s with Chroma, millions with Pinecone

**Q: Can I add my own file types?**  
A: Yes, see [FEATURE_IMPLEMENTATION_GUIDE.md](./FEATURE_IMPLEMENTATION_GUIDE.md)

**Q: How do I switch from OpenAI to local LLM?**  
A: Follow [OPTIONAL_FEATURES_GUIDE.md - Using Local LLMs](./OPTIONAL_FEATURES_GUIDE.md#using-local-llms)

**Q: Is this production-ready?**  
A: Yes, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for production setup

**Q: What about data privacy?**  
A: You control everything. Data stays on your server. Optional encryption available.

---

## 🎓 Learning Path

### Level 1: Beginner (1-2 days)
- [ ] Read README.md
- [ ] Follow CONTRIBUTOR_QUICK_START.md (15 min setup)
- [ ] Configure system (CONFIGURATION_MANAGEMENT.md)
- [ ] Ingest some documents
- [ ] Ask questions via the API or frontend
- [ ] Explore API_REFERENCE.md

### Level 2: Intermediate (1 week)
- [ ] Explore OPTIONAL_FEATURES_GUIDE.md
- [ ] Try different vector stores (FAISS)
- [ ] Try local LLM (Ollama)
- [ ] Read FEATURE_IMPLEMENTATION_GUIDE.md
- [ ] Implement a small feature (new file type)
- [ ] Learn about deployment (DEPLOYMENT_GUIDE.md)

### Level 3: Advanced (2+ weeks)
- [ ] Deploy to production
- [ ] Set up monitoring
- [ ] Implement advanced features
- [ ] Optimize performance
- [ ] Contribute to codebase
- [ ] Help others troubleshoot

---

## 💬 How to Get Help

### Before Asking for Help
1. Check [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)
2. Search documentation for your issue
3. Check existing GitHub issues
4. Review error messages carefully

### Where to Ask
- **GitHub Issues**: For bugs or feature requests
- **Discussions**: For questions & ideas
- **Documentation**: First place to check (you are here!)

### When Asking
**Include**:
- What you're trying to do
- What error/problem you're experiencing
- Steps to reproduce
- Your environment (OS, Python version, etc.)
- Relevant error messages or logs

**Example**:
```
Issue: Backend won't start after configuration
Error: ModuleNotFoundError: No module named 'anthropic'
OS: Ubuntu 22.04
Python: 3.11.1
Steps:
1. Cloned repo
2. Created venv
3. Installed requirements.txt
4. Set ANTHROPIC_API_KEY in .env
5. Ran: python -m backend.main

Expected: Server starts
Actual: Import error (see log below)
```

---

## 🔗 Useful Links Summary

| Need | Link | Time |
|------|------|------|
| Quick setup | [CONTRIBUTOR_QUICK_START.md](./CONTRIBUTOR_QUICK_START.md) | 15 min |
| Configuration | [CONFIGURATION_MANAGEMENT.md](./CONFIGURATION_MANAGEMENT.md) | 20 min |
| API docs | [API_REFERENCE.md](./API_REFERENCE.md) | 30 min |
| Fix problem | [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) | 5-20 min |
| Deploy | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | 1-2 hrs |
| New feature | [FEATURE_IMPLEMENTATION_GUIDE.md](./FEATURE_IMPLEMENTATION_GUIDE.md) | 20 min read |
| Advanced features | [OPTIONAL_FEATURES_GUIDE.md](./OPTIONAL_FEATURES_GUIDE.md) | 30-60 min |
| Overview | [DOCUMENTATION_SUMMARY.md](./DOCUMENTATION_SUMMARY.md) | 10 min |

---

## ✅ Everything You Need to Know

This documentation covers:
- ✅ Getting started (15 minutes)
- ✅ Configuration (all options)
- ✅ API reference (all endpoints)
- ✅ Features (all options)
- ✅ Troubleshooting (40+ issues)
- ✅ Deployment (local to production)
- ✅ Development (how to add features)
- ✅ Error handling (how errors are managed)

**You're fully equipped to use AfundiOS!** 🚀

---

**Last Updated**: January 2024  
**Documentation Status**: Complete & Comprehensive  
**Coverage**: All aspects of AfundiOS development, deployment, and usage
