#!/bin/bash
# Camel TUI Unix Installer
# Run: curl -sSL https://raw.githubusercontent.com/quivent/camel/main/install.sh | bash

set -e

echo "Installing Camel TUI..."

INSTALL_DIR="$HOME/.camel"

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "Cloning Camel..."
    git clone https://github.com/quivent/camel.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Add to PATH via shell config
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "alias camel=" "$SHELL_RC"; then
        echo 'alias camel="python3 ~/.camel/src/main.py"' >> "$SHELL_RC"
        echo "Added 'camel' alias to $SHELL_RC"
    fi
fi

echo ""
echo "Camel TUI installed successfully!"
echo "Run: source $SHELL_RC && camel"
echo ""
echo "Requirements:"
echo "  - Python 3.10+"
echo "  - Ollama server running (localhost:11434)"
echo "  - xclip for clipboard support (apt install xclip)"
