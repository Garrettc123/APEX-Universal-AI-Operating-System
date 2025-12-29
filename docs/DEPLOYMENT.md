# APEX Deployment Guide

## Overview

This guide describes the automated deployment pipeline for the APEX Universal AI Operating System.

## Architecture

The deployment pipeline consists of:

1. **Continuous Integration** - Automated testing, linting, and security scans
2. **Container Build** - Docker image creation with multi-stage builds
3. **Container Registry** - GitHub Container Registry (ghcr.io)
4. **Automated Deployment** - Kubernetes-based deployment

## Automated Deployment Pipeline

### Workflow Triggers

The auto-deploy pipeline (`auto-deploy.yml`) triggers on:
- Push to `main` branch
- Manual trigger via `workflow_dispatch`

### Pipeline Stages

#### 1. Build and Push
- Builds Docker image using multi-stage Dockerfile
- Pushes to GitHub Container Registry
- Tags: `latest`, `main-<sha>`, branch-specific tags

#### 2. Deploy
- Creates Kubernetes deployment manifests
- Deploys to production environment
- Runs health checks
- Sends deployment notifications

## Docker Image

### Building Locally

```bash
docker build -t apex-ai-os:latest .
```

### Running Locally

```bash
# Run with Docker
docker run -p 8000:8000 apex-ai-os:latest

# Run with Docker Compose
docker-compose up
```

### Testing the Container

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Container registry access

### Deployment Manifest

The pipeline automatically generates a Kubernetes deployment manifest with:

- **Replicas**: 3 (for high availability)
- **Health Probes**: Liveness and readiness checks
- **Service**: LoadBalancer type
- **Secrets**: Database credentials

### Manual Deployment

To deploy manually:

```bash
# Apply the deployment
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -l app=apex-ai-os
kubectl get svc apex-ai-os-service
```

## Environment Variables

Required environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `MONGODB_URI` - MongoDB connection string
- `REDIS_URL` - Redis connection string

### Setting Secrets

```bash
kubectl create secret generic apex-secrets \
  --from-literal=database-url='postgresql://user:pass@host:5432/db' \
  --from-literal=mongodb-uri='mongodb://host:27017/db' \
  --from-literal=redis-url='redis://host:6379'
```

## CI/CD Workflows

### ci-cd.yml
- Runs tests on pull requests and pushes
- Performs linting and type checking
- Builds Docker images
- Runs security scans

### auto-deploy.yml
- Builds and pushes production images
- Deploys to production environment
- Automated on main branch

### ci.yml
- Matrix testing across Python versions
- Coverage reporting

## Deployment Verification

After deployment:

1. Check pod status: `kubectl get pods`
2. Check service endpoint: `kubectl get svc`
3. Test health endpoint: `curl http://<service-ip>/health`
4. Monitor logs: `kubectl logs -l app=apex-ai-os`

## Rollback

To rollback a deployment:

```bash
# View deployment history
kubectl rollout history deployment/apex-ai-os

# Rollback to previous version
kubectl rollout undo deployment/apex-ai-os

# Rollback to specific revision
kubectl rollout undo deployment/apex-ai-os --to-revision=2
```

## Monitoring

The deployment includes:

- Health checks every 30 seconds
- Readiness probes every 5 seconds
- Automatic pod restart on failure
- LoadBalancer for traffic distribution

## Security

- Multi-stage builds to minimize image size
- Non-root user execution
- Secrets management via Kubernetes secrets
- Security scanning in CI pipeline

## Troubleshooting

### Image Pull Errors

Ensure GitHub token has packages:read permission:

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<github-token>
```

### Pod Crashes

Check logs:
```bash
kubectl logs -l app=apex-ai-os --tail=100
kubectl describe pod <pod-name>
```

### Service Unreachable

Check service and endpoints:
```bash
kubectl get svc apex-ai-os-service
kubectl get endpoints apex-ai-os-service
```

## Support

For deployment issues, refer to:
- GitHub Actions logs
- Kubernetes event logs
- Application logs

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
