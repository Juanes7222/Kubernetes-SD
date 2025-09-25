# Kubernetes Resource Inspector
# This script provides detailed inspection of all resources in the microservices namespace

param(
    [string]$Namespace = "microservices-app",
    [string]$ServiceName = "",
    [switch]$Detailed = $false
)

Write-Host "🔍 Kubernetes Resource Inspector" -ForegroundColor Green
Write-Host "Namespace: $Namespace" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray

# Function to show section header
function Show-Section($title) {
    Write-Host ""
    Write-Host "📋 $title" -ForegroundColor Yellow
    Write-Host ("-" * 40) -ForegroundColor Gray
}

# Check cluster connectivity
try {
    kubectl cluster-info --request-timeout=5s | Out-Null
    Write-Host "✅ Connected to Kubernetes cluster" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to Kubernetes cluster!" -ForegroundColor Red
    exit 1
}

# 1. Overview
Show-Section "Resource Overview"
Write-Host "Deployments:" -ForegroundColor White
kubectl get deployments -n $Namespace

Write-Host "`nPods:" -ForegroundColor White
kubectl get pods -n $Namespace -o wide

Write-Host "`nServices:" -ForegroundColor White
kubectl get services -n $Namespace

# 2. ConfigMaps and Secrets
Show-Section "Configuration Resources"
Write-Host "ConfigMaps:" -ForegroundColor White
kubectl get configmaps -n $Namespace

Write-Host "`nSecrets:" -ForegroundColor White
kubectl get secrets -n $Namespace

# 3. Pod Health and Status
Show-Section "Pod Health Analysis"
$unhealthyPods = kubectl get pods -n $Namespace --field-selector=status.phase!=Running --no-headers 2>$null
if ($unhealthyPods) {
    Write-Host "⚠️  Unhealthy Pods Found:" -ForegroundColor Red
    Write-Host $unhealthyPods -ForegroundColor White
} else {
    Write-Host "✅ All pods are healthy and running!" -ForegroundColor Green
}

# 4. Resource Limits and Requests
Show-Section "Resource Allocation"
kubectl describe deployments -n $Namespace | Select-String -Pattern "(Limits|Requests):" -A 2 -B 1

# 5. Environment Variables Check (for specific service or all)
Show-Section "Environment Variables"
if ($ServiceName) {
    $podName = kubectl get pods -n $Namespace -l app=$ServiceName --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>$null
    if ($podName) {
        Write-Host "Environment variables for $ServiceName ($podName):" -ForegroundColor White
        kubectl exec $podName -n $Namespace -- env | Select-String -Pattern "^(ENVIRONMENT|DEBUG|LOG_LEVEL|HOST|PORT|.*SERVICE_URL|SECRET_KEY|FIREBASE)" | Sort-Object
    } else {
        Write-Host "❌ No running pods found for service: $ServiceName" -ForegroundColor Red
    }
} else {
    Write-Host "Specify -ServiceName to check environment variables for a specific service" -ForegroundColor Gray
}

# 6. Recent Events
Show-Section "Recent Events"
kubectl get events -n $Namespace --sort-by=.metadata.creationTimestamp --field-selector type!=Normal | tail -10 2>$null

# 7. Ingress/Networking
Show-Section "Networking"
$ingress = kubectl get ingress -n $Namespace 2>$null
if ($ingress) {
    Write-Host "Ingress Resources:" -ForegroundColor White
    kubectl get ingress -n $Namespace
} else {
    Write-Host "No ingress resources found" -ForegroundColor Gray
}

# 8. Detailed Analysis (if requested)
if ($Detailed) {
    Show-Section "Detailed Analysis"
    
    # Pod resource usage (if metrics server available)
    Write-Host "Attempting to get resource usage..." -ForegroundColor White
    $resourceUsage = kubectl top pods -n $Namespace 2>$null
    if ($resourceUsage) {
        Write-Host $resourceUsage -ForegroundColor White
    } else {
        Write-Host "Metrics server not available - install with 'minikube addons enable metrics-server'" -ForegroundColor Gray
    }
    
    # Detailed pod descriptions for each service
    $services = @("auth-service", "tasks-service", "collaborator-service", "logs-service")
    foreach ($service in $services) {
        $pods = kubectl get pods -n $Namespace -l app=$service --no-headers 2>$null
        if ($pods) {
            Write-Host "`nDetailed info for $service pods:" -ForegroundColor Cyan
            kubectl get pods -n $Namespace -l app=$service -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp"
        }
    }
}

# 9. Troubleshooting Commands
Show-Section "Troubleshooting Commands"
Write-Host "Useful debugging commands:" -ForegroundColor Cyan
Write-Host "  Check pod logs:           kubectl logs -f <pod-name> -n $Namespace" -ForegroundColor White
Write-Host "  Describe problematic pod: kubectl describe pod <pod-name> -n $Namespace" -ForegroundColor White
Write-Host "  Check events:            kubectl get events -n $Namespace --sort-by='.lastTimestamp'" -ForegroundColor White
Write-Host "  Port forward service:    kubectl port-forward svc/<service-name> <local-port>:<service-port> -n $Namespace" -ForegroundColor White
Write-Host "  Execute in pod:          kubectl exec -it <pod-name> -n $Namespace -- /bin/bash" -ForegroundColor White
Write-Host "  Check ConfigMap:         kubectl get configmap <configmap-name> -o yaml -n $Namespace" -ForegroundColor White

# 10. Quick Actions
Show-Section "Quick Actions"
Write-Host "Available inspection options:" -ForegroundColor Cyan
Write-Host "  Detailed analysis:       ./inspect-resources.ps1 -Detailed" -ForegroundColor White
Write-Host "  Specific service env:    ./inspect-resources.ps1 -ServiceName auth-service" -ForegroundColor White
Write-Host "  Check all services:      ./check-status.ps1" -ForegroundColor White

Write-Host ""
Write-Host "🎯 Inspection completed!" -ForegroundColor Green
