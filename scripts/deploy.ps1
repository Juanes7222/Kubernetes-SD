# Deploy to Kubernetes Script for Microservices
# This script deploys all microservices to Kubernetes

Write-Host "Deploying microservices to Kubernetes..." -ForegroundColor Green

# Set error action preference
$ErrorActionPreference = "Stop"

# Get the root directory (parent of scripts directory)
$rootDir = Split-Path -Parent $PSScriptRoot
$k8sDir = Join-Path $rootDir "k8s"

# Check if kubectl is available
try {
    kubectl version --client | Out-Null
} catch {
    Write-Host "Error: kubectl is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if Kubernetes cluster is accessible
try {
    $clusterInfo = kubectl cluster-info 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Cluster not accessible"
    }
    Write-Host "Kubernetes cluster is accessible." -ForegroundColor Green
    Write-Host "Cluster info:" -ForegroundColor Cyan
    kubectl cluster-info
} catch {
    Write-Host "Error: Cannot connect to Kubernetes cluster." -ForegroundColor Red
    Write-Host "Trying to help you set up Kubernetes..." -ForegroundColor Yellow
    
    # Check if Minikube is available
    try {
        minikube status | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Minikube is available but may not be running." -ForegroundColor Yellow
            Write-Host "Run 'minikube start' to start your cluster." -ForegroundColor Cyan
        }
    } catch {
        Write-Host "Please enable Kubernetes in Docker Desktop or install Minikube." -ForegroundColor Red
        Write-Host "Docker Desktop: Settings > Kubernetes > Enable Kubernetes" -ForegroundColor Cyan
        Write-Host "Minikube: Run 'minikube start'" -ForegroundColor Cyan
    }
    exit 1
}

# Function to apply Kubernetes manifest
function Apply-KubernetesManifest {
    param(
        [string]$ManifestPath,
        [string]$Description
    )
    
    Write-Host "Applying $Description..." -ForegroundColor Yellow
    
    try {
        kubectl apply -f $ManifestPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully applied $Description" -ForegroundColor Green
        } else {
            throw "Failed to apply $Description"
        }
    }
    catch {
        Write-Host "Error applying ${Description}: $_" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Deploy in order (namespace first, then services, then ingress)
$deployments = @(
    @{ Path = "namespace.yaml"; Description = "Namespace" },
    @{ Path = "auth-service-deployment.yaml"; Description = "Auth Service" },
    @{ Path = "..\tasks_service\k8s\deployment.yaml"; Description = "Tasks Service Deployment" },
    @{ Path = "..\tasks_service\k8s\service.yaml"; Description = "Tasks Service" },
    @{ Path = "collaborator-service-deployment.yaml"; Description = "Collaborator Service" },
    @{ Path = "logs-service-deployment.yaml"; Description = "Logs Service" },
    @{ Path = "frontend-deployment.yaml"; Description = "Frontend" },
    @{ Path = "ingress.yaml"; Description = "Ingress" }
)

$success = $true
foreach ($deployment in $deployments) {
    $fullPath = Join-Path $k8sDir $deployment.Path
    
    if (Test-Path $fullPath) {
        $result = Apply-KubernetesManifest -ManifestPath $fullPath -Description $deployment.Description
        if (-not $result) {
            $success = $false
        }
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Manifest not found: $fullPath" -ForegroundColor Red
        $success = $false
    }
}

if ($success) {
    Write-Host "`nAll deployments applied successfully!" -ForegroundColor Green
    
    # Wait for deployments to be ready
    Write-Host "`nWaiting for deployments to be ready..." -ForegroundColor Yellow
    kubectl wait --for=condition=available --timeout=300s deployment --all -n microservices-app
    
    # Show deployment status
    Write-Host "`nDeployment Status:" -ForegroundColor Cyan
    kubectl get deployments -n microservices-app
    
    Write-Host "`nService Status:" -ForegroundColor Cyan
    kubectl get services -n microservices-app
    
    Write-Host "`nPod Status:" -ForegroundColor Cyan
    kubectl get pods -n microservices-app
    
    Write-Host "`nIngress Status:" -ForegroundColor Cyan
    kubectl get ingress -n microservices-app
    
    Write-Host "`nApplication URLs:" -ForegroundColor Green
    Write-Host "Frontend: http://microservices-app.local" -ForegroundColor Cyan
    Write-Host "API: http://microservices-app.local/api" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Add the following to your hosts file:" -ForegroundColor Yellow
    Write-Host "<INGRESS_IP> microservices-app.local" -ForegroundColor Yellow
    
} else {
    Write-Host "`nSome deployments failed. Please check the errors above." -ForegroundColor Red
    exit 1
}
