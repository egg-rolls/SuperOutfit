# ============================================================================
# SuperOutfit Installer for Windows
# ============================================================================
# 
# Usage:
#   irm https://raw.githubusercontent.com/egg-rolls/SuperOutfit/master/scripts/install-simple.ps1 | iex
#
# ============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# UTF-8 output for correct display of Unicode characters
try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
} catch {}

# ============================================================================
# Configuration
# ============================================================================

$RepoUrl = "https://github.com/egg-rolls/SuperOutfit.git"
$InstallDir = "$env:LOCALAPPDATA\SuperOutfit"
$PythonVersion = "3.11"

# ============================================================================
# Helper functions
# ============================================================================

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=> $Message..." -ForegroundColor White
}

# ============================================================================
# Stage 1: Check Git
# ============================================================================

function Install-Git {
    Write-Step "Checking Git"
    
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $gitVersion = git --version 2>&1
        Write-Success "Git is available ($gitVersion)"
        return $true
    }
    
    Write-Err "Git is required"
    Write-Host "     Please install from https://git-scm.com/" -ForegroundColor Yellow
    return $false
}

# ============================================================================
# Stage 2: Check/Install uv
# ============================================================================

function Install-Uv {
    Write-Step "Checking uv"
    
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $uvVersion = uv --version 2>&1
        Write-Success "uv is already installed ($uvVersion)"
        return $true
    }
    
    Write-Info "Installing uv..."
    try {
        irm https://astral.sh/uv/install.ps1 | iex
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Success "uv installed"
        return $true
    } catch {
        Write-Err "Failed to install uv: $_"
        return $false
    }
}

# ============================================================================
# Stage 3: Check/Install Python
# ============================================================================

function Install-Python {
    Write-Step "Checking Python"
    
    # Check if Python 3.11+ is available
    $pythonCmd = $null
    foreach ($cmd in @("python", "python3")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            $ver = & $cmd --version 2>&1
            if ($ver -match "3\.(\d+)") {
                $minor = [int]$Matches[1]
                if ($minor -ge 11) {
                    $pythonCmd = $cmd
                    Write-Success "Python $ver"
                    break
                }
            }
        }
    }
    
    if ($pythonCmd) {
        return $true
    }
    
    # Install Python via uv
    Write-Info "Installing Python $PythonVersion..."
    try {
        uv python install $PythonVersion
        Write-Success "Python $PythonVersion installed"
        return $true
    } catch {
        Write-Err "Failed to install Python: $_"
        return $false
    }
}

# ============================================================================
# Stage 4: Clone or update repository
# ============================================================================

function Stop-SuperOutfitProcesses {
    # Stop any running SuperOutfit processes to release file locks
    $processes = @("superoutfit", "python")
    $stopped = $false
    
    foreach ($procName in $processes) {
        $procs = Get-Process -Name $procName -ErrorAction SilentlyContinue | Where-Object {
            $_.Path -like "*SuperOutfit*"
        }
        foreach ($proc in $procs) {
            try {
                Write-Info "Stopping process: $($proc.ProcessName) (PID: $($proc.Id))"
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $stopped = $true
            } catch {}
        }
    }
    
    if ($stopped) {
        Start-Sleep -Seconds 2  # Wait for processes to fully exit
    }
    
    return $stopped
}

function Install-Repository {
    Write-Step "Checking repository"
    
    $didUpdate = $false
    
    if (Test-Path $InstallDir) {
        # Stop running processes first
        Stop-SuperOutfitProcesses | Out-Null
        
        # Validate existing repo
        $repoValid = $false
        if (Test-Path "$InstallDir\.git") {
            Push-Location $InstallDir
            try {
                $global:LASTEXITCODE = 0
                $revParseOut = & git rev-parse --is-inside-work-tree 2>&1
                $revParseOk = ($LASTEXITCODE -eq 0) -and ($revParseOut -match "true")
                
                $global:LASTEXITCODE = 0
                $null = & git status --short 2>&1
                $statusOk = ($LASTEXITCODE -eq 0)
                
                if ($revParseOk -and $statusOk) {
                    $repoValid = $true
                }
            } catch {}
            Pop-Location
        }
        
        if ($repoValid) {
            Write-Info "Existing installation found, updating..."
            Push-Location $InstallDir
            
            $prevEAP = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            try {
                & git fetch origin master 2>&1 | Out-Null
                & git reset --hard origin/master 2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Repository updated"
                    $didUpdate = $true
                } else {
                    Write-Warn "Update failed, will reclone"
                }
            } finally {
                $ErrorActionPreference = $prevEAP
            }
            Pop-Location
        }
        
        if (-not $didUpdate) {
            # Remove broken installation
            Write-Info "Removing old installation..."
            Push-Location $env:USERPROFILE  # Step out of InstallDir
            try {
                Remove-Item -Recurse -Force $InstallDir -ErrorAction Stop
                Write-Success "Old installation removed"
            } catch {
                Write-Warn "Could not fully remove old installation: $_"
                # Try to continue anyway
            }
            Pop-Location
        }
    }
    
    if (-not $didUpdate) {
        # Fresh clone
        Write-Info "Cloning repository..."
        
        # Ensure parent directory exists
        $parentDir = Split-Path $InstallDir
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
        }
        
        $cloneSuccess = $false
        
        # Try HTTPS clone
        try {
            & git clone --depth 1 $RepoUrl $InstallDir 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $cloneSuccess = $true
                Write-Success "Repository cloned"
            }
        } catch {}
        
        # Fallback: ZIP download
        if (-not $cloneSuccess) {
            Write-Warn "Git clone failed, trying ZIP download..."
            try {
                $zipUrl = "https://github.com/egg-rolls/SuperOutfit/archive/refs/heads/master.zip"
                $zipPath = "$env:TEMP\superoutfit.zip"
                $extractPath = "$env:TEMP\superoutfit_extract"
                
                # Download ZIP
                Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
                
                # Extract
                if (Test-Path $extractPath) { Remove-Item -Recurse -Force $extractPath }
                Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
                
                # Move to install dir
                $extractedDir = Get-ChildItem $extractPath -Directory | Select-Object -First 1
                if ($extractedDir) {
                    Move-Item $extractedDir.FullName $InstallDir -Force
                    Write-Success "Downloaded and extracted"
                    
                    # Initialize git repo for future updates
                    Push-Location $InstallDir
                    & git init 2>$null
                    & git remote add origin $RepoUrl 2>$null
                    Pop-Location
                    
                    $cloneSuccess = $true
                }
                
                # Cleanup
                Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
                Remove-Item -Recurse -Force $extractPath -ErrorAction SilentlyContinue
            } catch {
                Write-Err "ZIP download also failed: $_"
            }
        }
        
        if (-not $cloneSuccess) {
            Write-Err "Failed to download repository"
            return $false
        }
    }
    
    # Configure git
    Push-Location $InstallDir
    & git config core.autocrlf false 2>$null
    Pop-Location
    
    return $true
}

# ============================================================================
# Stage 5: Create virtual environment
# ============================================================================

function Install-Venv {
    Write-Step "Creating virtual environment"
    
    Push-Location $InstallDir
    
    $venvValid = $false
    if (Test-Path ".venv") {
        # Check if venv is valid
        if (Test-Path ".venv\pyvenv.cfg") {
            $venvValid = $true
            Write-Info "Virtual environment already exists"
        } else {
            Write-Warn "Virtual environment is corrupted (missing pyvenv.cfg)"
            Write-Info "Removing and recreating..."
            Remove-Item -Recurse -Force ".venv" -ErrorAction SilentlyContinue
        }
    }
    
    if (-not $venvValid) {
        try {
            & uv venv .venv --python $PythonVersion 2>&1 | Out-Null
            Write-Success "Virtual environment created"
        } catch {
            Write-Err "Failed to create virtual environment: $_"
            Pop-Location
            return $false
        }
    }
    
    Pop-Location
    return $true
}

# ============================================================================
# Stage 6: Install dependencies
# ============================================================================

function Install-Dependencies {
    Write-Step "Installing dependencies"
    
    Push-Location $InstallDir
    
    try {
        & uv pip install -e . 2>&1 | Out-Null
        Write-Success "Dependencies installed"
    } catch {
        Write-Err "Failed to install dependencies: $_"
        Pop-Location
        return $false
    }
    
    Pop-Location
    return $true
}

# ============================================================================
# Stage 7: Initialize data
# ============================================================================

function Initialize-Data {
    Write-Step "Initializing data"
    
    Push-Location $InstallDir
    
    try {
        & ".\.venv\Scripts\superoutfit.exe" init --quick 2>&1 | Out-Null
        Write-Success "Data initialized"
    } catch {
        Write-Warn "Data initialization skipped (may already exist)"
    }
    
    Pop-Location
    return $true
}

# ============================================================================
# Stage 8: Add to PATH
# ============================================================================

function Add-ToPath {
    Write-Step "Adding to PATH"
    
    $scriptsDir = "$InstallDir\.venv\Scripts"
    $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    if ($currentPath -notlike "*$scriptsDir*") {
        [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$scriptsDir", "User")
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Success "Added to PATH"
    } else {
        Write-Success "Already in PATH"
    }
    
    return $true
}

# ============================================================================
# Main installation
# ============================================================================

function Main {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  SuperOutfit Installer" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Run stages
    $stages = @(
        @{ Name = "Git";          Func = { Install-Git } },
        @{ Name = "uv";           Func = { Install-Uv } },
        @{ Name = "Python";       Func = { Install-Python } },
        @{ Name = "Repository";   Func = { Install-Repository } },
        @{ Name = "Venv";         Func = { Install-Venv } },
        @{ Name = "Dependencies"; Func = { Install-Dependencies } },
        @{ Name = "Data";         Func = { Initialize-Data } },
        @{ Name = "PATH";         Func = { Add-ToPath } }
    )
    
    foreach ($stage in $stages) {
        $result = & $stage.Func
        if (-not $result) {
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Red
            Write-Host "  Installation failed at stage: $($stage.Name)" -ForegroundColor Red
            Write-Host "============================================================" -ForegroundColor Red
            Write-Host ""
            Write-Host "Press Enter to exit..." -ForegroundColor Yellow
            Read-Host
            return
        }
    }
    
    # Success
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
    Write-Host "  Quick commands:" -ForegroundColor White
    Write-Host "    superoutfit tui          # Interactive menu" -ForegroundColor Gray
    Write-Host "    superoutfit gateway      # Start web service" -ForegroundColor Gray
    Write-Host "    superoutfit update       # Update to latest" -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Press Enter to exit..." -ForegroundColor Yellow
    Read-Host
}

# Run installation
Main
