$ErrorActionPreference = 'Stop'

$installDir = "$env:ChocolateyInstall\lib\camel-tui\tools\camel"
$shimPath = "$env:ChocolateyInstall\bin\camel.bat"

if (Test-Path $installDir) {
    Remove-Item -Recurse -Force $installDir
}

if (Test-Path $shimPath) {
    Remove-Item $shimPath
}

Write-Host "Camel TUI uninstalled." -ForegroundColor Yellow
