# 🚀 Deployment Guide - GraphVoyageAI

This guide covers all deployment options: Docker, Kubernetes, and Render.

## Table of Contents
- [Docker Setup](#docker-setup)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Render Deployment](#render-deployment)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Docker Setup

### Prerequisites
- Docker Desktop installed
- Docker Compose v2.0+

### Local Development with Docker Compose

1. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. **Start all services**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- FastAPI application (port 8000)
- Adminer database UI (port 8080)

3. **View logs**
```bash
docker-compose logs -f app
```

4. **Stop services**
```bash
docker-compose down
```

5. **Clean up (including volumes)**
```bash
docker-compose down -v
```

### Production Docker Setup

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Build Docker Image Manually

```bash
# Development
docker build --target development -t graphvoyageai:dev .

# Production
docker build --target production -t graphvoyageai:prod .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="your_db_url" \
  -e GROQ_API_KEY="your_key" \
  -e TAVILY_API_KEY="your_key" \
  -e AVIATIONSTACK_API_KEY="your_key" \
  --name graphvoyage \
  graphvoyageai:prod
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (local or cloud)
- kubectl configured
- Docker image pushed to registry

### Option 1: Local Kubernetes with Minikube

#### Install Minikube
```bash
# Windows (using Chocolatey)
choco install minikube

# Or download from https://minikube.sigs.k8s.io/docs/start/

# Start Minikube
minikube start --cpus=4 --memory=8192

# Enable ingress addon
minikube addons enable ingress
minikube addons enable metrics-server
```

#### Deploy to Minikube

```bash
# 1. Build image and load into Minikube
eval $(minikube docker-env)
docker build -t graphvoyageai:latest .

# 2. Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# 3. Check deployment status
kubectl get pods -n graphvoyage
kubectl get services -n graphvoyage

# 4. Access the application
minikube service graphvoyage-service -n graphvoyage
```

### Option 2: Local Kubernetes with Kind (Kubernetes in Docker)

#### Install Kind
```bash
# Windows (using Chocolatey)
choco install kind

# Or download from https://kind.sigs.k8s.io/

# Create cluster
kind create cluster --name graphvoyage --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF

# Load image into Kind
docker build -t graphvoyageai:latest .
kind load docker-image graphvoyageai:latest --name graphvoyage

# Deploy application
kubectl apply -f k8s/
```

### Kubernetes Commands Cheat Sheet

```bash
# View all resources
kubectl get all -n graphvoyage

# View logs
kubectl logs -f deployment/graphvoyage-app -n graphvoyage

# Describe pod
kubectl describe pod <pod-name> -n graphvoyage

# Execute command in pod
kubectl exec -it <pod-name> -n graphvoyage -- /bin/bash

# Port forward
kubectl port-forward service/graphvoyage-service 8000:80 -n graphvoyage

# Scale deployment
kubectl scale deployment/graphvoyage-app --replicas=5 -n graphvoyage

# Update image
kubectl set image deployment/graphvoyage-app graphvoyage=graphvoyageai:v2 -n graphvoyage

# Rollback deployment
kubectl rollout undo deployment/graphvoyage-app -n graphvoyage

# View deployment history
kubectl rollout history deployment/graphvoyage-app -n graphvoyage

# Delete all resources
kubectl delete namespace graphvoyage
```

### Option 3: Cloud Kubernetes (AWS EKS, GCP GKE, Azure AKS)

#### AWS EKS Example

```bash
# Install eksctl
choco install eksctl

# Create cluster
eksctl create cluster \
  --name graphvoyage-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed

# Deploy application
kubectl apply -f k8s/

# Get LoadBalancer URL
kubectl get service graphvoyage-service -n graphvoyage
```

---

## Render Deployment

### Option 1: Deploy with Render Dashboard (Easy)

1. **Push to GitHub**
```bash
git push origin main
```

2. **Create Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: graphvoyageai
     - **Environment**: Docker
     - **Region**: Choose closest to users
     - **Branch**: main
     - **Dockerfile Path**: `./Dockerfile`
     - **Docker Build Context**: `./`

3. **Add Environment Variables**
   - DATABASE_URL (use Render PostgreSQL)
   - GROQ_API_KEY
   - TAVILY_API_KEY
   - AVIATIONSTACK_API_KEY
   - DEFAULT_ORIGIN_IATA

4. **Create PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Copy the "Internal Database URL"
   - Add it as `DATABASE_URL` in your web service

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

### Option 2: Deploy with render.yaml (Infrastructure as Code)

1. **Create render.yaml in project root**

```yaml
services:
  - type: web
    name: graphvoyageai
    env: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    region: oregon
    plan: starter
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: graphvoyage-db
          property: connectionString
      - key: GROQ_API_KEY
        sync: false
      - key: TAVILY_API_KEY
        sync: false
      - key: AVIATIONSTACK_API_KEY
        sync: false
      - key: DEFAULT_ORIGIN_IATA
        value: DAC
      - key: ENVIRONMENT
        value: production

databases:
  - name: graphvoyage-db
    databaseName: travel_db
    region: oregon
    plan: starter
```

2. **Deploy using Blueprint**
   - In Render Dashboard, click "New +" → "Blueprint Instance"
   - Connect repository
   - Render will read render.yaml and create all services

### Option 3: Deploy with Docker Image (Advanced)

1. **Build and push Docker image**

```bash
# Build production image
docker build --target production -t graphvoyageai:latest .

# Tag for registry (use Docker Hub or GitHub Container Registry)
docker tag graphvoyageai:latest yourusername/graphvoyageai:latest

# Push to registry
docker push yourusername/graphvoyageai:latest
```

2. **Create Web Service on Render**
   - Type: Web Service
   - Source: Existing Image
   - Image URL: `yourusername/graphvoyageai:latest`
   - Add environment variables

### Render Deploy Hook (CI/CD)

1. **Get Deploy Hook URL**
   - Go to your service settings
   - Copy "Deploy Hook" URL

2. **Add to GitHub Secrets**
   - Go to repository Settings → Secrets → Actions
   - Add secret: `RENDER_DEPLOY_HOOK_URL`

3. **Automatic deployment** is configured in `.github/workflows/ci-cd.yml`

### Render Commands

```bash
# Install Render CLI
npm install -g @render/cli

# Login
render login

# List services
render services list

# View logs
render logs --service=graphvoyageai

# Trigger manual deploy
curl -X POST <your-deploy-hook-url>
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

Two workflows are configured:

1. **ci-cd.yml** - Complete CI/CD pipeline
   - Runs tests
   - Builds Docker image
   - Pushes to GitHub Container Registry
   - Deploys to Render (on main branch)

2. **docker-build.yml** - Docker validation
   - Tests Docker builds
   - Scans for vulnerabilities
   - Runs on PR changes

### Required GitHub Secrets

Add these in repository Settings → Secrets → Actions:

```
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
AVIATIONSTACK_API_KEY=your_key
RENDER_DEPLOY_HOOK_URL=https://api.render.com/deploy/...
```

### GitHub Container Registry

Images are automatically pushed to:
```
ghcr.io/yourusername/graphvoyageai:latest
```

To pull:
```bash
docker pull ghcr.io/yourusername/graphvoyageai:latest
```

---

## Monitoring & Troubleshooting

### Check Application Health

```bash
# Local
curl http://localhost:8000/health

# Kubernetes
kubectl exec -it <pod-name> -n graphvoyage -- curl http://localhost:8000/health

# Render
curl https://your-app.onrender.com/health
```

### View Metrics

```bash
# Local
curl http://localhost:8000/api/metrics

# Production
curl https://your-app.onrender.com/api/metrics
```

### Common Issues

**Issue**: Container fails to start
```bash
# Check logs
docker logs <container-id>
kubectl logs <pod-name> -n graphvoyage

# Check environment variables
docker exec <container-id> env
kubectl exec <pod-name> -n graphvoyage -- env
```

**Issue**: Database connection failed
```bash
# Test database connectivity
docker exec <container-id> psql $DATABASE_URL -c "SELECT 1"
```

**Issue**: Port already in use
```bash
# Find process using port
netstat -ano | findstr :8000
# Kill process
taskkill /PID <process-id> /F
```

---

## Performance Tuning

### Docker
- Use multi-stage builds (already configured)
- Layer caching (already configured)
- Health checks (already configured)

### Kubernetes
- HPA configured (2-10 replicas based on CPU/Memory)
- Resource limits set
- Readiness/Liveness probes configured

### Render
- Use "Professional" plan for better performance
- Enable autoscaling
- Use Render PostgreSQL for better latency

---

## Security Best Practices

1. **Never commit secrets**
   - Use `.env` for local
   - Use Kubernetes secrets for K8s
   - Use Render environment variables for cloud

2. **Use non-root user in containers** (already configured)

3. **Scan images for vulnerabilities**
```bash
# Using Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image graphvoyageai:latest
```

4. **Keep dependencies updated**
```bash
pip list --outdated
```

---

## Next Steps

- [ ] Set up monitoring with Prometheus/Grafana
- [ ] Configure log aggregation (ELK stack)
- [ ] Set up alerts for errors
- [ ] Implement blue-green deployment
- [ ] Set up staging environment
- [ ] Configure CDN for static assets

For questions or issues, check the main README.md or open an issue on GitHub.
