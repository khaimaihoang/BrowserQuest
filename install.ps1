$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$env:PATH = "$ScriptDir\node_env\node-v20.17.0-win-x64;" + $env:PATH
Write-Host "Installing dependencies using Node.js v20.17.0..." -ForegroundColor Cyan
npm install
Write-Host "Done installing!" -ForegroundColor Green
pause
