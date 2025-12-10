# Docker Deployment Guide

## Overview

AfundiOS uses Docker for containerized deployment. This guide covers building and running the multi-container application locally and in production.

## Quick Start (Production)

Build and start all services:

```bash
docker-compose up -d
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

## Quick Start (Development)

For hot-reload development, uncomment the volumes and command overrides in `docker-compose.yml`:

```bash
# Uncomment development sections in docker-compose.yml
docker-compose up
```

This will mount local code and enable auto-reload when files change.

## Building Images

### Backend

Build the backend image:

```bash
docker build -t afundios-backend:latest ./backend
```

Or via docker-compose:

```bash
docker-compose build backend
```

**Features:**
- Multi-stage build for optimized image size (~400MB)
- Slim Python 3.11 base image
- Health checks enabled
- Data volume mount for persistence (`/app/data`)

### Frontend

Build the frontend image:

```bash
docker build -t afundios-frontend:latest ./frontend
```

Or via docker-compose:

```bash
docker-compose build frontend
```

**Features:**
- Streamlit optimized for containerized environment
- Health checks enabled
- Environment variable for backend URL
- No root user (security best practice)

## Running Containers

### Production Startup

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Development Startup

Uncomment the development sections in `docker-compose.yml`:

```yaml
# Uncomment these lines for development:
volumes:
  - ./backend:/app
command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then:

```bash
docker-compose up
```

### Running Individual Services

```bash
# Start only backend
docker-compose up -d backend

# Start only frontend
docker-compose up -d frontend

# Start frontend (depends on backend)
docker-compose up -d frontend
```

## Environment Configuration

### .env File

Create a `.env` file in the root directory for environment variables:

```env
# FastAPI / Uvicorn
ENVIRONMENT=docker
VECTOR_STORE_PATH=/app/data/vector_store

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Encryption (optional)
ENCRYPTION_ENABLED=false
ENCRYPTION_KEY=...

# Memory Compaction
MEMORY_COMPACTION_ENABLED=true
MEMORY_COMPACTION_INTERVAL_HOURS=24

# Daily Briefing
DAILY_BRIEFING_ENABLED=true
DAILY_BRIEFING_INTERVAL_HOURS=24

# Metadata DB
METADATA_DB_URL=sqlite:///data/metadata.db
```

### Backend Configuration

Additional configuration in `backend/config.py`:

```python
# Vector Store
vector_store_type: str = "chroma"
vector_store_path: str = "data/vector_store"

# LLM Parameters
llm_temperature: float = 0.0
llm_max_tokens: int = 512

# Embedding Model
embedding_model: str = "text-embedding-3-small"
```

## Data Persistence

Data is persisted in the `./data` directory (mounted as a volume):

```
data/
├── vector_store/          # Chroma vector store
│   └── chroma.sqlite3
├── briefings/             # Daily briefing JSON files
└── metadata.db            # Optional: metadata database
```

Ensure this directory is backed up for data persistence.

## Health Checks

Both services include health checks:

- **Backend**: `GET http://localhost:8000/` (FastAPI root endpoint)
- **Frontend**: `GET http://localhost:8501/_stcore/health` (Streamlit health)

View health status:

```bash
docker-compose ps
```

## Port Mapping

| Service  | Container Port | Host Port | Purpose       |
|----------|----------------|-----------|---------------|
| Backend  | 8000           | 8000      | FastAPI API   |
| Frontend | 8501           | 8501      | Streamlit UI  |

To change ports, edit `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"  # Backend on 9000
  - "9501:8501"  # Frontend on 9501
```

## Logs and Debugging

View all logs:

```bash
docker-compose logs -f
```

View backend logs only:

```bash
docker-compose logs -f backend
```

View frontend logs only:

```bash
docker-compose logs -f frontend
```

View last 100 lines with timestamps:

```bash
docker-compose logs --tail=100 -t
```

## Production Deployment

### Cloud Platforms

**Docker Hub / Private Registry:**

```bash
# Tag image
docker tag afundios-backend:latest myregistry/afundios-backend:latest

# Push
docker push myregistry/afundios-backend:latest
```

**Kubernetes:**

Create a `k8s/` directory with deployment manifests:

```bash
kubectl apply -f k8s/
```

**AWS ECS:**

1. Create an ECR repository
2. Push images:
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
   docker tag afundios-backend:latest $ECR_URI/afundios-backend:latest
   docker push $ECR_URI/afundios-backend:latest
   ```
3. Create ECS task definition
4. Deploy service

### Docker Image Security

Best practices implemented:

✅ Multi-stage builds (reduces image size)  
✅ Minimal base images (python:3.11-slim)  
✅ No hardcoded secrets  
✅ Health checks  
✅ Proper dependency pinning in requirements.txt  
✅ .dockerignore to exclude unnecessary files  

Recommendations:

- Scan images with Trivy: `trivy image afundios-backend:latest`
- Use private registry for sensitive deployments
- Enable image signing and verification
- Regularly update base images

## Troubleshooting

### Container won't start

```bash
# View logs
docker-compose logs backend

# Check if port is already in use
lsof -i :8000  # for backend
lsof -i :8501  # for frontend
```

### Backend can't reach database or services

Ensure all services are running and healthy:

```bash
docker-compose ps
```

Check network connectivity:

```bash
docker-compose exec backend ping frontend
docker-compose exec frontend curl http://backend:8000/
```

### Frontend can't reach backend

Verify `BACKEND_URL` environment variable:

```bash
docker-compose exec frontend echo $BACKEND_URL
```

Should be: `http://backend:8000`

### Out of disk space

Clean up unused images and volumes:

```bash
docker system prune -a --volumes
```

## Performance Tuning

### Memory Limits

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### CPU Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
    reservations:
      cpus: '1'
```

### Scaling

For production, use:

- **Docker Swarm**: `docker service create --replicas 3 ...`
- **Kubernetes**: `replicas: 3` in deployment manifest
- **Docker Compose**: Limited scaling support; use orchestrator above

## Next Steps

1. **Add CI/CD**: GitHub Actions, GitLab CI, or Jenkins to automatically build and push images
2. **Add monitoring**: Prometheus + Grafana for metrics and alerts
3. **Add logging**: ELK stack or CloudWatch for centralized logs
4. **Add secrets management**: HashiCorp Vault or cloud provider secret manager
5. **Add reverse proxy**: Nginx or Caddy for TLS termination and routing

For more details, see the main [README.md](../README.md) and individual component documentation.
