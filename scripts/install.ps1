# ============================================================================
# SuperOutfit Installer for Windows
# ============================================================================
# Installation script for Windows (PowerShell).
# Uses uv for fast Python provisioning and package management.
#
# Usage:
#   irm https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install.ps1 | iex
#
# Or download and run:
#   .\install.ps1
#
# ============================================================================

# Don't use param() - it doesn't work with iex
# Don't use $ErrorActionPreference = "Stop" - it causes silent exits

# Suppress progress bar for faster downloads
$ProgressPreference = "SilentlyContinue"

# ============================================================================
# Configuration
# ============================================================================

$RepoUrl = "https://github.com/egg-rolls/SuperOutfit.git"
$PythonVersion = "3.11"
$InstallDir = "$env:LOCALAPPDATA\SuperOutfit"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "   ✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "   ⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "   ✗ $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# ============================================================================
# Installation Steps
# ============================================================================

function Install-Uv {
    Write-Step "Checking uv..."
    
    if (Test-Command "uv") {
        Write-Success "uv is already installed"
        return $true
    }
    
    Write-Step "Installing uv..."
    
    try {
        # Install uv
        irm https://astral.sh/uv/install.ps1 | iex
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        if (Test-Command "uv") {
            Write-Success "uv installed successfully"
            return $true
        } else {
            Write-Error "Failed to install uv"
            return $false
        }
    } catch {
        Write-Error "Failed to install uv: $_"
        return $false
    }
}

function Install-Python {
    Write-Step "Checking Python..."
    
    # Check if Python is available
    if (Test-Command "python") {
        $version = python --version 2>&1
        if ($version -match "3\.1[1-9]") {
            Write-Success "Python $version is available"
            return $true
        }
    }
    
    # Try to install Python via uv
    Write-Step "Installing Python $PythonVersion via uv..."
    
    try {
        uv python install $PythonVersion
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python $PythonVersion installed"
            return $true
        } else {
            Write-Error "Failed to install Python"
            return $false
        }
    } catch {
        Write-Error "Failed to install Python: $_"
        return $false
    }
}

function Clone-Repository {
    Write-Step "Cloning SuperOutfit repository..."
    
    # Remove existing installation if present
    if (Test-Path $InstallDir) {
        Write-Warning "Existing installation found at $InstallDir"
        Write-Host "  Removing old installation..."
        
        try {
            Remove-Item -Recurse -Force $InstallDir
        } catch {
            Write-Error "Failed to remove old installation: $_"
            return $false
        }
    }
    
    # Clone repository
    try {
        git clone --depth 1 "$RepoUrl" "$InstallDir" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Repository cloned to $InstallDir"
            return $true
        } else {
            Write-Error "Failed to clone repository"
            return $false
        }
    } catch {
        Write-Error "Failed to clone repository: $_"
        return $false
    }
}

function Setup-Venv {
    Write-Step "Setting up virtual environment..."
    
    try {
        Push-Location $InstallDir
        
        # Create virtual environment
        uv venv 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Virtual environment created"
            Pop-Location
            return $true
        } else {
            Write-Error "Failed to create virtual environment"
            Pop-Location
            return $false
        }
    } catch {
        Write-Error "Failed to create virtual environment: $_"
        Pop-Location
        return $false
    }
}

function Install-Dependencies {
    Write-Step "Installing dependencies..."
    
    try {
        Push-Location $InstallDir
        
        # Install package in editable mode
        uv pip install -e . 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependencies installed"
            Pop-Location
            return $true
        } else {
            Write-Error "Failed to install dependencies"
            Pop-Location
            return $false
        }
    } catch {
        Write-Error "Failed to install dependencies: $_"
        Pop-Location
        return $false
    }
}

function Initialize-Data {
    Write-Step "Initializing data..."
    
    try {
        Push-Location $InstallDir
        
        # Run init command
        $superoutfitExe = ".\.venv\Scripts\superoutfit.exe"
        if (Test-Path $superoutfitExe) {
            & $superoutfitExe init --quick 2>&1 | Out-Null
            Write-Success "Data initialized"
        } else {
            Write-Warning "superoutfit.exe not found, skipping initialization"
        }
        
        Pop-Location
        return $true
    } catch {
        Write-Warning "Data initialization skipped: $_"
        Pop-Location
        return $true
    }
}

function Add-ToPath {
    Write-Step "Adding to PATH..."
    
    # Get the Scripts directory
    $scriptsDir = "$InstallDir\.venv\Scripts"
    
    # Check if already in PATH
    $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -like "*$scriptsDir*") {
        Write-Success "Already in PATH"
        return $true
    }
    
    try {
        # Add to user PATH
        $newPath = "$currentPath;$scriptsDir"
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        
        # Refresh current session PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-Success "Added to PATH"
        return $true
    } catch {
        Write-Warning "Failed to add to PATH: $_"
        Write-Host "  Please manually add to PATH: $scriptsDir"
        return $true
    }
}

function Print-Summary {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  SuperOutfit installed successfully!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Installation directory: $InstallDir"
    Write-Host ""
    Write-Host "  Quick start:"
    Write-Host "    1. Open a NEW terminal (important!)"
    Write-Host "    2. Run: superoutfit --help"
    Write-Host "    3. Run: superoutfit init"
    Write-Host "    4. Run: superoutfit gateway"
    Write-Host ""
    Write-Host "  Or use interactive mode:"
    Write-Host "    superoutfit tui"
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
}

# ============================================================================
# Main Installation
# ============================================================================

function Main {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  SuperOutfit Installer" -ForegroundColor Cyan
    Write-Host "  AI Fashion Advisor" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check prerequisites
    Write-Step "Checking prerequisites..."
    
    if (-not (Test-Command "git")) {
        Write-Error "Git is required but not installed."
        Write-Host "  Please install Git from: https://git-scm.com/"
        Write-Host ""
        Write-Host "Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    Write-Success "Git is available"
    
    # Install uv
    if (-not (Install-Uv)) {
        Write-Host ""
        Write-Host "Installation failed. Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    # Install Python
    if (-not (Install-Python)) {
        Write-Host ""
        Write-Host "Installation failed. Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    # Clone repository
    if (-not (Clone-Repository)) {
        Write-Host ""
        Write-Host "Installation failed. Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    # Setup virtual environment
    if (-not (Setup-Venv)) {
        Write-Host ""
        Write-Host "Installation failed. Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    # Install dependencies
    if (-not (Install-Dependencies)) {
        Write-Host ""
        Write-Host "Installation failed. Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    # Initialize data
    Initialize-Data
    
    # Add to PATH
    Add-ToPath
    
    # Print summary
    Print-Summary
    
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Run installation
Main
