# ============================================================================
# SuperOutfit Installer for Windows (Simple Version)
# ============================================================================
# 
# Usage:
#   irm https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install-simple.ps1 | iex
#
# ============================================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SuperOutfit Installer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$RepoUrl = "https://github.com/egg-rolls/SuperOutfit.git"
$InstallDir = "$env:LOCALAPPDATA\SuperOutfit"

# Step 1: Check Git
Write-Host "=> Checking Git..." -ForegroundColor Cyan
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "   ✓ Git is available" -ForegroundColor Green
} else {
    Write-Host "   ✗ Git is required. Please install from https://git-scm.com/" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
    return
}

# Step 2: Check/Install uv
Write-Host "=> Checking uv..." -ForegroundColor Cyan
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "   ✓ uv is already installed" -ForegroundColor Green
} else {
    Write-Host "   Installing uv..." -ForegroundColor Yellow
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Host "   ✓ uv installed" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed to install uv: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Press Enter to exit..." -ForegroundColor Yellow
        Read-Host
        return
    }
}

# Step 3: Install Python
Write-Host "=> Checking Python..." -ForegroundColor Cyan
$pythonInstalled = $false
if (Get-Command python -ErrorAction SilentlyContinue) {
    $ver = python --version 2>&1
    if ($ver -match "3\.1[1-9]") {
        Write-Host "   ✓ Python $ver" -ForegroundColor Green
        $pythonInstalled = $true
    }
}

if (-not $pythonInstalled) {
    Write-Host "   Installing Python 3.11..." -ForegroundColor Yellow
    uv python install 3.11
    Write-Host "   ✓ Python installed" -ForegroundColor Green
}

# Step 4: Clone or update repository
Write-Host "=> Checking repository..." -ForegroundColor Cyan
if (Test-Path "$InstallDir\.git") {
    Write-Host "   Updating existing installation..." -ForegroundColor Yellow
    Push-Location $InstallDir
    git pull origin master 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Repository updated" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to update repository" -ForegroundColor Red
    }
    Pop-Location
} else {
    Write-Host "   Cloning repository..." -ForegroundColor Yellow
    if (Test-Path $InstallDir) {
        Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
    }
    git clone --depth 1 $RepoUrl $InstallDir 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Repository cloned" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to clone repository" -ForegroundColor Red
        Write-Host ""
        Write-Host "Press Enter to exit..." -ForegroundColor Yellow
        Read-Host
        return
    }
}

# Step 5: Create virtual environment
Write-Host "=> Creating virtual environment..." -ForegroundColor Cyan
Push-Location $InstallDir
uv venv 2>&1 | Out-Null
Pop-Location
Write-Host "   ✓ Virtual environment created" -ForegroundColor Green

# Step 6: Install dependencies
Write-Host "=> Installing dependencies..." -ForegroundColor Cyan
Push-Location $InstallDir
uv pip install -e . 2>&1 | Out-Null
Pop-Location
Write-Host "   ✓ Dependencies installed" -ForegroundColor Green

# Step 7: Initialize data
Write-Host "=> Initializing data..." -ForegroundColor Cyan
Push-Location $InstallDir
& ".\.venv\Scripts\superoutfit.exe" init --quick 2>&1 | Out-Null
Pop-Location
Write-Host "   ✓ Data initialized" -ForegroundColor Green

# Step 8: Add to PATH
Write-Host "=> Adding to PATH..." -ForegroundColor Cyan
$scriptsDir = "$InstallDir\.venv\Scripts"
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$scriptsDir*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$scriptsDir", "User")
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
Write-Host "   ✓ Added to PATH" -ForegroundColor Green

# Done
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Close this window" -ForegroundColor White
Write-Host "    2. Open a NEW PowerShell window" -ForegroundColor White
Write-Host "    3. Run: superoutfit --help" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Yellow
Read-Host
