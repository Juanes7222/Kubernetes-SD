# Start Kubernetes Development Environment
# This script will start Docker Desktop and Minikube, then deploy the configurations

param(
    [string]$Environment = "development"
)

Write-Host "🚀 Starting Kubernetes Development Environment" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Cyan

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        $result = docker ps 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Function to check if Docker Desktop service is running
function Test-DockerServiceRunning {
    try {
        $service = Get-Service -Name "com.docker.service" -ErrorAction SilentlyContinue
        return $service -and $service.Status -eq "Running"
    }
    catch {
        return $false
    }
}

# Function to start Docker Desktop
function Start-DockerDesktop {
    Write-Host "🔄 Starting Docker Desktop..." -ForegroundColor Yellow
    
    # Try to start Docker Desktop executable
    try {
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction Stop
    }
    catch {
        Write-Host "❌ Could not start Docker Desktop. Please start it manually." -ForegroundColor Red
        return $false
    }
    
    # Wait for Docker to start (up to 2 minutes)
    $timeout = 120
    $elapsed = 0
    
    Write-Host "⏳ Waiting for Docker Desktop to initialize (this may take 1-2 minutes)..." -ForegroundColor Yellow
    
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 5
        $elapsed += 5
        
        Write-Host "." -NoNewline -ForegroundColor Gray
        
        if (Test-DockerRunning) {
            Write-Host ""
            Write-Host "✅ Docker Desktop is now running!" -ForegroundColor Green
            return $true
        }
    }
    
    Write-Host ""
    Write-Host "❌ Docker Desktop did not start within $timeout seconds." -ForegroundColor Red
    return $false
}

# Function to check if Minikube is running
function Test-MinikubeRunning {
    try {
        $status = minikube status 2>$null
        return $status -match "Running"
    }
    catch {
        return $false
    }
}

# Check if Docker is running
Write-Host "🐳 Checking Docker status..." -ForegroundColor Yellow
if (-not (Test-DockerRunning)) {
    Write-Host "❌ Docker is not running." -ForegroundColor Red
    
    # Try to start Docker Desktop automatically
    if (-not (Start-DockerDesktop)) {
        Write-Host "❌ Failed to start Docker Desktop automatically." -ForegroundColor Red
        Write-Host "Please start Docker Desktop manually:" -ForegroundColor Yellow
        Write-Host "   1. Open Docker Desktop from the Windows Start menu" -ForegroundColor White
        Write-Host "   2. Wait for Docker to start (you'll see the Docker whale icon in the system tray)" -ForegroundColor White
        Write-Host "   3. Run this script again" -ForegroundColor White
        exit 1
    }
}

Write-Host "✅ Docker is running!" -ForegroundColor Green

# Check if Minikube is running
Write-Host "☸️  Checking Minikube status..." -ForegroundColor Yellow
if (-not (Test-MinikubeRunning)) {
    Write-Host "🔄 Starting Minikube..." -ForegroundColor Yellow
    minikube start
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to start Minikube. Check the error messages above." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Minikube is already running!" -ForegroundColor Green
}

# Verify kubectl connection
Write-Host "🔍 Verifying kubectl connection..." -ForegroundColor Yellow
try {
    kubectl cluster-info | Out-Null
    Write-Host "✅ kubectl connected to cluster!" -ForegroundColor Green
} catch {
    Write-Host "❌ kubectl cannot connect to cluster. Check Minikube status." -ForegroundColor Red
    minikube status
    exit 1
}

# Deploy configurations
Write-Host "📦 Deploying Kubernetes configurations..." -ForegroundColor Yellow
try {
    & "./deploy-configs.ps1" $Environment
    Write-Host "✅ Configurations deployed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to deploy configurations. Error: $_" -ForegroundColor Red
    exit 1
}

# Show status
Write-Host "📊 Current cluster status:" -ForegroundColor Cyan
kubectl get namespaces
Write-Host ""
kubectl get pods -n microservices-app
Write-Host ""
kubectl get services -n microservices-app

Write-Host "🎉 Environment is ready!" -ForegroundColor Green
Write-Host "To access your services, you can use port-forwarding:" -ForegroundColor Cyan
Write-Host "  kubectl port-forward svc/auth-service 8000:8000 -n microservices-app" -ForegroundColor White
Write-Host "  kubectl port-forward svc/tasks-service 8001:8001 -n microservices-app" -ForegroundColor White
