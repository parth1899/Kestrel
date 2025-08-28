# PowerShell build script for Windows Security Agent

Write-Host "Building Windows Security Agent..." -ForegroundColor Green

# Set Go environment variables for Windows
$env:GOOS = "windows"
$env:GOARCH = "amd64"

# Clean previous builds
if (Test-Path "windows-agent.exe") {
    Remove-Item "windows-agent.exe" -Force
    Write-Host "Removed previous build" -ForegroundColor Yellow
}

# Download dependencies
Write-Host "Downloading dependencies..." -ForegroundColor Cyan
go mod tidy
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to download dependencies" -ForegroundColor Red
    exit 1
}

# Build the agent
Write-Host "Building agent..." -ForegroundColor Cyan
go build -ldflags="-s -w" -o windows-agent.exe .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Check if build was successful
if (Test-Path "windows-agent.exe") {
    $fileInfo = Get-Item "windows-agent.exe"
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable: windows-agent.exe" -ForegroundColor White
    Write-Host "Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor White
    Write-Host "Created: $($fileInfo.CreationTime)" -ForegroundColor White
} else {
    Write-Host "Build failed! Executable not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "To run the agent:" -ForegroundColor Cyan
Write-Host "  .\windows-agent.exe" -ForegroundColor White
Write-Host ""
Write-Host "To stop the agent:" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C" -ForegroundColor White
Write-Host ""

# Optional: Run the agent
$runAgent = Read-Host "Would you like to run the agent now? (y/n)"
if ($runAgent -eq "y" -or $runAgent -eq "Y") {
    Write-Host "Starting Windows Security Agent..." -ForegroundColor Green
    .\windows-agent.exe
}

