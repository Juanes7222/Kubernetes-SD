# Deploy Kubernetes configurations for microservices
# Usage: ./deploy-configs.ps1 [Environment]
# Environment can be: development, production (default: production)

param(
    [string]$Environment = "production"
)

$NAMESPACE = "microservices-app"

Write-Host "Deploying Kubernetes configurations for environment: $Environment" -ForegroundColor Green

# Create namespace if it doesn't exist
Write-Host "Creating namespace..." -ForegroundColor Yellow
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

Write-Host "Applying ConfigMaps..." -ForegroundColor Yellow

# Apply common ConfigMaps
kubectl apply -f ..\configmaps\common-config.yaml -n $NAMESPACE
kubectl apply -f ..\configmaps\service-urls-config.yaml -n $NAMESPACE
kubectl apply -f ..\configmaps\service-ports-config.yaml -n $NAMESPACE

# Apply environment-specific configuration
$envConfigPath = "..\environments\$Environment\config.yaml"
if (Test-Path $envConfigPath) {
    Write-Host "Applying $Environment environment configuration..." -ForegroundColor Yellow
    kubectl apply -f $envConfigPath -n $NAMESPACE
} else {
    Write-Host "Warning: No configuration found for environment '$Environment', using production defaults" -ForegroundColor Yellow
    kubectl apply -f ..\environments\production\config.yaml -n $NAMESPACE
}

Write-Host "Applying Secrets..." -ForegroundColor Yellow
kubectl apply -f ..\secrets\app-secrets.yaml -n $NAMESPACE

Write-Host "Applying Deployments..." -ForegroundColor Yellow
kubectl apply -f ..\auth-service-deployment.yaml -n $NAMESPACE
kubectl apply -f ..\tasks-service-deployment.yaml -n $NAMESPACE
kubectl apply -f ..\collaborator-service-deployment.yaml -n $NAMESPACE
kubectl apply -f ..\logs-service-deployment.yaml -n $NAMESPACE

Write-Host "Applying other resources..." -ForegroundColor Yellow
if (Test-Path ..\namespace.yaml) {
    kubectl apply -f ..\namespace.yaml
}

if (Test-Path ..\ingress.yaml) {
    kubectl apply -f ..\ingress.yaml -n $NAMESPACE
}

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "To check status, run:" -ForegroundColor Cyan
Write-Host "  kubectl get pods -n $NAMESPACE" -ForegroundColor White
Write-Host "  kubectl get services -n $NAMESPACE" -ForegroundColor White
Write-Host "  kubectl get configmaps -n $NAMESPACE" -ForegroundColor White
Write-Host "  kubectl get secrets -n $NAMESPACE" -ForegroundColor White
