#!/bin/bash
# ============================================================================
# SuperOutfit Installer for macOS / Linux
# ============================================================================
# Installation script for macOS and Linux.
# Uses uv for fast Python provisioning and package management.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/egg-rolls/SuperOutfit/main/scripts/install.sh | bash
#
# Or download and run:
#   chmod +x install.sh
#   ./install.sh
#
# ============================================================================

set -e

# ============================================================================
# Configuration
# ============================================================================

REPO_URL="https://github.com/egg-rolls/SuperOutfit.git"
PYTHON_VERSION="3.11"
INSTALL_DIR="${SUPEROUTFIT_HOME:-$HOME/.superoutfit}"

# ============================================================================
# Helper Functions
# ============================================================================

print_step() {
    echo ""
    echo "=> $1"
}

print_success() {
    echo "   ✓ $1"
}

print_warning() {
    echo "   ⚠ $1"
}

print_error() {
    echo "   ✗ $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# Installation Steps
# ============================================================================

install_uv() {
    print_step "Checking uv..."
    
    if command_exists uv; then
        print_success "uv is already installed"
        return
    fi
    
    print_step "Installing uv..."
    
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the environment
    if [ -f "$HOME/.local/bin/env" ]; then
        . "$HOME/.local/bin/env"
    fi
    
    # Add to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
    
    if command_exists uv; then
        print_success "uv installed successfully"
    else
        print_error "Failed to install uv"
        exit 1
    fi
}

install_python() {
    print_step "Checking Python..."
    
    # Check if Python is available
    if command_exists python3; then
        version=$(python3 --version 2>&1)
        if echo "$version" | grep -q "3\.1[1-9]"; then
            print_success "Python $version is available"
            return
        fi
    fi
    
    # Try to install Python via uv
    print_step "Installing Python $PYTHON_VERSION via uv..."
    uv python install "$PYTHON_VERSION"
    
    if [ $? -eq 0 ]; then
        print_success "Python $PYTHON_VERSION installed"
    else
        print_error "Failed to install Python"
        exit 1
    fi
}

clone_repository() {
    print_step "Cloning SuperOutfit repository..."
    
    # Remove existing installation if present
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Existing installation found at $INSTALL_DIR"
        if [ -t 0 ]; then
            read -p "Remove and reinstall? (y/N) " response
            if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
                echo "Installation cancelled."
                exit 0
            fi
        fi
        rm -rf "$INSTALL_DIR"
    fi
    
    # Clone repository
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Repository cloned to $INSTALL_DIR"
    else
        print_error "Failed to clone repository"
        exit 1
    fi
}

setup_venv() {
    print_step "Setting up virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    uv venv
    
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
}

install_dependencies() {
    print_step "Installing dependencies..."
    
    cd "$INSTALL_DIR"
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install package in editable mode
    uv pip install -e .
    
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

initialize_data() {
    print_step "Initializing data..."
    
    cd "$INSTALL_DIR"
    
    # Run init command
    ./.venv/bin/superoutfit init --quick 2>/dev/null || true
    
    print_success "Data initialized"
}

add_to_path() {
    print_step "Adding to PATH..."
    
    # Get the bin directory
    bin_dir="$INSTALL_DIR/.venv/bin"
    
    # Check if already in PATH
    if echo "$PATH" | grep -q "$bin_dir"; then
        print_success "Already in PATH"
        return
    fi
    
    # Determine shell profile
    if [ -f "$HOME/.zshrc" ]; then
        profile="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        profile="$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        profile="$HOME/.bash_profile"
    elif [ -f "$HOME/.profile" ]; then
        profile="$HOME/.profile"
    else
        profile="$HOME/.profile"
    fi
    
    # Add to PATH
    echo "" >> "$profile"
    echo "# SuperOutfit" >> "$profile"
    echo "export PATH=\"$bin_dir:\$PATH\"" >> "$profile"
    
    # Export for current session
    export PATH="$bin_dir:$PATH"
    
    print_success "Added to PATH ($profile)"
}

create_desktop_entry() {
    # Only for Linux with desktop environment
    if [ "$(uname)" != "Linux" ]; then
        return
    fi
    
    if [ -z "$XDG_DATA_HOME" ]; then
        XDG_DATA_HOME="$HOME/.local/share"
    fi
    
    desktop_dir="$XDG_DATA_HOME/applications"
    mkdir -p "$desktop_dir"
    
    cat > "$desktop_dir/superoutfit.desktop" << EOF
[Desktop Entry]
Name=SuperOutfit
Comment=AI Fashion Advisor
Exec=x-terminal-emulator -e "$INSTALL_DIR/.venv/bin/superoutfit tui"
Icon=$INSTALL_DIR/assets/icon.png
Terminal=true
Type=Application
Categories=Utility;
EOF
    
    print_success "Desktop entry created"
}

print_summary() {
    echo ""
    echo "============================================================"
    echo "  SuperOutfit installed successfully!"
    echo "============================================================"
    echo ""
    echo "  Installation directory: $INSTALL_DIR"
    echo ""
    echo "  Quick start:"
    echo "    1. Open a new terminal"
    echo "    2. Run: superoutfit --help"
    echo "    3. Run: superoutfit init"
    echo "    4. Run: superoutfit gateway"
    echo ""
    echo "  Note: You may need to restart your terminal or run:"
    echo "    source ~/.bashrc  # or ~/.zshrc"
    echo ""
    echo "  Documentation:"
    echo "    - README.md"
    echo "    - docs/INSTALL.md"
    echo "    - docs/CLI.md"
    echo ""
    echo "============================================================"
}

# ============================================================================
# Main Installation
# ============================================================================

main() {
    echo ""
    echo "============================================================"
    echo "  SuperOutfit Installer"
    echo "  AI Fashion Advisor"
    echo "============================================================"
    echo ""
    
    # Check prerequisites
    print_step "Checking prerequisites..."
    
    if ! command_exists git; then
        print_error "Git is required but not installed."
        echo "  Please install Git first:"
        echo "    macOS: xcode-select --install"
        echo "    Ubuntu/Debian: sudo apt install git"
        echo "    Fedora: sudo dnf install git"
        exit 1
    fi
    print_success "Git is available"
    
    # Install uv
    install_uv
    
    # Install Python
    install_python
    
    # Clone repository
    clone_repository
    
    # Setup virtual environment
    setup_venv
    
    # Install dependencies
    install_dependencies
    
    # Initialize data
    initialize_data
    
    # Add to PATH
    add_to_path
    
    # Create desktop entry (Linux only)
    create_desktop_entry
    
    # Print summary
    print_summary
}

# Run installation
main
