# Cleanup Kubernetes Deployment Script
# This script removes all microservices deployments from Kubernetes

Write-Host "Cleaning up microservices deployment from Kubernetes..." -ForegroundColor Yellow

# Set error action preference
$ErrorActionPreference = "Continue"

# Check if kubectl is available
try {
    kubectl version --client | Out-Null
} catch {
    Write-Host "Error: kubectl is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Function to delete Kubernetes resources
function Delete-KubernetesResource {
    param(
        [string]$ResourceType,
        [string]$ResourceName,
        [string]$Namespace = "microservices-app"
    )
    
    Write-Host "Deleting $ResourceType/$ResourceName..." -ForegroundColor Yellow
    
    try {
        if ($Namespace) {
            kubectl delete $ResourceType $ResourceName -n $Namespace --ignore-not-found=true
        } else {
            kubectl delete $ResourceType $ResourceName --ignore-not-found=true
        }
    }
    catch {
        Write-Host "Error deleting ${ResourceType}/${ResourceName}: $_" -ForegroundColor Red
    }
}

# Delete resources in reverse order
Write-Host "Deleting ingress..." -ForegroundColor Yellow
Delete-KubernetesResource -ResourceType "ingress" -ResourceName "microservices-ingress"

Write-Host "Deleting services..." -ForegroundColor Yellow
$services = @("frontend", "auth-service", "tasks-service", "collaborator-service", "logs-service")
foreach ($service in $services) {
    Delete-KubernetesResource -ResourceType "service" -ResourceName $service
}

Write-Host "Deleting deployments..." -ForegroundColor Yellow
$deployments = @("frontend", "auth-service", "tasks-service", "collaborator-service", "logs-service")
foreach ($deployment in $deployments) {
    Delete-KubernetesResource -ResourceType "deployment" -ResourceName $deployment
}

Write-Host "Deleting namespace..." -ForegroundColor Yellow
kubectl delete namespace microservices-app --ignore-not-found=true

Write-Host "`nWaiting for resources to be fully deleted..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if namespace is deleted
$namespaceExists = kubectl get namespace microservices-app --ignore-not-found=true 2>$null
if (-not $namespaceExists) {
    Write-Host "Cleanup completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Namespace still exists. Resources may still be terminating." -ForegroundColor Yellow
    Write-Host "Run 'kubectl get all -n microservices-app' to check remaining resources." -ForegroundColor Cyan
}

Write-Host "`nTo also remove Docker images, run:" -ForegroundColor Cyan
Write-Host "docker rmi auth-service:latest backend-service:latest tasks-service:latest collaborator-service:latest logs-service:latest frontend:latest" -ForegroundColor Yellow
