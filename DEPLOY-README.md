# 🚀 Quick Deployment Guide

## One-Command Deployment

**Deploy everything with one command:**

```powershell
# Complete deployment (build, deploy, wait, and expose publicly)
.\deploy-full.ps1 -WaitForReady -Expose
```

## What You Get

✅ **Automated deployment process**  
✅ **Environment validation**  
✅ **Docker image building and loading**  
✅ **Kubernetes deployment**  
✅ **Health checks**  
✅ **Public exposure via ngrok**  

## Quick Commands

```powershell
# Show all options
.\deploy-full.ps1 -Help

# Full deployment
.\deploy-full.ps1

# Clean deployment (remove old, deploy new)
.\deploy-full.ps1 -Clean -WaitForReady

# Deploy without rebuilding images
.\deploy-full.ps1 -SkipBuild

# Deploy and expose publicly
.\deploy-full.ps1 -Expose
```

## Prerequisites

Before running, make sure:

- ✅ Docker Desktop is running
- ✅ Minikube is started (`minikube start`)
- ✅ kubectl is installed
- ✅ (Optional) ngrok for public access

## Access Your App

After deployment:

- **Local**: `http://localhost:3000` (with port-forward)
- **Cluster**: `http://<minikube-ip>:30000`
- **Public**: ngrok HTTPS URL (when using `-Expose`)

## Troubleshooting

```powershell
# Check what's running
kubectl get pods -n microservices-app

# Clean up everything
.\scripts\cleanup.ps1

# Start fresh
.\deploy-full.ps1 -Clean -WaitForReady
```

**💡 Need help?** Run `.\deploy-full.ps1 -Help` for detailed information!
