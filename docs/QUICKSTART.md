# Quick Start: Deployment

## 🚀 Local Deployment

```bash
# Quick start with script
./deploy-local.sh

# Or manually with Docker
docker build -t apex-ai-os .
docker run -p 8000:8000 apex-ai-os

# Or with Python
pip install -r requirements.txt
python main.py
```

## 🔄 Automated Deployment

Every push to `main` automatically:
1. ✅ Builds Docker image
2. ✅ Pushes to GitHub Container Registry
3. ✅ Creates deployment manifest
4. ✅ Runs health checks

**View deployment status:**
```bash
gh run list --workflow=auto-deploy.yml
```

**Trigger manual deployment:**
```bash
gh workflow run auto-deploy.yml
```

## 📊 Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# View running containers
docker ps

# View logs
docker logs apex-ai-os-local -f
```

## 🛑 Rollback

```bash
# List previous deployments
kubectl rollout history deployment/apex-ai-os

# Rollback to previous
kubectl rollout undo deployment/apex-ai-os
```

## 📖 Full Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive guide.

## 🔐 Security Features

- ✅ Multi-stage Docker builds
- ✅ Non-root container user
- ✅ SHA-based image tags
- ✅ Health checks enabled
- ✅ Minimal permissions

## 🌐 Endpoints

- **Root**: `http://localhost:8000/`
- **Health**: `http://localhost:8000/health`

## 📦 Container Registry

Images are published to:
```
ghcr.io/garrettc123/apex-universal-ai-operating-system
```

Tags:
- `main-<sha>` - Production releases
- `latest` - Latest main branch build
