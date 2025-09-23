# Microservices Kubernetes Deployment Guide

This guide provides step-by-step instructions to deploy your microservices architecture to Kubernetes.

## 🏗️ Architecture Overview

Your application consists of the following microservices:

- **Frontend**: React application (port 80)
- **Backend**: Main API Gateway (port 8080)
- **Auth Service**: Authentication service (port 8000)
- **Tasks Service**: Task management service (port 8001)
- **Collaborator Service**: Collaborator management service (port 8002)
- **Logs Service**: Logging service (port 8003)

## 📋 Prerequisites

Before deploying, ensure you have the following installed:

1. **Docker**: For building container images
   - Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - Verify installation: `docker --version`

2. **Kubernetes Cluster**: One of the following:
   - **Docker Desktop** (Windows/Mac): Enable Kubernetes in settings
   - **Minikube**: `minikube start`
   - **Kind**: `kind create cluster`
   - **Cloud provider** (AKS, EKS, GKE)

3. **kubectl**: Kubernetes command-line tool
   - Install from [kubernetes.io](https://kubernetes.io/docs/tasks/tools/)
   - Verify installation: `kubectl version --client`

4. **NGINX Ingress Controller** (optional, for ingress):
   ```powershell
   # For Docker Desktop
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   
   # For Minikube
   minikube addons enable ingress
   ```

## 🚀 Quick Start

### 1. Clone and Navigate to Project
```powershell
cd C:\Users\juanb\OneDrive\Documentos\GitHub\Kubernetes-SD
```

### 2. Build Docker Images
```powershell
.\scripts\build-images.ps1
```

This script will build Docker images for all microservices:
- `auth-service:latest`
- `backend-service:latest`
- `tasks-service:latest`
- `collaborator-service:latest`
- `logs-service:latest`
- `frontend:latest`

### 3. Deploy to Kubernetes
```powershell
.\scripts\deploy.ps1
```

This script will:
- Create the `microservices-app` namespace
- Deploy all services with their configurations
- Set up ingress routing
- Show deployment status

### 4. Access Your Application

After successful deployment:

- **Frontend**: http://microservices-app.local
- **API Gateway**: http://microservices-app.local/api
- **Direct service access**:
  - Auth: http://microservices-app.local/auth
  - Tasks: http://microservices-app.local/tasks
  - Collaborators: http://microservices-app.local/collaborators
  - Logs: http://microservices-app.local/logs

**Note**: Add the following to your hosts file:
```
<INGRESS_IP> microservices-app.local
```

To get the ingress IP:
```powershell
kubectl get ingress -n microservices-app
```

## 📁 Project Structure

```
Kubernetes-SD/
├── auth_service/              # Authentication microservice
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── backend/                   # Main API gateway
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── tasks_service/             # Tasks microservice
│   ├── Dockerfile
│   ├── k8s/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── main.py
│   └── requirements.txt
├── collaborator_service/      # Collaborator microservice
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── logs_service/              # Logging microservice
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/                  # React frontend
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
├── k8s/                       # Kubernetes manifests
│   ├── namespace.yaml
│   ├── auth-service-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── collaborator-service-deployment.yaml
│   ├── logs-service-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── ingress.yaml
└── scripts/                   # Deployment scripts
    ├── build-images.ps1
    ├── deploy.ps1
    └── cleanup.ps1
```

## 🔧 Manual Deployment Steps

If you prefer manual deployment:

### 1. Build Images Manually
```powershell
# Build each service
docker build -t auth-service:latest auth_service/
docker build -t backend-service:latest backend/
docker build -t tasks-service:latest tasks_service/
docker build -t collaborator-service:latest collaborator_service/
docker build -t logs-service:latest logs_service/
docker build -t frontend:latest frontend/
```

### 2. Deploy Manually
```powershell
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy services
kubectl apply -f k8s/auth-service-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f tasks_service/k8s/deployment.yaml
kubectl apply -f tasks_service/k8s/service.yaml
kubectl apply -f k8s/collaborator-service-deployment.yaml
kubectl apply -f k8s/logs-service-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml
```

## 📊 Monitoring and Management

### Check Deployment Status
```powershell
# Check all resources
kubectl get all -n microservices-app

# Check specific resources
kubectl get deployments -n microservices-app
kubectl get services -n microservices-app
kubectl get pods -n microservices-app
kubectl get ingress -n microservices-app
```

### View Logs
```powershell
# View logs for a specific service
kubectl logs -f deployment/auth-service -n microservices-app
kubectl logs -f deployment/backend-service -n microservices-app
kubectl logs -f deployment/tasks-service -n microservices-app

# View logs for all pods
kubectl logs -f -l app=auth-service -n microservices-app
```

### Scale Services
```powershell
# Scale a specific service
kubectl scale deployment auth-service --replicas=3 -n microservices-app
kubectl scale deployment backend-service --replicas=3 -n microservices-app
```

## 🛠️ Troubleshooting

### Common Issues

1. **Pods not starting**:
   ```powershell
   kubectl describe pod <pod-name> -n microservices-app
   kubectl logs <pod-name> -n microservices-app
   ```

2. **Image pull errors**:
   - Ensure Docker images are built locally
   - Check image names match in deployment files

3. **Service connectivity issues**:
   ```powershell
   kubectl get endpoints -n microservices-app
   kubectl exec -it <pod-name> -n microservices-app -- curl <service-name>:8080
   ```

4. **Ingress not working**:
   - Ensure ingress controller is installed
   - Check ingress configuration:
   ```powershell
   kubectl describe ingress microservices-ingress -n microservices-app
   ```

### Health Checks

Each service includes health check endpoints. Modify your services to include a `/health` endpoint if not already present:

```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## 🧹 Cleanup

To remove all deployments:
```powershell
.\scripts\cleanup.ps1
```

Or manually:
```powershell
kubectl delete namespace microservices-app
```

To remove Docker images:
```powershell
docker rmi auth-service:latest backend-service:latest tasks-service:latest collaborator-service:latest logs-service:latest frontend:latest
```

## 🌐 Production Considerations

For production deployment, consider:

1. **Environment Variables**: Use ConfigMaps and Secrets
2. **Resource Limits**: Set appropriate CPU and memory limits
3. **Persistent Storage**: Use PersistentVolumes for databases
4. **SSL/TLS**: Configure HTTPS with cert-manager
5. **Monitoring**: Add Prometheus and Grafana
6. **Backup**: Implement backup strategies for data
7. **Security**: Use network policies and security contexts

## 📝 Environment Configuration

Create environment-specific configurations:

### Development
- Single replica per service
- No resource limits
- Debug logging enabled

### Staging
- 2 replicas per service
- Moderate resource limits
- Standard logging

### Production
- 3+ replicas per service
- Strict resource limits
- Minimal logging
- Health checks and monitoring

## 🔗 Useful Commands

```powershell
# Port forward to access services directly
kubectl port-forward svc/auth-service 8000:8000 -n microservices-app
kubectl port-forward svc/backend-service 8080:8080 -n microservices-app
kubectl port-forward svc/frontend 80:80 -n microservices-app

# Get ingress IP
kubectl get ingress -n microservices-app -o wide

# Watch pod status
kubectl get pods -n microservices-app -w

# Get events
kubectl get events -n microservices-app --sort-by='.lastTimestamp'
```

## 🚀 Next Steps

1. **Configure CI/CD pipeline** for automated deployments
2. **Set up monitoring** with Prometheus and Grafana
3. **Implement logging aggregation** with ELK stack
4. **Add database persistence** for stateful services
5. **Configure auto-scaling** based on metrics
6. **Set up alerts** for system health

---

For questions or issues, please check the troubleshooting section or refer to the Kubernetes documentation.
