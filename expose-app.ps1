# Expose Kubernetes Microservices App Publicly
# This script sets up port forwarding and provides instructions for public access

Write-Host "🚀 Kubernetes Microservices Public Exposure" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Check if all services are running
Write-Host "`n🔍 Checking if services are running..." -ForegroundColor Yellow

try {
    $pods = kubectl get pods -n microservices-app --no-headers 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Cannot connect to Kubernetes cluster" -ForegroundColor Red
        Write-Host "   Make sure minikube is running: minikube start" -ForegroundColor Gray
        exit 1
    }
    
    $runningPods = ($pods | Where-Object { $_ -match "Running" } | Measure-Object).Count
    $totalPods = ($pods | Measure-Object).Count
    
    if ($runningPods -eq 0) {
        Write-Host "❌ No running pods found" -ForegroundColor Red
        Write-Host "   Deploy the app first: kubectl apply -f k8s/complete-deployment.yaml" -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "✅ Found $runningPods/$totalPods pods running" -ForegroundColor Green
    
    # Test API connectivity
    $testResponse = curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/api/auth/verify" 2>$null
    if ($testResponse -eq "401") {
        Write-Host "✅ API endpoints are responding correctly" -ForegroundColor Green
    } else {
        Write-Host "⚠️  API endpoints may not be fully ready yet" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Error checking cluster status: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🌐 Your app is currently accessible at:" -ForegroundColor Cyan
Write-Host "   Local: http://127.0.0.1" -ForegroundColor White
Write-Host "   (This only works from your computer)" -ForegroundColor Gray

Write-Host "`n📡 To make it accessible from ANYWHERE on the internet:" -ForegroundColor Green
Write-Host "`n1. Download ngrok:" -ForegroundColor Yellow
Write-Host "   • Go to: https://ngrok.com/download" -ForegroundColor Gray
Write-Host "   • Create a free account (optional but recommended)" -ForegroundColor Gray
Write-Host "   • Download ngrok.exe and put it somewhere in your PATH" -ForegroundColor Gray

Write-Host "`n2. Start port forwarding (in this window):" -ForegroundColor Yellow
Write-Host "   kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80" -ForegroundColor White

Write-Host "`n3. In a NEW terminal/command window, run:" -ForegroundColor Yellow
Write-Host "   ngrok http 8080" -ForegroundColor White

Write-Host "`n4. Copy the https://xxxxx.ngrok.io URL and share it!" -ForegroundColor Yellow

Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "🎯 Quick Start - Run these commands:" -ForegroundColor Green
Write-Host "`nTerminal 1 (this window):" -ForegroundColor Yellow
Write-Host "kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80" -ForegroundColor White
Write-Host "`nTerminal 2 (new window):" -ForegroundColor Yellow  
Write-Host "ngrok http 8080" -ForegroundColor White
Write-Host "="*50 -ForegroundColor Cyan

$response = Read-Host "`n🚀 Start port forwarding now? (y/N)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "`n🔧 Starting port forwarding on port 8080..." -ForegroundColor Yellow
    Write-Host "⚠️  Keep this window open! Press Ctrl+C to stop" -ForegroundColor Red
    Write-Host "`n📱 Your app will be available at:" -ForegroundColor Green
    Write-Host "   • Local: http://localhost:8080" -ForegroundColor White
    Write-Host "   • Public: Run 'ngrok http 8080' in another terminal" -ForegroundColor White
    Write-Host "`n" + "-"*50 -ForegroundColor Gray
    
    kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
} else {
    Write-Host "`n✨ When you're ready:" -ForegroundColor Cyan
    Write-Host "   kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80" -ForegroundColor White
}
