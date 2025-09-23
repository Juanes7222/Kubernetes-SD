# Load Docker Images to Minikube Script
# This script loads all Docker images into Minikube's Docker registry

Write-Host "Loading Docker images into Minikube..." -ForegroundColor Green

# Define the images to load
$images = @(
    "auth-service:latest",
    "tasks-service:latest", 
    "collaborator-service:latest",
    "logs-service:latest",
    "frontend:latest"
)

# Function to load image into Minikube
function Load-ImageToMinikube {
    param([string]$ImageName)
    
    Write-Host "Loading $ImageName into Minikube..." -ForegroundColor Yellow
    
    try {
        minikube image load $ImageName
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully loaded $ImageName" -ForegroundColor Green
            return $true
        } else {
            throw "Failed to load $ImageName"
        }
    }
    catch {
        Write-Host "Error loading ${ImageName}: $_" -ForegroundColor Red
        return $false
    }
}

# Load all images
$success = $true
foreach ($image in $images) {
    $result = Load-ImageToMinikube -ImageName $image
    if (-not $result) {
        $success = $false
    }
}

if ($success) {
    Write-Host "`nAll images loaded successfully into Minikube!" -ForegroundColor Green
    Write-Host "You can now run 'scripts/deploy.ps1' to deploy to Kubernetes" -ForegroundColor Cyan
    
    # List images in Minikube
    Write-Host "`nImages in Minikube:" -ForegroundColor Cyan
    minikube image ls | Select-String "auth-service|tasks-service|collaborator-service|logs-service|frontend"
} else {
    Write-Host "`nSome images failed to load. Please check the errors above." -ForegroundColor Red
    exit 1
}
