# Check Kubernetes Deployment Status
# This script provides a comprehensive view of your microservices deployment

param(
    [string]$Namespace = "microservices-app"
)

Write-Host "📊 Kubernetes Deployment Status Check" -ForegroundColor Green
Write-Host "Namespace: $Namespace" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

# Check if cluster is accessible
try {
    kubectl cluster-info --request-timeout=5s | Out-Null
} catch {
    Write-Host "❌ Cannot connect to Kubernetes cluster!" -ForegroundColor Red
    Write-Host "   Make sure Docker Desktop and Minikube are running." -ForegroundColor Yellow
    Write-Host "   Run: ./start-k8s-environment.ps1" -ForegroundColor White
    exit 1
}

Write-Host "✅ Connected to Kubernetes cluster" -ForegroundColor Green
Write-Host ""

# Check namespace
Write-Host "🏢 Namespace Status:" -ForegroundColor Yellow
kubectl get namespace $Namespace 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Namespace '$Namespace' not found!" -ForegroundColor Red
    Write-Host "   Run: ./deploy-configs.ps1 to create it" -ForegroundColor White
    exit 1
}
Write-Host ""

# Check ConfigMaps
Write-Host "🗂️  ConfigMaps:" -ForegroundColor Yellow
kubectl get configmaps -n $Namespace
Write-Host ""

# Check Secrets
Write-Host "🔐 Secrets:" -ForegroundColor Yellow
kubectl get secrets -n $Namespace
Write-Host ""

# Check Deployments
Write-Host "🚀 Deployments:" -ForegroundColor Yellow
kubectl get deployments -n $Namespace
Write-Host ""

# Check Pods
Write-Host "📦 Pods:" -ForegroundColor Yellow
kubectl get pods -n $Namespace -o wide
Write-Host ""

# Check Services
Write-Host "🌐 Services:" -ForegroundColor Yellow
kubectl get services -n $Namespace
Write-Host ""

# Check for any unhealthy pods
Write-Host "🔍 Pod Health Check:" -ForegroundColor Yellow
$unhealthyPods = kubectl get pods -n $Namespace --field-selector=status.phase!=Running --no-headers 2>$null
if ($unhealthyPods) {
    Write-Host "⚠️  Found unhealthy pods:" -ForegroundColor Red
    Write-Host $unhealthyPods -ForegroundColor White
    Write-Host ""
    Write-Host "To debug, run:" -ForegroundColor Cyan
    Write-Host "  kubectl describe pod <pod-name> -n $Namespace" -ForegroundColor White
    Write-Host "  kubectl logs <pod-name> -n $Namespace" -ForegroundColor White
} else {
    Write-Host "✅ All pods are healthy!" -ForegroundColor Green
}
Write-Host ""

# Show useful commands
Write-Host "💡 Useful Commands:" -ForegroundColor Cyan
Write-Host "  View logs:        kubectl logs -f <pod-name> -n $Namespace" -ForegroundColor White
Write-Host "  Port forward:     kubectl port-forward svc/<service-name> <local-port>:<service-port> -n $Namespace" -ForegroundColor White
Write-Host "  Describe resource: kubectl describe <resource-type> <resource-name> -n $Namespace" -ForegroundColor White
Write-Host "  Execute in pod:   kubectl exec -it <pod-name> -n $Namespace -- /bin/bash" -ForegroundColor White
Write-Host ""

# Show port-forwarding examples
Write-Host "🌐 Port Forwarding Examples:" -ForegroundColor Cyan
Write-Host "  Auth Service:     kubectl port-forward svc/auth-service 8000:8000 -n $Namespace" -ForegroundColor White
Write-Host "  Tasks Service:    kubectl port-forward svc/tasks-service 8001:8001 -n $Namespace" -ForegroundColor White
Write-Host "  Collaborator:     kubectl port-forward svc/collaborator-service 8002:8002 -n $Namespace" -ForegroundColor White
Write-Host "  Logs Service:     kubectl port-forward svc/logs-service 8003:8003 -n $Namespace" -ForegroundColor White
