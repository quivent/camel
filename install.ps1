# Camel TUI Windows Installer
# Run: iwr -useb https://raw.githubusercontent.com/quivent/camel/main/install.ps1 | iex

Write-Host "Installing Camel TUI..." -ForegroundColor Cyan

# Clone to user's home directory
$installDir = "$env:USERPROFILE\.camel"

if (Test-Path $installDir) {
    Write-Host "Updating existing installation..." -ForegroundColor Yellow
    Push-Location $installDir
    git pull
    Pop-Location
} else {
    Write-Host "Cloning Camel..." -ForegroundColor Green
    git clone https://github.com/quivent/camel.git $installDir
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Green
Push-Location $installDir
pip install -r requirements.txt
Pop-Location

# Create camel.bat in PATH
$batPath = "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\camel.bat"
@"
@echo off
python "$env:USERPROFILE\.camel\src\main.py" %*
"@ | Out-File -FilePath $batPath -Encoding ASCII

Write-Host ""
Write-Host "Camel TUI installed successfully!" -ForegroundColor Green
Write-Host "Run 'camel' from any terminal to start." -ForegroundColor Cyan
Write-Host ""
Write-Host "Requirements:" -ForegroundColor Yellow
Write-Host "  - Python 3.10+ (python --version)"
Write-Host "  - Ollama server running (localhost:11434)"
