$ErrorActionPreference = 'Stop'

$installDir = "$env:ChocolateyInstall\lib\camel-tui\tools\camel"

# Clone repository
git clone https://github.com/quivent/camel.git $installDir

# Install Python dependencies
Push-Location $installDir
pip install -r requirements.txt
Pop-Location

# Create shim
$shimPath = "$env:ChocolateyInstall\bin\camel.bat"
@"
@echo off
python "$installDir\src\main.py" %*
"@ | Out-File -FilePath $shimPath -Encoding ASCII

Write-Host "Camel TUI installed! Run 'camel' to start." -ForegroundColor Green
