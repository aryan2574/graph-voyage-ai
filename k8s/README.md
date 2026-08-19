# Kubernetes Manifests - GraphVoyageAI

This directory contains Kubernetes manifests to deploy GraphVoyageAI locally using Docker Desktop's Kubernetes cluster.

## File Structure

```
k8s/
├── 00-namespace.yaml           # Creates 'graphvoyage' namespace
├── 01-secret.yaml              # Stores API keys, passwords
├── 02-configmap.yaml           # Stores non-sensitive config
├── 03-postgres-pvc.yaml        # Persistent storage for PostgreSQL
├── 04-postgres-deployment.yaml # PostgreSQL database
├── 05-postgres-service.yaml    # PostgreSQL service endpoint
├── 06-app-deployment.yaml      # FastAPI application
├── 07-app-service.yaml         # App service (LoadBalancer)
├── 08-adminer-deployment.yaml  # Database UI (optional)
└── 09-adminer-service.yaml     # Adminer service (LoadBalancer)
```

## Resource Hierarchy

```
Namespace: graphvoyage
│
├── ConfigMap: graphvoyageai-config
│   └── Non-sensitive environment variables
│
├── Secret: graphvoyageai-secrets
│   └── API keys, passwords
│
├── PersistentVolumeClaim: postgres-pvc
│   └── 5Gi storage for PostgreSQL data
│
├── PostgreSQL
│   ├── Deployment: postgres (1 replica)
│   │   └── Pod: postgres-xxx
│   │       └── Container: postgres:16-alpine
│   └── Service: postgres-service (ClusterIP)
│
├── FastAPI App
│   ├── Deployment: graphvoyageai-app (2 replicas)
│   │   ├── Pod: graphvoyageai-app-xxx-1
│   │   │   └── Container: graphvoyageai:latest
│   │   └── Pod: graphvoyageai-app-xxx-2
│   │       └── Container: graphvoyageai:latest
│   └── Service: graphvoyageai-service (LoadBalancer :8000)
│
└── Adminer
    ├── Deployment: adminer (1 replica)
    │   └── Pod: adminer-xxx
    │       └── Container: adminer:latest
    └── Service: adminer-service (LoadBalancer :8080)
```

## Prerequisites

1. **Enable Kubernetes in Docker Desktop**
   - Open Docker Desktop
   - Settings → Kubernetes
   - Check "Enable Kubernetes"
   - Apply & Restart
   - Wait for "Kubernetes is running" status

2. **Verify Kubernetes is running**
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

3. **Build Docker image**
   ```bash
   docker build -t graphvoyageai:latest -f Dockerfile --target production .
   ```

## Deployment Steps

### 1. Apply all manifests
```bash
# Apply all at once (files are applied in order due to naming)
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secret.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-postgres-pvc.yaml
kubectl apply -f k8s/04-postgres-deployment.yaml
kubectl apply -f k8s/05-postgres-service.yaml
kubectl apply -f k8s/06-app-deployment.yaml
kubectl apply -f k8s/07-app-service.yaml
kubectl apply -f k8s/08-adminer-deployment.yaml
kubectl apply -f k8s/09-adminer-service.yaml
```

### 2. Verify deployment
```bash
# Check all resources in namespace
kubectl get all -n graphvoyage

# Watch Pods starting up
kubectl get pods -n graphvoyage -w

# Check Pod details
kubectl describe pod <pod-name> -n graphvoyage

# View logs
kubectl logs -f <pod-name> -n graphvoyage
```

### 3. Access services

**FastAPI Application:**
- URL: http://localhost:8000
- Service: `graphvoyageai-service` (LoadBalancer)

**Adminer (Database UI):**
- URL: http://localhost:8080
- Login:
  - System: PostgreSQL
  - Server: `postgres-service`
  - Username: `travel_user`
  - Password: `dev_password`
  - Database: `travel_db`

## Common Commands

### Viewing Resources
```bash
# List all resources in namespace
kubectl get all -n graphvoyage

# List Pods with more details
kubectl get pods -n graphvoyage -o wide

# List Services
kubectl get services -n graphvoyage

# List Deployments
kubectl get deployments -n graphvoyage

# List PVCs
kubectl get pvc -n graphvoyage
```

### Debugging
```bash
# Describe Pod (shows events, errors)
kubectl describe pod <pod-name> -n graphvoyage

# View logs
kubectl logs <pod-name> -n graphvoyage

# Follow logs (live)
kubectl logs -f <pod-name> -n graphvoyage

# Previous container logs (if restarted)
kubectl logs <pod-name> -n graphvoyage --previous

# Shell into Pod
kubectl exec -it <pod-name> -n graphvoyage -- /bin/sh

# Port forward (alternative to NodePort)
kubectl port-forward pod/<pod-name> 8000:8000 -n graphvoyage
```

### Scaling
```bash
# Scale app to 3 replicas
kubectl scale deployment graphvoyageai-app --replicas=3 -n graphvoyage

# View scaling
kubectl get deployments -n graphvoyage
```

### Updates
```bash
# Update image
kubectl set image deployment/graphvoyageai-app app=graphvoyageai:v2 -n graphvoyage

# Check rollout status
kubectl rollout status deployment/graphvoyageai-app -n graphvoyage

# View rollout history
kubectl rollout history deployment/graphvoyageai-app -n graphvoyage

# Rollback to previous version
kubectl rollout undo deployment/graphvoyageai-app -n graphvoyage
```

### Cleanup
```bash
# Delete all resources in namespace
kubectl delete namespace graphvoyage

# Or delete individually
kubectl delete -f k8s/

# Delete specific resource
kubectl delete deployment graphvoyageai-app -n graphvoyage
```

## Resource Limits

Each Pod has resource requests and limits:

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| PostgreSQL | 250m | 500m | 256Mi | 512Mi |
| FastAPI App | 500m | 1000m | 512Mi | 1Gi |
| Adminer | 100m | 200m | 128Mi | 256Mi |

**Note:** 1000m = 1 CPU core

## Probes Explained

### Liveness Probe
- Checks if container is alive
- Restarts container if it fails
- Example: HTTP GET to `/health`

### Readiness Probe
- Checks if container is ready to receive traffic
- Removes from Service endpoints if it fails
- Traffic resumes when probe succeeds

### Startup Probe
- For slow-starting applications
- Other probes are disabled until this succeeds
- Prevents premature restarts

## Next Steps

1. **Experiment with scaling**
   ```bash
   kubectl scale deployment graphvoyageai-app --replicas=5 -n graphvoyage
   ```

2. **Test self-healing**
   ```bash
   # Delete a Pod and watch it recreate
   kubectl delete pod <pod-name> -n graphvoyage
   kubectl get pods -n graphvoyage -w
   ```

3. **Test rolling updates**
   ```bash
   # Rebuild image with changes
   docker build -t graphvoyageai:v2 .
   
   # Update deployment
   kubectl set image deployment/graphvoyageai-app app=graphvoyageai:v2 -n graphvoyage
   
   # Watch rollout
   kubectl rollout status deployment/graphvoyageai-app -n graphvoyage
   ```

4. **Monitor resources**
   ```bash
   kubectl top nodes
   kubectl top pods -n graphvoyage
   ```

5. **View events**
   ```bash
   kubectl get events -n graphvoyage --sort-by='.lastTimestamp'
   ```

## Troubleshooting

### Pod not starting
```bash
# Check Pod status
kubectl get pods -n graphvoyage

# View detailed events
kubectl describe pod <pod-name> -n graphvoyage

# Check logs
kubectl logs <pod-name> -n graphvoyage
```

### Image pull errors
- Ensure `imagePullPolicy: Never` for local images
- Or push to Docker Hub and use `imagePullPolicy: Always`

### Database connection issues
- Check if PostgreSQL Pod is ready: `kubectl get pods -n graphvoyage`
- Check Service DNS: `kubectl get svc -n graphvoyage`
- Verify Secret: `kubectl get secret graphvoyageai-secrets -n graphvoyage -o yaml`

### Service not accessible
```bash
# Check Service endpoints
kubectl get endpoints -n graphvoyage

# Port forward as alternative
kubectl port-forward service/graphvoyageai-service 8000:8000 -n graphvoyage
```
