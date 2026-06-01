# ==========================================
# M8 Intelligent Document Pipeline GUI
# PowerShell Launcher
# ==========================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Activating Environment" -ForegroundColor Cyan
Write-Host "=========================================="

# Activate virtual environment
$venvActivate = "D:\study\sem2\ISE\SE_project\venv\Scripts\Activate.ps1"

if (-Not (Test-Path $venvActivate)) {
    Write-Host "[ERROR] Virtual environment not found at: $venvActivate" -ForegroundColor Red
    exit 1
}

try {
    & $venvActivate
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting M8 PyQt6 GUI" -ForegroundColor Cyan
Write-Host "=========================================="

# Move to project root (important for module imports)
Set-Location "D:\study\sem2\ISE\SE_project"

try {
    python -m src.pipeline.m8_gui.app
} catch {
    Write-Host "[ERROR] Application crashed or failed to start" -ForegroundColor Red
    Write-Host $_
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Execution Finished" -ForegroundColor Cyan
Write-Host "=========================================="

Read-Host "Press Enter to close"