# Troubleshooting Guide

Common issues and solutions for AfundiOS.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Backend Issues](#backend-issues)
4. [Frontend Issues](#frontend-issues)
5. [Data & Vector Store Issues](#data--vector-store-issues)
6. [LLM & API Issues](#llm--api-issues)
7. [Performance Issues](#performance-issues)
8. [Docker Issues](#docker-issues)

---

## Installation Issues

### Issue: Python Version Error

**Problem**: `Python 3.11+ required`

**Solution**:
```bash
# Check current version
python --version

# Install Python 3.11+
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11

# Windows
# Download from python.org or use choco/scoop

# Create virtual environment with correct version
python3.11 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### Issue: pip install fails with "No module named setuptools"

**Problem**: `ERROR: Could not find a version that satisfies the requirement setuptools`

**Solution**:
```bash
# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Then install requirements
pip install -r requirements.txt
```

### Issue: "Permission denied" on Linux/Mac

**Problem**: `OSError: [Errno 13] Permission denied`

**Solution**:
```bash
# Option 1: Use virtual environment (RECOMMENDED)
python3.11 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Option 2: Use --user flag
pip install --user -r requirements.txt

# Option 3: Fix ownership (if using sudo previously)
sudo chown -R $(whoami) ~/.local/lib/python3.11/
```

### Issue: Chroma database lock error

**Problem**: `Error: database is locked`

**Solution**:
```bash
# Option 1: Wait (if another process is using it)
# Check if backend is running elsewhere
ps aux | grep python

# Option 2: Remove lock file
rm -f backend/data/vector_store/chroma.sqlite3-shm
rm -f backend/data/vector_store/chroma.sqlite3-wal

# Option 3: Rebuild index
python scripts/rebuild_index.py
```

---

## Configuration Issues

### Issue: Missing API Key

**Problem**: `KeyError: 'OPENAI_API_KEY'` or similar

**Solution**:
```bash
# 1. Check .env file exists
ls -la .env

# 2. Verify key is set
cat .env | grep OPENAI_API_KEY

# 3. If missing, add to .env
echo "OPENAI_API_KEY=sk-..." >> .env

# 4. Reload environment
source .env  # Linux/Mac
# OR reload your terminal/IDE

# 5. Validate configuration
python -m backend.config_validator
```

Expected output:
```
✅ Environment variables validated
✅ LLM Configuration valid (Provider: openai)
✅ Vector Store Configuration valid
✅ All configurations OK
```

### Issue: Invalid API Key

**Problem**: `400 Bad Request: Invalid API key provided` or `403 Forbidden: API key not authorized`

**Solution**:
```bash
# 1. Check key format (should start with provider prefix)
echo $OPENAI_API_KEY  # Should be: sk-...

# 2. Verify key in API dashboard
# OpenAI: https://platform.openai.com/api-keys
# Anthropic: https://console.anthropic.com/
# Cohere: https://dashboard.cohere.ai/

# 3. Test API connectivity
# For OpenAI:
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 4. Replace key if expired
# Most APIs allow rotating keys without downtime
```

### Issue: Port Already in Use

**Problem**: `Address already in use` or `Cannot assign requested address`

**Solution**:
```bash
# Check what's using the port
# Linux/Mac
lsof -i :8000  # Backend port
lsof -i :8501  # Frontend port

# Windows
netstat -ano | findstr :8000

# Kill the process
# Linux/Mac
kill -9 <PID>

# Windows
taskkill /PID <PID> /F

# OR use different port
# Start backend on different port
BACKEND_PORT=8001 python -m backend.main

# Start frontend on different port
streamlit run frontend/app.py --server.port 8502
```

### Issue: Vector Store Path Not Found

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: 'backend/data/vector_store'`

**Solution**:
```bash
# Create missing directory
mkdir -p backend/data/vector_store

# Verify path in .env
cat .env | grep VECTOR_STORE_PATH

# Should be:
# VECTOR_STORE_PATH=backend/data/vector_store

# Rebuild index
python scripts/rebuild_index.py
```

---

## Backend Issues

### Issue: Backend Won't Start

**Problem**: Server crashes immediately or hangs

**Solution**:
```bash
# Step 1: Check Python version
python --version  # Should be 3.11+

# Step 2: Activate virtual environment
source env/bin/activate  # Linux/Mac
env\Scripts\activate     # Windows

# Step 3: Validate configuration
python -m backend.config_validator

# Step 4: Check for syntax errors
python -m py_compile backend/main.py
python -m py_compile backend/config.py

# Step 5: Start with verbose logging
PYTHONUNBUFFERED=1 python -m backend.main

# Step 6: Check logs for errors
tail -f backend/logs/app.log
```

### Issue: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'anthropic'` or similar

**Solution**:
```bash
# Reinstall requirements
pip install --upgrade pip
pip install -r requirements.txt

# Check what's installed
pip list | grep anthropic

# If missing, install specific package
pip install anthropic

# If version conflict, update
pip install --upgrade anthropic
```

### Issue: Slow Ingestion

**Problem**: File upload hangs or times out

**Solution**:
```bash
# Check file size (backend limits 100MB by default)
ls -lh your_file.pdf

# If > 100MB, increase limit in backend/config.py
# Find MAX_FILE_SIZE and increase

# Check available disk space
df -h

# Check RAM usage during ingestion
top -p $(pgrep -f "python.*backend")

# If out of memory, reduce chunk size
# In .env:
CHUNK_SIZE=500  # Reduce from default 1000

# Process smaller files first
```

### Issue: Out of Memory (OOM)

**Problem**: `MemoryError` or process killed

**Solution**:
```bash
# Reduce chunk size
echo "CHUNK_SIZE=200" >> .env

# Use memory-efficient embedder
echo "EMBEDDER_BATCH_SIZE=32" >> .env  # Default 128

# Limit vector store in-memory cache
echo "VECTOR_STORE_CACHE_SIZE=100" >> .env

# Monitor memory usage
watch -n 1 free -h

# If persistent, use smaller embedding model
echo "EMBEDDER_MODEL=all-MiniLM-L6-v2" >> .env
```

### Issue: Timeout Errors

**Problem**: `ReadTimeout` or `ConnectTimeout` when calling LLM APIs

**Solution**:
```bash
# Increase timeout in .env
echo "LLM_TIMEOUT=60" >> .env  # Default 30

# Check network connectivity
ping api.openai.com

# Check API status pages
# OpenAI: status.openai.com
# Anthropic: status.anthropic.com

# Check rate limits
# Try again with exponential backoff

# Reduce request size
# Summarize long documents before querying
```

---

## Frontend Issues

### Issue: Frontend Won't Load

**Problem**: Blank screen or connection error

**Solution**:
```bash
# Check if Streamlit is running
ps aux | grep streamlit

# Activate virtual environment
cd frontend
source env/bin/activate  # Or env\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt

# Run with verbose logging
streamlit run app.py --logger.level=debug

# Check for port conflicts
lsof -i :8501

# Use different port
streamlit run app.py --server.port 8502
```

### Issue: "Backend is unreachable"

**Problem**: Frontend can't connect to backend API

**Solution**:
```bash
# Step 1: Verify backend is running
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-01T12:00:00Z"}

# Step 2: Check firewall
# macOS: System Preferences > Security & Privacy > Firewall
# Linux: sudo ufw status
# Windows: Windows Defender Firewall

# Step 3: Verify backend URL in frontend
# Check frontend/config.py:
# BACKEND_URL should be "http://localhost:8000"

# Step 4: If running on different machine
# Update BACKEND_URL to actual IP
# frontend/config.py:
# BACKEND_URL = "http://192.168.1.100:8000"

# Step 5: Check CORS settings (backend/config.py)
# Should allow frontend origin

# Step 6: Test connectivity
curl -v http://localhost:8000/health
```

### Issue: Slow Frontend Response

**Problem**: UI lags, buttons unresponsive

**Solution**:
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/

# Reduce animation/animation settings
# In frontend/config.py set ANIMATION_ENABLED=false

# Check for memory leaks
# Monitor RAM while using app
watch -n 1 free -h

# Close other tabs/apps
# Streamlit runs in single thread

# Increase Streamlit memory limit
streamlit run app.py --client.maxMessageSize=200 --client.toolbarMode='minimal'
```

### Issue: File Upload Fails

**Problem**: `Upload failed` error when uploading file

**Solution**:
```bash
# Check file format
# Supported: PDF, TXT, MD, DOCX, XLSX, URLs, YouTube

# Check file size (must be < 100MB)
ls -lh your_file.pdf

# Check backend is accepting files
curl -F "file=@test.pdf" http://localhost:8000/ingest

# Check storage space
df -h | grep -E "/$|/home"

# Check temporary directory
ls -la /tmp  # Or %TEMP% on Windows

# Increase upload timeout in frontend/config.py
# REQUEST_TIMEOUT = 300  # 5 minutes
```

---

## Data & Vector Store Issues

### Issue: No Results from Query

**Problem**: "No relevant documents found" or empty results

**Solution**:
```bash
# Step 1: Verify data is ingested
# Check vector store size
ls -lh backend/data/vector_store/

# Step 2: Rebuild vector store
python scripts/rebuild_index.py

# Step 3: Ingest sample data
# Upload a test PDF or text file

# Step 4: Check embedder is working
python << 'EOF'
from backend.core.embedder import Embedder
embedder = Embedder()
result = embedder.embed("test")
print(f"Embedding created: {len(result)} dimensions")
EOF

# Step 5: Check retriever
python << 'EOF'
from backend.core.retriever import Retriever
retriever = Retriever()
results = retriever.retrieve("test query", top_k=3)
print(f"Found {len(results)} documents")
for r in results:
    print(f"- {r.metadata.get('source', 'Unknown')}")
EOF

# Step 6: Try switching vector store
echo "VECTOR_STORE_TYPE=faiss" >> .env
python scripts/rebuild_index.py
```

### Issue: Duplicate Documents

**Problem**: Same content appears multiple times in results

**Solution**:
```bash
# Enable deduplication
echo "MEMORY_COMPACTION_STRATEGY=deduplicate_exact" >> .env

# Manually trigger cleanup
python << 'EOF'
from backend.core.vectorstore import get_vector_store
from backend.config import settings

store = get_vector_store()
removed = store.deduplicate_exact()
print(f"Removed {removed} duplicate entries")
EOF

# Rebuild index if many duplicates
python scripts/rebuild_index.py
```

### Issue: Vector Store Corruption

**Problem**: `sqlite3.DatabaseError` or index won't load

**Solution**:
```bash
# Backup current data
cp -r backend/data/vector_store backend/data/vector_store.backup

# Remove corrupted database
rm -f backend/data/vector_store/chroma.sqlite3
rm -f backend/data/vector_store/chroma.sqlite3-shm
rm -f backend/data/vector_store/chroma.sqlite3-wal

# Rebuild index
python scripts/rebuild_index.py

# Verify
curl http://localhost:8000/stats | jq .documents

# Should show document count > 0
```

---

## LLM & API Issues

### Issue: LLM Response is Empty

**Problem**: Query returns no response or blank text

**Solution**:
```bash
# Test LLM connection
python << 'EOF'
from backend.core.llm import LLM
from backend.config import settings

llm = LLM(settings.llm_provider, settings.llm_model)
response = llm.generate("Say hello")
print(f"Response: {response}")
EOF

# Check API key
python -m backend.config_validator | grep LLM

# Check API rate limits
# Visit: https://platform.openai.com/account/billing/overview

# Increase timeout
echo "LLM_TIMEOUT=60" >> .env

# Reduce max tokens
echo "LLM_MAX_TOKENS=256" >> .env
```

### Issue: Slow LLM Responses

**Problem**: Queries take > 30 seconds

**Solution**:
```bash
# Switch to faster model
echo "LLM_MODEL=gpt-3.5-turbo" >> .env  # Instead of gpt-4

# Use local LLM (much faster)
# See: OPTIONAL_FEATURES_GUIDE.md > Using Local LLMs

# Reduce max tokens
echo "LLM_MAX_TOKENS=256" >> .env

# Use caching for common queries
# Check: backend/core/cache.py

# Disable reranking (if enabled)
echo "RERANKER_ENABLED=false" >> .env
```

### Issue: API Rate Limited

**Problem**: `429 Too Many Requests` error

**Solution**:
```bash
# Check usage dashboard
# OpenAI: https://platform.openai.com/account/billing/usage
# Anthropic: https://console.anthropic.com/

# Implement request throttling
echo "REQUEST_RATE_LIMIT=10" >> .env  # Max 10 requests/min

# Increase cache TTL to reuse results
echo "CACHE_TTL_SECONDS=3600" >> .env

# Switch to higher tier plan if needed
# Or use local LLM (unlimited, no API calls)

# Monitor requests
curl http://localhost:8000/stats | jq .requests
```

### Issue: Wrong Provider Configuration

**Problem**: Using OpenAI provider but Anthropic key set

**Solution**:
```bash
# Verify provider in .env
cat .env | grep LLM_PROVIDER

# Should match installed providers:
# - openai (needs OPENAI_API_KEY)
# - anthropic (needs ANTHROPIC_API_KEY)
# - cohere (needs COHERE_API_KEY)
# - local (needs OLLAMA_BASE_URL or similar)

# Fix configuration
echo "LLM_PROVIDER=anthropic" >> .env
echo "ANTHROPIC_API_KEY=your-key" >> .env

# Validate
python -m backend.config_validator
```

---

## Performance Issues

### Issue: Slow Embeddings

**Problem**: Embedding takes 5+ seconds per document

**Solution**:
```bash
# Use smaller embedding model
echo "EMBEDDER_MODEL=all-MiniLM-L6-v2" >> .env

# Increase batch size
echo "EMBEDDER_BATCH_SIZE=128" >> .env

# Use GPU if available
echo "EMBEDDER_DEVICE=cuda" >> .env

# Check current model
python << 'EOF'
from backend.config import settings
print(f"Model: {settings.embedder_model}")
print(f"Batch size: {settings.embedder_batch_size}")
EOF

# Monitor GPU usage
nvidia-smi  # If using CUDA
```

### Issue: High Memory Usage

**Problem**: Process uses > 8GB RAM

**Solution**:
```bash
# Reduce batch sizes
echo "EMBEDDER_BATCH_SIZE=32" >> .env
echo "LLM_BATCH_SIZE=1" >> .env

# Reduce vector store cache
echo "VECTOR_STORE_CACHE_SIZE=100" >> .env

# Disable in-memory indexing
# Restart backend

# Monitor memory
watch -n 1 'ps aux | grep python | head -5'

# Reduce max document length
echo "MAX_CHUNK_SIZE=500" >> .env
```

### Issue: High CPU Usage

**Problem**: Process uses 100% CPU constantly

**Solution**:
```bash
# Check what's running
top -p $(pgrep -f "python.*backend")

# Disable expensive features
echo "RERANKER_ENABLED=false" >> .env

# Reduce embedding frequency
# Only embed new documents

# Check for infinite loops
# Review recent code changes

# Monitor with profiler
python -m cProfile -s cumulative -m backend.main 2>&1 | head -20
```

---

## Docker Issues

### Issue: Docker Build Fails

**Problem**: `ERROR: failed to solve with frontend dockerfile`

**Solution**:
```bash
# Verify Docker is installed
docker --version

# Check disk space
docker system df

# Clean up
docker system prune -a

# Build with verbose output
docker build --progress=plain -t aosbfs-backend .

# Check Dockerfile syntax
docker build --no-cache -t aosbfs-backend .
```

### Issue: Docker Container Won't Start

**Problem**: Container exits immediately or port conflicts

**Solution**:
```bash
# Check logs
docker logs <container-id>

# Check port conflicts
docker ps  # See running containers
netstat -tlnp | grep 8000

# Start with different port
docker run -p 8001:8000 aosbfs-backend

# Run interactively for debugging
docker run -it aosbfs-backend /bin/bash

# Check image
docker inspect aosbfs-backend
```

### Issue: Docker Compose Fails

**Problem**: Services don't start together

**Solution**:
```bash
# Check compose file syntax
docker-compose config

# Start with verbose logging
docker-compose up --verbose

# Check service status
docker-compose ps

# View service logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart

# Rebuild images
docker-compose build --no-cache
```

---

## Getting More Help

### Debug Mode

```bash
# Run backend in debug mode
PYTHONUNBUFFERED=1 LOGLEVEL=DEBUG python -m backend.main

# Check logs
tail -f backend/logs/app.log
```

### Test Connectivity

```bash
# Test all APIs
python << 'EOF'
import requests

endpoints = [
    ("Health", "http://localhost:8000/health"),
    ("Stats", "http://localhost:8000/stats"),
    ("Models", "http://localhost:8000/models"),
]

for name, url in endpoints:
    try:
        r = requests.get(url, timeout=5)
        print(f"✅ {name}: {r.status_code}")
    except Exception as e:
        print(f"❌ {name}: {e}")
EOF
```

### Configuration Validation

```bash
# Full validation with detailed output
python -m backend.config_validator

# Expected output:
# ✅ Environment variables validated
# ✅ LLM Configuration valid (Provider: openai)
# ✅ Vector Store Configuration valid
# ✅ Encryption Configuration valid
# ✅ All configurations OK
```

### System Information

```bash
# Collect debug info
echo "Python version:"
python --version

echo "Installed packages:"
pip list | head -20

echo "Disk usage:"
df -h

echo "Memory:"
free -h

echo "Environment:"
env | grep -E "PYTHON|PATH|LLM|VECTOR"
```

---

## Still Having Issues?

1. **Check documentation**: OPTIONAL_FEATURES_GUIDE.md, CONFIGURATION_MANAGEMENT.md
2. **Review logs**: `backend/logs/app.log` and `frontend/logs/app.log`
3. **Check GitHub issues**: Similar problem might be reported
4. **Run tests**: `pytest tests/ -v` to identify failures
5. **Create issue**: Include error messages, logs, system info

Good luck! 🚀
