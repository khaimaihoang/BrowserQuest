<#
    run_pi.ps1
    ----------
    Launch Pi (pi-coding-agent) through the Headroom optimization proxy with the
    codebase-memory MCP server registered.

    Modelled on run_agy.ps1:

      1. Ensure ripgrep (BurntSushi, MSVC build) and fd (sharkdp) are installed,
         auto-installing them with winget -> scoop -> choco when missing. This is
         what stops Pi from trying (and failing) to download them at startup.
      2. Start the Headroom proxy on port 8787 (skipped when it is already up).
      3. Point Pi's LLM traffic at Headroom and route general HTTP through it,
         bypassing the proxy for localhost like run_agy.ps1 does.
      4. Make sure codebase-memory-mcp is registered in Pi's MCP config.
      5. Run Pi, forwarding every argument you pass to this script.

    Usage
    -----
      powershell -ExecutionPolicy Bypass -File .\run_pi.ps1
      powershell -ExecutionPolicy Bypass -File .\run_pi.ps1 --model deepseek/deepseek-v4-pro

    Environment overrides
    ---------------------
      HEADROOM_PORT   Port for the Headroom proxy (default 8787)
      SKIP_HEADROOM=1 Skip starting/using the Headroom proxy
      SKIP_INSTALL=1  Skip the tool presence/installation step
#>

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
$HeadroomPort   = if ($env:HEADROOM_PORT) { [int]$env:HEADROOM_PORT } else { 8787 }
$HeadroomUrl    = "http://localhost:$HeadroomPort"
$SkipHeadroom   = $env:SKIP_HEADROOM -match '^(1|true|yes)$'
$SkipInstall    = $env:SKIP_INSTALL  -match '^(1|true|yes)$'

$AgentDir       = if ($env:PI_CODING_AGENT_DIR) { $env:PI_CODING_AGENT_DIR } else { Join-Path $HOME ".pi\agent" }
$PiBinDir       = Join-Path $AgentDir "bin"

function Write-Step($msg) { Write-Host "[run_pi] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   [ok] $msg" -ForegroundColor Green }
function Write-Warn2($msg){ Write-Host "   [!!] $msg" -ForegroundColor Yellow }

# Re-read PATH from the registry so binaries installed during this session are
# visible to the current process (and to the Pi child process we spawn).
function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ";"
}

# A tool counts as available if it is on PATH or already sits in Pi's bin dir
# (where Pi itself would download it).
function Test-ToolFile {
    param([string]$Command, [string]$ExeName)
    if (Get-Command $Command -ErrorAction SilentlyContinue) { return $true }
    if (Test-Path (Join-Path $PiBinDir $ExeName)) { return $true }
    return $false
}

# ===========================================================================
# 1. Ensure ripgrep + fd are present
# ===========================================================================
function Ensure-Tool {
    param(
        [Parameter(Mandatory)][string]$Command,
        [Parameter(Mandatory)][string]$ExeName,
        [Parameter(Mandatory)][string]$FriendlyName,
        [Parameter(Mandatory)][string]$WingetId,
        [Parameter(Mandatory)][string]$ScoopId,
        [Parameter(Mandatory)][string]$ChocoId
    )

    if (Test-ToolFile -Command $Command -ExeName $ExeName) {
        Write-Ok "$FriendlyName already available."
        return $true
    }

    Write-Step "$FriendlyName is missing - installing..."

    $installed = $false

    if (Get-Command winget -ErrorAction SilentlyContinue) {
        try {
            winget install --id $WingetId --exact --silent `
                --accept-package-agreements --accept-source-agreements `
                --disable-interactivity | Out-Host
            Update-SessionPath
        } catch { }
        if (Test-ToolFile -Command $Command -ExeName $ExeName) { $installed = $true }
    }

    if (-not $installed -and (Get-Command scoop -ErrorAction SilentlyContinue)) {
        try {
            scoop install $ScoopId | Out-Host
            Update-SessionPath
        } catch { }
        if (Test-ToolFile -Command $Command -ExeName $ExeName) { $installed = $true }
    }

    if (-not $installed -and (Get-Command choco -ErrorAction SilentlyContinue)) {
        try {
            choco install $ChocoId -y --no-progress | Out-Host
            Update-SessionPath
        } catch { }
        if (Test-ToolFile -Command $Command -ExeName $ExeName) { $installed = $true }
    }

    if ($installed) {
        Write-Ok "$FriendlyName installed."
    } else {
        Write-Warn2 "Could not install $FriendlyName automatically. Install it manually so Pi stops trying to download it."
    }
    return $installed
}

if (-not $SkipInstall) {
    Write-Step "Checking for ripgrep (MSVC) and fd (sharkdp)..."
    [void](Ensure-Tool -Command "rg" -ExeName "rg.exe" -FriendlyName "ripgrep (MSVC)" `
        -WingetId "BurntSushi.ripgrep.MSVC" -ScoopId "ripgrep" -ChocoId "ripgrep")
    [void](Ensure-Tool -Command "fd" -ExeName "fd.exe" -FriendlyName "fd (sharkdp)" `
        -WingetId "sharkdp.fd" -ScoopId "fd" -ChocoId "fd")
} else {
    Write-Step "SKIP_INSTALL set - not checking for ripgrep/fd."
}

# ===========================================================================
# 2. Start the Headroom proxy
# ===========================================================================
function Test-PortOpen {
    param([int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("127.0.0.1", $Port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

if (-not $SkipHeadroom) {
    if (Test-PortOpen -Port $HeadroomPort) {
        Write-Ok "Headroom proxy already listening on $HeadroomUrl."
    } else {
        Write-Step "Starting Headroom proxy on port $HeadroomPort..."
        $headroom = (Get-Command headroom -ErrorAction SilentlyContinue).Source
        if (-not $headroom) {
            Write-Warn2 "headroom was not found on PATH. Continuing without the proxy."
            $SkipHeadroom = $true
        } else {
            Start-Process -FilePath $headroom -ArgumentList "proxy", "--port", "$HeadroomPort" -WindowStyle Hidden
            $ready = $false
            for ($i = 0; $i -lt 40; $i++) {
                Start-Sleep -Milliseconds 500
                if (Test-PortOpen -Port $HeadroomPort) { $ready = $true; break }
            }
            if ($ready) { Write-Ok "Headroom proxy is up on $HeadroomUrl." }
            else { Write-Warn2 "Headroom proxy did not become ready in time. Continuing without it."; $SkipHeadroom = $true }
        }
    }
} else {
    Write-Step "SKIP_HEADROOM set - not starting the proxy."
}

# ===========================================================================
# 3. Route traffic through Headroom (mirrors run_agy.ps1)
# ===========================================================================
if (-not $SkipHeadroom) {
    Write-Step "Routing Pi through Headroom..."

    # LLM API base URLs (Pi honours these to override provider endpoints).
    $env:OPENAI_BASE_URL    = "$HeadroomUrl/v1"
    $env:ANTHROPIC_BASE_URL = "$HeadroomUrl"

    # General outbound HTTP goes through Headroom as well.
    $env:HTTP_PROXY  = $HeadroomUrl
    $env:HTTPS_PROXY = $HeadroomUrl

    # Never proxy the local proxy itself, and keep Pi's own update/registry
    # traffic direct so tooling still works.
    $env:NO_PROXY = "localhost,127.0.0.1,::1,pi.dev,registry.npmjs.org"
    $env:no_proxy = $env:NO_PROXY
} else {
    Write-Step "Headroom routing disabled - using direct connections."
}

# Prefer the OS certificate store so corporate/root CAs validate correctly.
# This is the fix for the "unable to verify the first certificate" warning.
if ($env:NODE_OPTIONS -notmatch '--use-system-ca') {
    $env:NODE_OPTIONS = ("$env:NODE_OPTIONS --use-system-ca").Trim()
    Write-Ok "NODE_OPTIONS now includes --use-system-ca."
}

# ===========================================================================
# 4. Ensure the codebase-memory MCP server is registered for Pi
# ===========================================================================
function Resolve-CodebaseMemoryExe {
    $cmd = Get-Command codebase-memory-mcp -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        (Join-Path $HOME ".local\bin\codebase-memory-mcp.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\codebase-memory-mcp\codebase-memory-mcp.exe")
    )
    return ($candidates | Where-Object { Test-Path $_ } | Select-Object -First 1)
}

function Ensure-CodebaseMemoryMcp {
    $configPath = Join-Path $AgentDir "mcp.json"
    $exe = Resolve-CodebaseMemoryExe
    if (-not $exe) {
        Write-Warn2 "codebase-memory-mcp was not found - skipping MCP registration."
        return
    }
    $exeJson = $exe -replace '\\', '/'

    $config = $null
    if (Test-Path $configPath) {
        try {
            $config = Get-Content -Path $configPath -Raw | ConvertFrom-Json
        } catch {
            Write-Warn2 "Could not parse $configPath - leaving it untouched."
            return
        }
    }
    if (-not $config) { $config = [pscustomobject]@{ mcpServers = [pscustomobject]@{} } }

    if (-not $config.PSObject.Properties["mcpServers"]) {
        $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([pscustomobject]@{}) -Force
    }
    $servers = $config.mcpServers

    if ($servers.PSObject.Properties["codebase-memory-mcp"]) {
        Write-Ok "codebase-memory-mcp already registered in $configPath."
        return
    }

    $entry = [pscustomobject]@{ command = $exeJson; args = @() }
    $servers | Add-Member -MemberType NoteProperty -Name "codebase-memory-mcp" -Value $entry -Force

    $json = $config | ConvertTo-Json -Depth 100
    # Write UTF-8 without a BOM so Node's JSON.parse accepts the file.
    [System.IO.File]::WriteAllText($configPath, $json)
    Write-Ok "Registered codebase-memory-mcp in $configPath."
}

Write-Step "Ensuring codebase-memory MCP is configured..."
Ensure-CodebaseMemoryMcp

# ===========================================================================
# 5. Run Pi
# ===========================================================================
if (-not (Get-Command pi -ErrorAction SilentlyContinue)) {
    Write-Warn2 "'pi' was not found on PATH. Install it with: npm install -g @earendil-works/pi-coding-agent"
    exit 1
}

Write-Step "Launching Pi..."
& pi @args
exit $LASTEXITCODE
