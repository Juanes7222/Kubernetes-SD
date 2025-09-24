# Build Docker Images Script for Microservices
# This script builds Docker images for all microservices

Write-Host "Building Docker images for all microservices..." -ForegroundColor Green

# Set error action preference
$ErrorActionPreference = "Stop"

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "Docker is running." -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -PassThru | Out-Null
        Write-Host "Docker Desktop started. Please wait a moment for it to initialize and try again." -ForegroundColor Yellow
    } catch {
        Write-Host "Could not start Docker Desktop automatically. Please start it manually." -ForegroundColor Red
    }
    exit 1
}

# Get the root directory (parent of scripts directory)
$rootDir = Split-Path -Parent $PSScriptRoot

# Define services and their respective directories
$services = @{
    "auth-service" = "auth_service"
    "tasks-service" = "tasks_service"
    "collaborator-service" = "collaborator_service"
    "logs-service" = "logs_service"
    "frontend" = "frontend"
}

# Function to build Docker image
function Build-DockerImage {
    param(
        [string]$ServiceName,
        [string]$ServicePath,
        [string]$RootDirectory
    )
    
    Write-Host "Building $ServiceName..." -ForegroundColor Yellow
    
    $fullPath = Join-Path $RootDirectory $ServicePath
    
    if (Test-Path $fullPath) {
        try {
            # Change to service directory
            Push-Location $fullPath
            
            # Build the Docker image
            docker build -t "${ServiceName}:latest" .
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Successfully built $ServiceName" -ForegroundColor Green
            } else {
                throw "Failed to build $ServiceName"
            }
        }
        catch {
            Write-Host "Error building ${ServiceName}: $_" -ForegroundColor Red
            return $false
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "Directory not found: $fullPath" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Build all services
$success = $true
foreach ($service in $services.GetEnumerator()) {
    $result = Build-DockerImage -ServiceName $service.Key -ServicePath $service.Value -RootDirectory $rootDir
    if (-not $result) {
        $success = $false
    }
}

if ($success) {
    Write-Host "`nAll Docker images built successfully!" -ForegroundColor Green
    Write-Host "You can now run 'scripts/deploy.ps1' to deploy to Kubernetes" -ForegroundColor Cyan
} else {
    Write-Host "`nSome Docker images failed to build. Please check the errors above." -ForegroundColor Red
    exit 1
}

# List built images
Write-Host "`nBuilt images:" -ForegroundColor Cyan
docker images | Select-String "auth-service|tasks-service|collaborator-service|logs-service|frontend"
