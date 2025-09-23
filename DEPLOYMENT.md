# 🚀 Microservices Task Manager - Deployment Guide

This guide covers all deployment options for your Kubernetes microservices application, from local development to public cloud deployment.

## 🎯 Quick Start (Local Development)

**For local development with minikube, use the master deployment script:**

```powershell
# Complete deployment with everything (recommended)
.\deploy-full.ps1 -WaitForReady -Expose

# Or just deploy locally
.\deploy-full.ps1 -WaitForReady
```

## 📋 Available Deployment Scripts

### Master Script: `deploy-full.ps1` (Recommended)
```powershell
.\deploy-full.ps1 -Help          # Show all options
.\deploy-full.ps1               # Full deployment
.\deploy-full.ps1 -Clean        # Clean deployment
.\deploy-full.ps1 -Expose       # Deploy and expose publicly
.\deploy-full.ps1 -SkipBuild    # Skip image building
```

### Individual Scripts (in `scripts/` folder)
- `build-images.ps1` - Build all Docker images
- `deploy.ps1` - Deploy to Kubernetes
- `rebuild-and-redeploy.ps1` - Rebuild and redeploy services
- `cleanup.ps1` - Remove all deployments

### Exposure Script
- `expose-app.ps1` - Set up port forwarding and ngrok for public access

---

# 🌐 Public/Cloud Deployment Guide

This section covers deploying to any Kubernetes cluster for public access.

## Prerequisites

1. **Kubernetes cluster** with:
   - NGINX Ingress Controller installed
   - At least 4GB RAM and 2 CPU cores available
   - LoadBalancer service support (cloud provider) OR NodePort access

2. **Docker images** built and available in a registry accessible to your cluster

3. **Firebase credentials** for authentication services

## Quick Deployment Steps

### 1. Setup Firebase Secret

First, create the Firebase credentials secret with your Firebase service account JSON:

```bash
kubectl create secret generic firebase-credentials \
  --from-file=kubernetes-sd.json=/path/to/your/firebase-credentials.json \
  -n microservices-app
```

### 2. Deploy All Services

Apply the complete deployment manifest:

```bash
kubectl apply -f k8s/complete-deployment.yaml
```

### 3. Install NGINX Ingress Controller (if not already installed)

For most cloud providers:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

For local/on-premise clusters:
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/baremetal/deploy.yaml
```

### 4. Get Access Information

Check the external IP or access method:
```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

## Building and Pushing Docker Images

If you need to make your images available in a public registry:

### 1. Build all images
```bash
# Build frontend
docker build -t your-registry/frontend:latest ./frontend

# Build auth service
docker build -t your-registry/auth-service:latest ./auth_service

# Build tasks service  
docker build -t your-registry/tasks-service:latest ./tasks_service

# Build collaborator service
docker build -t your-registry/collaborator-service:latest ./collaborator_service

# Build logs service
docker build -t your-registry/logs-service:latest ./logs_service
```

### 2. Push to registry
```bash
docker push your-registry/frontend:latest
docker push your-registry/auth-service:latest
docker push your-registry/tasks-service:latest
docker push your-registry/collaborator-service:latest
docker push your-registry/logs-service:latest
```

### 3. Update deployment manifest
Edit `k8s/complete-deployment.yaml` and replace all `image: service-name:latest` with your registry URLs:
```yaml
image: your-registry/frontend:latest
image: your-registry/auth-service:latest
# etc...
```

## Cloud Provider Specific Notes

### AWS EKS
- The LoadBalancer service will automatically create an ALB/NLB
- Access via the load balancer DNS name

### Google GKE  
- The LoadBalancer service will create a Google Cloud Load Balancer
- Access via the external IP

### Azure AKS
- The LoadBalancer service will create an Azure Load Balancer
- Access via the external IP

### DigitalOcean Kubernetes
- The LoadBalancer service will create a DigitalOcean Load Balancer
- Access via the external IP

## Verification

1. Check all pods are running:
```bash
kubectl get pods -n microservices-app
```

2. Check services:
```bash
kubectl get svc -n microservices-app
```

3. Check ingress:
```bash
kubectl get ingress -n microservices-app
```

4. Test API endpoints:
```bash
curl http://YOUR-EXTERNAL-IP/api/auth/verify
# Should return 401 (expected without auth)
```

5. Access the frontend:
Navigate to `http://YOUR-EXTERNAL-IP` in your browser

## Environment Variables

The frontend is configured to use relative URLs, which means:
- `REACT_APP_AUTH_SERVICE_URL=""` → API calls go to `/api/auth/*`
- `REACT_APP_TASKS_SERVICE_URL=""` → API calls go to `/api/tasks/*`  
- etc.

This allows the application to work with any domain/IP address.

## Scaling

You can scale services independently:
```bash
kubectl scale deployment frontend --replicas=3 -n microservices-app
kubectl scale deployment auth-service --replicas=3 -n microservices-app
```

## Monitoring

Check logs:
```bash
kubectl logs -f deployment/frontend -n microservices-app
kubectl logs -f deployment/auth-service -n microservices-app
```

## Security Notes

1. The application uses Firebase for authentication
2. CORS is configured to allow requests from any origin (`*`)
3. All inter-service communication happens within the cluster
4. The ingress handles external traffic routing

## Troubleshooting

### Common Issues

1. **Pods stuck in Pending**: Check resource limits and node capacity
2. **ImagePullBackOff**: Ensure images are accessible from the cluster
3. **502/504 errors**: Check service endpoints and pod health
4. **Firebase errors**: Verify the Firebase credentials secret is created correctly

### Debug Commands
```bash
kubectl describe pod POD-NAME -n microservices-app
kubectl logs POD-NAME -n microservices-app
kubectl get events -n microservices-app --sort-by='.lastTimestamp'
```

## Next Steps

- Configure a proper domain name and SSL certificates
- Set up monitoring and alerting
- Configure backup strategies for any persistent data
- Implement CI/CD pipelines for automated deployments
