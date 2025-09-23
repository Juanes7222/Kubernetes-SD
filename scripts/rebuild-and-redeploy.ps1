# Rebuild and Redeploy Script
# This script rebuilds Docker images with Firebase fixes and redeploys to Kubernetes

Write-Host "Rebuilding and redeploying microservices..." -ForegroundColor Green

# Build images
Write-Host "`nStep 1: Building updated Docker images..." -ForegroundColor Yellow
& "$PSScriptRoot\build-images.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build images" -ForegroundColor Red
    exit 1
}

# Load images to Minikube
Write-Host "`nStep 2: Loading images to Minikube..." -ForegroundColor Yellow
& "$PSScriptRoot\load-images-to-minikube.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to load images to Minikube" -ForegroundColor Red
    exit 1
}

# Restart deployments to use new images
Write-Host "`nStep 3: Restarting deployments..." -ForegroundColor Yellow
kubectl rollout restart deployment auth-service -n microservices-app
kubectl rollout restart deployment tasks-service -n microservices-app  
kubectl rollout restart deployment collaborator-service -n microservices-app

# Wait for deployments to be ready
Write-Host "`nStep 4: Waiting for deployments to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=300s deployment auth-service tasks-service collaborator-service -n microservices-app

# Show status
Write-Host "`nDeployment Status:" -ForegroundColor Cyan
kubectl get deployments -n microservices-app

Write-Host "`nPod Status:" -ForegroundColor Cyan
kubectl get pods -n microservices-app

Write-Host "`nAll services redeployed successfully!" -ForegroundColor Green
