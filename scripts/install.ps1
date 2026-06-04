# ============================================================================
# SuperOutfit Installer for Windows
# ============================================================================
# Installation script for Windows (PowerShell).
# Uses uv for fast Python provisioning and package management.
#
# Usage:
#   iex (irm https://raw.githubusercontent.com/egg-rolls/SuperOutfit/main/scripts/install.ps1)
#
# Or download and run:
#   .\install.ps1
#
# ============================================================================

param(
    [switch]$SkipSetup,
    [string]$Branch = "main",
    [string]$InstallDir = "$env:LOCALAPPDATA\SuperOutfit",
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

# Suppress progress bar for faster downloads
$ProgressPreference = "SilentlyContinue"

# Force UTF-8 output
try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
} catch {
    # Some constrained hosts disallow encoding mutation
}

# ============================================================================
# Configuration
# ============================================================================

$RepoUrl = "https://github.com/egg-rolls/SuperOutfit.git"
$PythonVersion = "3.11"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n=> $Message" -ForegroundColor Cyan
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
        return
    }
    
    Write-Step "Installing uv..."
    
    # Install uv
    irm https://astral.sh/uv/install.ps1 | iex
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    if (Test-Command "uv") {
        Write-Success "uv installed successfully"
    } else {
        Write-Error "Failed to install uv"
        exit 1
    }
}

function Install-Python {
    Write-Step "Checking Python..."
    
    # Check if Python is available
    if (Test-Command "python") {
        $version = python --version 2>&1
        if ($version -match "3\.1[1-9]") {
            Write-Success "Python $version is available"
            return
        }
    }
    
    # Try to install Python via uv
    Write-Step "Installing Python $PythonVersion via uv..."
    uv python install $PythonVersion
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python $PythonVersion installed"
    } else {
        Write-Error "Failed to install Python"
        exit 1
    }
}

function Clone-Repository {
    Write-Step "Cloning SuperOutfit repository..."
    
    # Remove existing installation if present
    if (Test-Path $InstallDir) {
        Write-Warning "Existing installation found at $InstallDir"
        if (-not $NonInteractive) {
            $response = Read-Host "Remove and reinstall? (y/N)"
            if ($response -ne "y" -and $response -ne "Y") {
                Write-Host "Installation cancelled."
                exit 0
            }
        }
        Remove-Item -Recurse -Force $InstallDir
    }
    
    # Clone repository
    git clone --depth 1 -b $Branch $RepoUrl $InstallDir
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Repository cloned to $InstallDir"
    } else {
        Write-Error "Failed to clone repository"
        exit 1
    }
}

function Setup-Venv {
    Write-Step "Setting up virtual environment..."
    
    Push-Location $InstallDir
    
    # Create virtual environment
    uv venv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment created"
    } else {
        Write-Error "Failed to create virtual environment"
        Pop-Location
        exit 1
    }
    
    Pop-Location
}

function Install-Dependencies {
    Write-Step "Installing dependencies..."
    
    Push-Location $InstallDir
    
    # Install package in editable mode
    uv pip install -e .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
    } else {
        Write-Error "Failed to install dependencies"
        Pop-Location
        exit 1
    }
    
    Pop-Location
}

function Initialize-Data {
    Write-Step "Initializing data..."
    
    Push-Location $InstallDir
    
    # Run init command
    & ".\.venv\Scripts\superoutfit.exe" init --quick
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Data initialized"
    } else {
        Write-Warning "Data initialization skipped (may already exist)"
    }
    
    Pop-Location
}

function Add-ToPath {
    Write-Step "Adding to PATH..."
    
    # Get the Scripts directory
    $scriptsDir = "$InstallDir\.venv\Scripts"
    
    # Check if already in PATH
    $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -contains $scriptsDir) {
        Write-Success "Already in PATH"
        return
    }
    
    # Add to user PATH
    $newPath = "$currentPath;$scriptsDir"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    # Refresh current session PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Success "Added to PATH"
}

function Create-Shortcut {
    Write-Step "Creating desktop shortcut..."
    
    $shortcutPath = "$env:USERPROFILE\Desktop\SuperOutfit.lnk"
    $targetPath = "$InstallDir\.venv\Scripts\superoutfit.exe"
    
    # Check if shortcut already exists
    if (Test-Path $shortcutPath) {
        Write-Success "Desktop shortcut already exists"
        return
    }
    
    # Create shortcut
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "cmd.exe"
    $shortcut.Arguments = "/k cd /d $InstallDir && .venv\Scripts\activate"
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.Description = "SuperOutfit - AI Fashion Advisor"
    $shortcut.Save()
    
    Write-Success "Desktop shortcut created"
}

function Print-Summary {
    Write-Host "`n" -NoNewline
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  SuperOutfit installed successfully!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Installation directory: $InstallDir"
    Write-Host ""
    Write-Host "  Quick start:"
    Write-Host "    1. Open a new terminal"
    Write-Host "    2. Run: superoutfit --help"
    Write-Host "    3. Run: superoutfit init"
    Write-Host "    4. Run: superoutfit gateway"
    Write-Host ""
    Write-Host "  Or use the desktop shortcut."
    Write-Host ""
    Write-Host "  Documentation:"
    Write-Host "    - README.md"
    Write-Host "    - docs/INSTALL.md"
    Write-Host "    - docs/CLI.md"
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
}

# ============================================================================
# Main Installation
# ============================================================================

function Main {
    Write-Host "`n" -NoNewline
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
        exit 1
    }
    Write-Success "Git is available"
    
    # Install uv
    Install-Uv
    
    # Install Python
    Install-Python
    
    # Clone repository
    Clone-Repository
    
    # Setup virtual environment
    Setup-Venv
    
    # Install dependencies
    Install-Dependencies
    
    # Initialize data
    if (-not $SkipSetup) {
        Initialize-Data
    }
    
    # Add to PATH
    Add-ToPath
    
    # Create shortcut
    Create-Shortcut
    
    # Print summary
    Print-Summary
}

# Run installation
Main
