$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$env:PATH = "$ScriptDir\node_env\node-v20.17.0-win-x64;" + $env:PATH
Write-Host "Starting BrowserQuest Client..." -ForegroundColor Green
npm run watch:client
pause
