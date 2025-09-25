# 🚀 Start Local Access to Microservices
# This script sets up port forwarding to access your services locally

Write-Host "🚀 Setting up local access to microservices..." -ForegroundColor Green
Write-Host ""

# Function to start port forwarding in background
function Start-PortForward {
    param(
        [string]$Service,
        [int]$LocalPort,
        [int]$RemotePort,
        [string]$Description
    )
    
    Write-Host "🔗 Starting $Description on http://localhost:$LocalPort" -ForegroundColor Cyan
    Start-Job -ScriptBlock {
        param($svc, $local, $remote)
        kubectl port-forward "svc/$svc" "${local}:${remote}" -n microservices-app
    } -ArgumentList $Service, $LocalPort, $RemotePort -Name "PortForward-$Service" | Out-Null
}

# Stop any existing port forwarding jobs
Write-Host "🧹 Cleaning up existing port forwarding..." -ForegroundColor Yellow
Get-Job -Name "PortForward-*" -ErrorAction SilentlyContinue | Stop-Job -ErrorAction SilentlyContinue
Get-Job -Name "PortForward-*" -ErrorAction SilentlyContinue | Remove-Job -ErrorAction SilentlyContinue

# Start port forwarding for all services
Start-PortForward -Service "frontend" -LocalPort 3000 -RemotePort 80 -Description "Frontend"
Start-PortForward -Service "auth-service" -LocalPort 8000 -RemotePort 8000 -Description "Auth Service"
Start-PortForward -Service "tasks-service" -LocalPort 8001 -RemotePort 8001 -Description "Tasks Service"
Start-PortForward -Service "collaborator-service" -LocalPort 8002 -RemotePort 8002 -Description "Collaborator Service"
Start-PortForward -Service "logs-service" -LocalPort 8003 -RemotePort 8003 -Description "Logs Service"

# Wait a moment for port forwarding to start
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ Port forwarding setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access your application:" -ForegroundColor Cyan
Write-Host "   Frontend:      http://localhost:3000" -ForegroundColor White
Write-Host "   Auth API:      http://localhost:8000" -ForegroundColor White
Write-Host "   Tasks API:     http://localhost:8001" -ForegroundColor White
Write-Host "   Collaborator:  http://localhost:8002" -ForegroundColor White
Write-Host "   Logs API:      http://localhost:8003" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Check port forwarding status:" -ForegroundColor Yellow
Write-Host "   Get-Job -Name 'PortForward-*'" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 To stop port forwarding:" -ForegroundColor Red
Write-Host "   Get-Job -Name 'PortForward-*' | Stop-Job; Get-Job -Name 'PortForward-*' | Remove-Job" -ForegroundColor Gray
Write-Host ""
Write-Host "ℹ️  Note: Keep this PowerShell window open to maintain port forwarding" -ForegroundColor Blue

# Show job status
Write-Host "Current port forwarding jobs:" -ForegroundColor Cyan
Get-Job -Name "PortForward-*" | Format-Table Name, State -AutoSize
