# Deployment Guide

Production-ready deployment strategies for AfundiOS.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment (AWS)](#cloud-deployment-aws)
4. [Cloud Deployment (Google Cloud)](#cloud-deployment-google-cloud)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Local Development

### Quick Start (Dev Mode)

```bash
# 1. Clone repository
git clone <repo-url>
cd AOSBAckend

# 2. Create virtual environment
python3.11 -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start backend
python -m backend.main
# Runs on http://localhost:8000

# 6. In another terminal, start frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
# Runs on http://localhost:8501
```

### Development Workflow

```bash
# Run tests before committing
pytest tests/ -v

# Check code quality
pylint backend/ --disable=all --enable=E,F

# Format code
black backend/ frontend/ tests/

# Run with hot reload
# Terminal 1:
PYTHONUNBUFFERED=1 python -m backend.main

# Terminal 2:
streamlit run frontend/app.py --logger.level=debug

# Watch for changes and restart
pip install watchfiles
watchmedo auto-restart -d backend/ -p '*.py' -- python -m backend.main
```

---

## Docker Deployment

### Build Images

```bash
# Build backend image
docker build -f backend/Dockerfile -t aosbfs-backend:latest .

# Build frontend image
docker build -f frontend/Dockerfile -t aosbfs-frontend:latest .

# Verify images
docker images | grep aosbfs
```

### Single Container (Backend Only)

```bash
# Run backend container
docker run -d \
  --name aosbfs-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e VECTOR_STORE_TYPE=chroma \
  -v $(pwd)/backend/data:/app/backend/data \
  aosbfs-backend:latest

# Check logs
docker logs aosbfs-backend

# Test API
curl http://localhost:8000/health

# Stop container
docker stop aosbfs-backend
docker rm aosbfs-backend
```

### Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
# Expected:
# NAME                COMMAND                  STATUS
# aosbfs-backend      "python -m backend..."   Up 2 minutes
# aosbfs-frontend     "streamlit run app.py"   Up 2 minutes

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### Docker Compose Production

```yaml
version: '3.9'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: aosbfs-backend
    restart: always
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      VECTOR_STORE_TYPE: chroma
      VECTOR_STORE_PATH: /app/backend/data/vector_store
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    volumes:
      - backend_data:/app/backend/data
      - ./backend/logs:/app/backend/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - aosbfs-network

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    container_name: aosbfs-frontend
    restart: always
    environment:
      BACKEND_URL: http://backend:8000
      LOG_LEVEL: INFO
    ports:
      - "8501:8501"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - aosbfs-network

volumes:
  backend_data:
    driver: local

networks:
  aosbfs-network:
    driver: bridge
```

### Use Production Config

```yaml
# In docker-compose.yml
services:
  backend:
    environment:
      # Production settings
      ENVIRONMENT: production
      LOG_LEVEL: WARNING
      DEBUG: "false"
      VECTOR_STORE_CACHE_SIZE: 1000
      MEMORY_COMPACTION_STRATEGY: age_based
      REQUEST_TIMEOUT: 60
      MAX_FILE_SIZE: 100000000  # 100MB
```

---

## Cloud Deployment (AWS)

### Option 1: AWS App Runner (Easiest)

```bash
# Prerequisites
# - AWS account
# - AWS CLI configured
# - Docker image pushed to ECR

# 1. Push Docker image to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag aosbfs-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aosbfs-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aosbfs-backend:latest

# 2. Create App Runner service (via AWS Console or CLI)
aws apprunner create-service \
  --service-name aosbfs-backend \
  --source-configuration \
    ImageRepository={ImageIdentifier=<account-id>.dkr.ecr.us-east-1.amazonaws.com/aosbfs-backend:latest,ImageRepositoryType=ECR} \
  --instance-configuration Cpu=1024,Memory=2048 \
  --region us-east-1

# 3. Set environment variables
aws apprunner update-service \
  --service-arn arn:aws:apprunner:... \
  --environment-variables OPENAI_API_KEY=sk-...,VECTOR_STORE_TYPE=chroma

# 4. Monitor
aws apprunner describe-service --service-arn arn:aws:apprunner:...
```

### Option 2: AWS ECS (More Control)

```bash
# 1. Create ECS cluster
aws ecs create-cluster --cluster-name aosbfs-cluster

# 2. Register task definition
aws ecs register-task-definition \
  --family aosbfs-backend \
  --container-definitions file://ecs-task-definition.json

# 3. Create service
aws ecs create-service \
  --cluster aosbfs-cluster \
  --service-name aosbfs-backend \
  --task-definition aosbfs-backend:1 \
  --desired-count 2

# 4. Scale as needed
aws ecs update-service \
  --cluster aosbfs-cluster \
  --service aosbfs-backend \
  --desired-count 3
```

### Option 3: AWS Lambda (Serverless)

Not recommended for this application due to:
- Long-running processes (LLM inference)
- State management (vector store)
- Large dependencies
- Better to use App Runner or ECS

### AWS ECS Task Definition

```json
{
  "family": "aosbfs-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "aosbfs-backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/aosbfs-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "VECTOR_STORE_TYPE",
          "value": "chroma"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/aosbfs-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

---

## Cloud Deployment (Google Cloud)

### Cloud Run (Recommended)

```bash
# Prerequisites
# - Google Cloud account
# - gcloud CLI installed
# - Dockerfile ready

# 1. Set project
gcloud config set project aosbfs-project

# 2. Build and push image
gcloud builds submit --tag gcr.io/aosbfs-project/aosbfs-backend

# 3. Deploy to Cloud Run
gcloud run deploy aosbfs-backend \
  --image gcr.io/aosbfs-project/aosbfs-backend \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600 \
  --set-env-vars OPENAI_API_KEY=sk-...,VECTOR_STORE_TYPE=chroma \
  --allow-unauthenticated

# 4. Get service URL
gcloud run services describe aosbfs-backend --region us-central1

# 5. Update frontend to use service URL
BACKEND_URL=https://aosbfs-backend-xxxxx.a.run.app
```

### Cloud Run with Persistent Storage

```bash
# Use Cloud Storage for vector store
gsutil mb gs://aosbfs-vector-store

# Update config to use Cloud Storage
VECTOR_STORE_TYPE=gcs-chroma
GCS_BUCKET=aosbfs-vector-store

# OR use Cloud Firestore for metadata
gcloud firestore databases create --region us-central1
```

### Cloud Compute Engine (VM)

```bash
# Create VM instance
gcloud compute instances create aosbfs-vm \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-standard-2 \
  --zone=us-central1-a

# SSH into VM
gcloud compute ssh aosbfs-vm --zone=us-central1-a

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Pull and run image
docker pull gcr.io/aosbfs-project/aosbfs-backend
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  gcr.io/aosbfs-project/aosbfs-backend

# Setup firewall
gcloud compute firewall-rules create allow-backend \
  --allow tcp:8000 \
  --source-ranges 0.0.0.0/0
```

---

## Production Checklist

### Before Deployment

- [ ] Environment variables set (.env file)
- [ ] API keys valid and funded
- [ ] Database migrations applied
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code reviewed and merged
- [ ] Docker images built and tested
- [ ] Security scan passed (`docker scan`)
- [ ] Performance tested with load

### Configuration

- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=WARNING` or `INFO`
- [ ] `VECTOR_STORE_CACHE_SIZE` set to appropriate value
- [ ] `MEMORY_COMPACTION_STRATEGY=age_based`
- [ ] `REQUEST_TIMEOUT=60`
- [ ] API rate limits configured
- [ ] CORS properly configured

### Security

- [ ] API keys stored in secrets manager (not .env file)
- [ ] Database encrypted at rest
- [ ] HTTPS enabled (not HTTP)
- [ ] CORS restricted to known origins
- [ ] Rate limiting enabled
- [ ] Request validation strict
- [ ] Error messages don't leak sensitive info
- [ ] Logs don't contain API keys

### Infrastructure

- [ ] Load balancer configured
- [ ] Health checks working
- [ ] Auto-scaling enabled
- [ ] Backup strategy in place
- [ ] Disaster recovery plan
- [ ] Monitoring alerts set up
- [ ] Logging centralized
- [ ] Network isolation (private VPC)

### Testing

- [ ] Smoke tests pass
- [ ] All integration tests pass
- [ ] Performance within SLA
- [ ] Database backups automated
- [ ] Health endpoint responding
- [ ] API endpoints responding
- [ ] Frontend loads successfully
- [ ] File upload working

### Documentation

- [ ] Deployment procedure documented
- [ ] Rollback procedure documented
- [ ] Monitoring dashboard created
- [ ] Runbook for common issues
- [ ] Team trained on deployment
- [ ] Incident response plan created

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check backend health
curl https://api.example.com/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-01-01T12:00:00Z",
#   "uptime_seconds": 86400,
#   "version": "1.0.0"
# }

# Check API statistics
curl https://api.example.com/stats
```

### Logging

```bash
# View logs (Docker)
docker logs -f aosbfs-backend --tail 100

# View logs (Kubernetes)
kubectl logs -f deployment/aosbfs-backend

# View logs (Cloud Run)
gcloud run logs read aosbfs-backend --limit 100

# Structured logging for analysis
cat backend/logs/app.log | grep ERROR | jq .

# Send to centralized logging
# - ELK Stack
# - Splunk
# - Datadog
# - CloudWatch
```

### Monitoring Metrics

```bash
# Key metrics to monitor
# 1. Request latency (p50, p95, p99)
# 2. Error rate (5xx, 4xx)
# 3. Vector store size (documents, vectors)
# 4. Memory usage
# 5. CPU usage
# 6. API rate limit usage
# 7. Cache hit rate
# 8. Queue length (if async)

# Example Prometheus metrics
# request_duration_seconds
# requests_total
# errors_total
# vector_store_size
# memory_usage_bytes
```

### Backup & Recovery

```bash
# Backup vector store (daily)
docker exec aosbfs-backend \
  tar czf /tmp/vector_store_backup.tar.gz \
  /app/backend/data/vector_store/

# Upload to backup storage
aws s3 cp /tmp/vector_store_backup.tar.gz \
  s3://aosbfs-backups/

# Restore from backup
aws s3 cp s3://aosbfs-backups/vector_store_backup.tar.gz .
tar xzf vector_store_backup.tar.gz -C /app/backend/data/
```

### Updates & Patches

```bash
# Check for security updates
docker image inspect aosbfs-backend | jq .
# Or use: trivy image aosbfs-backend

# Update base image
# In Dockerfile, update FROM image
FROM python:3.11.1 # <- update version

# Rebuild and test
docker build -t aosbfs-backend:latest .
docker run -it aosbfs-backend pytest tests/

# Deploy new version
docker push aosbfs-backend:latest

# Rollout new version (Kubernetes example)
kubectl set image deployment/aosbfs-backend \
  aosbfs-backend=aosbfs-backend:latest
```

### Auto-Scaling

```bash
# Kubernetes HPA (Horizontal Pod Autoscaler)
kubectl apply -f - << EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aosbfs-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aosbfs-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

### Scheduled Tasks

```bash
# Cleanup old logs (cron)
# 0 2 * * * find /app/backend/logs -mtime +30 -delete

# Optimize vector store (cron)
# 0 3 * * 0 python -m backend.core.vectorstore deduplicate

# Health check (every 5 minutes)
# */5 * * * * curl -f https://api.example.com/health || alert
```

---

## Deployment Commands Reference

### Docker

```bash
# Build
docker build -f backend/Dockerfile -t aosbfs-backend:latest .

# Push
docker push aosbfs-backend:latest

# Run
docker run -d -p 8000:8000 aosbfs-backend:latest

# Stop
docker stop $(docker ps -q --filter ancestor=aosbfs-backend)

# Logs
docker logs -f <container-id>
```

### Docker Compose

```bash
# Up
docker-compose up -d

# Down
docker-compose down

# Logs
docker-compose logs -f backend

# Restart
docker-compose restart backend

# Rebuild
docker-compose build --no-cache
```

### AWS

```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag aosbfs-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/aosbfs-backend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/aosbfs-backend:latest

# Deploy to App Runner
aws apprunner create-service --service-name aosbfs-backend \
  --source-configuration ImageRepository={ImageIdentifier=<account>.dkr.ecr.<region>.amazonaws.com/aosbfs-backend:latest}
```

### Google Cloud

```bash
# Push to GCR
gcloud builds submit --tag gcr.io/<project>/aosbfs-backend

# Deploy to Cloud Run
gcloud run deploy aosbfs-backend \
  --image gcr.io/<project>/aosbfs-backend \
  --platform managed --region us-central1
```

---

## Rollback Procedure

```bash
# If something goes wrong:

# 1. Check what's broken
docker logs -f <container-id> --tail 100

# 2. Stop current version
docker stop <container-id>

# 3. Run previous version
docker run -d -p 8000:8000 aosbfs-backend:previous

# 4. Verify it's working
curl http://localhost:8000/health

# 5. Investigate issue
# Check logs, test locally, review changes

# 6. Fix and redeploy
# Option 1: Revert commit
git revert <bad-commit-sha>
# Option 2: Fix issue
# Then rebuild and redeploy
```

---

## Getting Help

- **Deployment issues**: Check Docker logs and system resources
- **Performance issues**: Check monitoring dashboards and optimize configuration
- **Data issues**: Restore from backup and investigate root cause
- **Security**: Run security scan, update dependencies, rotate keys
- **Scaling**: Add more replicas, increase resources, optimize queries

Good luck with your deployment! 🚀
