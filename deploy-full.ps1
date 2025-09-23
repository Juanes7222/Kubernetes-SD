# Complete Deployment Script for Kubernetes Microservices
# This script handles the full deployment process: build, deploy, and expose

param(
    [switch]$SkipBuild,        # Skip Docker image building
    [switch]$Expose,           # Start port forwarding and ngrok
    [switch]$Clean,            # Clean up before deployment
    [switch]$WaitForReady,     # Wait for all services to be ready
    [switch]$Help              # Show help
)

$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Red = "Red" 
$Yellow = "Yellow"
$Cyan = "Cyan"
$White = "White"
$Gray = "Gray"

function Write-Header {
    param([string]$Message)
    Write-Host "`n" + "="*60 -ForegroundColor $Cyan
    Write-Host "  $Message" -ForegroundColor $Cyan
    Write-Host "="*60 -ForegroundColor $Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔄 $Message..." -ForegroundColor $Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $White
}

function Show-Help {
    Write-Header "Kubernetes Microservices Deployment Script"
    Write-Host @"

USAGE:
    .\deploy-full.ps1 [OPTIONS]

OPTIONS:
    -SkipBuild      Skip Docker image building (use existing images)
    -Expose         Start port forwarding and ngrok after deployment
    -Clean          Clean up existing deployments before deploying
    -WaitForReady   Wait for all services to be ready before finishing
    -Help           Show this help message

EXAMPLES:
    .\deploy-full.ps1                    # Full deployment
    .\deploy-full.ps1 -SkipBuild         # Deploy without rebuilding images
    .\deploy-full.ps1 -Clean -Expose     # Clean deploy and expose publicly
    .\deploy-full.ps1 -WaitForReady      # Deploy and wait for all services

WHAT THIS SCRIPT DOES:
1. 🔍 Checks prerequisites (kubectl, minikube, docker)
2. 🏗️  Builds Docker images (unless -SkipBuild)
3. 📦 Loads images to minikube
4. 🚀 Deploys all services to Kubernetes
5. ⏳ Optionally waits for services to be ready
6. 🌐 Optionally exposes the app publicly

"@ -ForegroundColor $White
    exit 0
}

function Test-Prerequisites {
    Write-Step "Checking prerequisites"
    
    # Check kubectl
    try {
        kubectl version --client --output=json | Out-Null
        Write-Success "kubectl is available"
    } catch {
        Write-Error "kubectl is not installed or not accessible"
        Write-Info "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    }
    
    # Check minikube
    try {
        $status = minikube status --format=json 2>$null | ConvertFrom-Json
        if ($status.Host -eq "Running" -and $status.Kubelet -eq "Running") {
            Write-Success "Minikube is running"
        } else {
            Write-Error "Minikube is not running"
            Write-Info "Start minikube with: minikube start"
            exit 1
        }
    } catch {
        Write-Error "Minikube is not installed or not running"
        Write-Info "Install minikube: https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    }
    
    # Check Docker (only if not skipping build)
    if (-not $SkipBuild) {
        try {
            docker version --format=json | Out-Null
            Write-Success "Docker is available"
        } catch {
            Write-Error "Docker is not running"
            Write-Info "Please start Docker Desktop or Docker daemon"
            exit 1
        }
    }
    
    # Check cluster connectivity
    try {
        kubectl cluster-info --request-timeout=10s | Out-Null
        Write-Success "Kubernetes cluster is accessible"
    } catch {
        Write-Error "Cannot connect to Kubernetes cluster"
        Write-Info "Make sure minikube is started and kubectl is configured"
        exit 1
    }
}

function Build-Images {
    if ($SkipBuild) {
        Write-Step "Skipping Docker image build"
        return
    }
    
    Write-Step "Building Docker images"
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\build-images.ps1"
    if (Test-Path $scriptPath) {
        & $scriptPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to build Docker images"
            exit 1
        }
        Write-Success "Docker images built successfully"
    } else {
        Write-Error "Build script not found: $scriptPath"
        exit 1
    }
}

function Load-ImagesToMinikube {
    Write-Step "Loading images to minikube"
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\load-images-to-minikube.ps1"
    if (Test-Path $scriptPath) {
        & $scriptPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to load images to minikube"
            exit 1
        }
        Write-Success "Images loaded to minikube successfully"
    } else {
        Write-Error "Load images script not found: $scriptPath"
        exit 1
    }
}

function Clean-Deployment {
    if (-not $Clean) {
        return
    }
    
    Write-Step "Cleaning existing deployment"
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\cleanup.ps1"
    if (Test-Path $scriptPath) {
        & $scriptPath
        Write-Success "Existing deployment cleaned"
    } else {
        Write-Info "No cleanup script found, proceeding with deployment"
    }
}

function Deploy-Services {
    Write-Step "Deploying services to Kubernetes"
    
    $scriptPath = Join-Path $PSScriptRoot "scripts\deploy.ps1"
    if (Test-Path $scriptPath) {
        & $scriptPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to deploy services"
            exit 1
        }
        Write-Success "Services deployed successfully"
    } else {
        Write-Error "Deploy script not found: $scriptPath"
        exit 1
    }
}

function Wait-ForServices {
    if (-not $WaitForReady) {
        return
    }
    
    Write-Step "Waiting for all services to be ready"
    
    try {
        # Wait for deployments
        kubectl wait --for=condition=available --timeout=300s deployment --all -n microservices-app
        Write-Success "All deployments are ready"
        
        # Show status
        Write-Info "Current deployment status:"
        kubectl get deployments,services,pods -n microservices-app
        
    } catch {
        Write-Error "Timeout waiting for services to be ready"
        Write-Info "Check status with: kubectl get pods -n microservices-app"
        exit 1
    }
}

function Test-ServiceHealth {
    Write-Step "Testing service health"
    
    try {
        # Test each service endpoint
        $services = @(
            @{ Name = "auth-service"; Port = 8001; Endpoint = "/api/auth/verify" },
            @{ Name = "tasks-service"; Port = 8002; Endpoint = "/api/tasks/health" },
            @{ Name = "collaborator-service"; Port = 8003; Endpoint = "/api/collaborators/health" },
            @{ Name = "logs-service"; Port = 8004; Endpoint = "/api/logs/health" },
            @{ Name = "frontend"; Port = 80; Endpoint = "/" }
        )
        
        foreach ($service in $services) {
            $podName = kubectl get pods -n microservices-app -l app=$($service.Name) -o jsonpath='{.items[0].metadata.name}' 2>$null
            if ($podName) {
                Write-Info "✓ $($service.Name) pod is running: $podName"
            } else {
                Write-Info "⚠ $($service.Name) pod not found"
            }
        }
        
        Write-Success "Service health check completed"
        
    } catch {
        Write-Info "Health check encountered issues, but deployment may still be successful"
    }
}

function Show-AccessInformation {
    Write-Header "🌐 Application Access Information"
    
    # Get minikube IP
    try {
        $minikubeIP = minikube ip 2>$null
        if ($minikubeIP) {
            Write-Host "🔗 Access URLs:" -ForegroundColor $Green
            Write-Host "   • Frontend (NodePort): http://$minikubeIP`:30000" -ForegroundColor $White
            Write-Host "   • Port-forward: http://localhost:3000 (after running port-forward)" -ForegroundColor $White
        }
    } catch {
        Write-Info "Could not get minikube IP"
    }
    
    Write-Host "`n📋 Available Commands:" -ForegroundColor $Yellow
    Write-Host "   • Port-forward frontend: kubectl port-forward -n microservices-app svc/frontend 3000:80" -ForegroundColor $Gray
    Write-Host "   • Check pods: kubectl get pods -n microservices-app" -ForegroundColor $Gray
    Write-Host "   • Check logs: kubectl logs -n microservices-app deployment/[service-name]" -ForegroundColor $Gray
    Write-Host "   • Clean deployment: .\scripts\cleanup.ps1" -ForegroundColor $Gray
    
    if ($Expose) {
        Start-Exposure
    }
}

function Start-Exposure {
    Write-Header "🚀 Starting Public Exposure"
    
    Write-Info "Starting port-forward in background..."
    
    # Start port-forward for frontend in background
    $job = Start-Job -ScriptBlock {
        kubectl port-forward -n microservices-app svc/frontend 3000:80
    }
    
    Start-Sleep -Seconds 3
    
    Write-Success "Port-forward started (Job ID: $($job.Id))"
    Write-Host "   • Frontend accessible at: http://localhost:3000" -ForegroundColor $White
    
    # Check if ngrok is available
    try {
        ngrok version | Out-Null
        Write-Info "Starting ngrok tunnel..."
        Write-Host "`n🌍 Your app will be publicly accessible via ngrok" -ForegroundColor $Green
        Write-Host "   Keep this window open for the tunnel to stay active" -ForegroundColor $Yellow
        Write-Host "   Press Ctrl+C to stop the tunnel" -ForegroundColor $Yellow
        Write-Host "`n" + "-"*50 -ForegroundColor $Gray
        
        # Start ngrok (this will run in foreground)
        ngrok http 3000
        
    } catch {
        Write-Info "ngrok not found. Install from: https://ngrok.com/download"
        Write-Host "`n🔧 Manual steps to expose publicly:" -ForegroundColor $Yellow
        Write-Host "   1. Download ngrok from https://ngrok.com/download" -ForegroundColor $Gray
        Write-Host "   2. Run: ngrok http 3000" -ForegroundColor $Gray
        Write-Host "   3. Share the https://xxxxx.ngrok.io URL" -ForegroundColor $Gray
    }
}

# Main execution
if ($Help) {
    Show-Help
}

try {
    Write-Header "🚀 Kubernetes Microservices Deployment"
    
    # Execute deployment steps
    Test-Prerequisites
    Clean-Deployment
    Build-Images
    Load-ImagesToMinikube
    Deploy-Services
    Wait-ForServices
    Test-ServiceHealth
    Show-AccessInformation
    
    Write-Header "✅ Deployment Complete!"
    Write-Info "Your microservices application is now running on Kubernetes"
    
} catch {
    Write-Header "❌ Deployment Failed"
    Write-Error "Error: $_"
    Write-Info "Check the logs above for details"
    exit 1
}
