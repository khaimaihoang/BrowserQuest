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
      3. Point Pi's LLM provider base URLs (OpenAI/Anthropic) at Headroom.
         Everything else (incl. DeepSeek, which uses its own baseUrl) connects
         directly - Headroom is not a general HTTP/CONNECT proxy.
      4. Register Pi's MCP servers: codebase-memory-mcp, unity-synaptic, and
         the bundled dsh-ltm long-term-memory bridge (tools/dsh-ltm-mcp).
      5. Load the dsh-ltm auto-recall extension and run Pi, forwarding every
         argument you pass to this script.

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
# 3. Route LLM traffic through Headroom
# ===========================================================================

# Headroom is an LLM optimization proxy ONLY (OpenAI-compatible at /v1 and
# Anthropic at /). It does NOT support generic CONNECT tunneling, so it must
# never be set as HTTP_PROXY/HTTPS_PROXY - that makes every HTTPS request
# (DeepSeek, npm, github, telemetry) fail with "Connection error" (404).
# Clear any stale proxy inherited from the parent shell so Pi connects direct.
Remove-Item Env:HTTP_PROXY  -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy  -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
Remove-Item Env:NO_PROXY    -ErrorAction SilentlyContinue
Remove-Item Env:no_proxy    -ErrorAction SilentlyContinue

if (-not $SkipHeadroom) {
    Write-Step "Routing LLM traffic through Headroom..."

    # Point only the LLM provider base URLs at Headroom. Providers with their
    # own baseUrl (e.g. DeepSeek -> https://api.deepseek.com) ignore these and
    # connect directly to the vendor.
    $env:OPENAI_BASE_URL    = "$HeadroomUrl/v1"
    $env:ANTHROPIC_BASE_URL = "$HeadroomUrl"
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
# 4. Ensure the MCP servers (codebase-memory-mcp, unity-synaptic, dsh-ltm) are
#    registered for Pi
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

function Resolve-UnitySynaptic {
    # unity-synaptic runs the Synaptic MCP index-supersave.js via Node.
    $node = (Get-Command node -ErrorAction SilentlyContinue).Source
    if (-not $node) { $node = "E:/Program Files/nodejs/node.exe" }
    if (-not (Test-Path $node)) { return $null }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Synaptic\MCPServer\index-supersave.js"),
        (Join-Path $env:LOCALAPPDATA "Synaptic\MCPServer\index.js")
    )
    $script = ($candidates | Where-Object { Test-Path $_ } | Select-Object -First 1)
    if (-not $script) { return $null }

    return [pscustomobject]@{ Command = $node; Args = @($script) }
}

function Resolve-DshLtmMcp {
    # The dsh-ltm long-term-memory bridge ships with this repo under tools/dsh-ltm-mcp.
    $candidates = @(
        (Join-Path $PSScriptRoot "tools\dsh-ltm-mcp\mcp-server.mjs"),
        (Join-Path $PSScriptRoot "dsh-ltm-mcp\mcp-server.mjs")
    )
    return ($candidates | Where-Object { Test-Path $_ } | Select-Object -First 1)
}

function Ensure-DshLtmDeps {
    param([Parameter(Mandatory)][string]$ServerDir)
    $engine = Join-Path $ServerDir "node_modules\@tr1v3r\dsh-ltm"
    if (Test-Path $engine) {
        Write-Ok "dsh-ltm engine already installed."
        return $true
    }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Warn2 "npm was not found - cannot install the dsh-ltm MCP dependencies."
        return $false
    }
    Write-Step "Installing dsh-ltm MCP dependencies (npm install)..."
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        Push-Location $ServerDir
        & npm install --no-audit --no-fund | Out-Host
    } finally {
        Pop-Location
        $ErrorActionPreference = $saved
    }
    if (Test-Path $engine) {
        Write-Ok "dsh-ltm MCP dependencies installed."
        return $true
    }
    Write-Warn2 "dsh-ltm MCP dependencies are still missing - skipping its registration."
    return $false
}

function Initialize-DshLtmSeeds {
    param(
        [Parameter(Mandatory)][string]$ServerDir,
        [Parameter(Mandatory)][string]$NodeExe
    )
    $seeder = Join-Path $ServerDir "seed-memories.mjs"
    $seeds  = Join-Path $ServerDir "seeds.json"
    if (-not (Test-Path $seeder) -or -not (Test-Path $seeds)) { return }

    # Applied once per machine; the seeder itself is idempotent (dedupe).
    $memoryDir = Join-Path $AgentDir "memory"
    $marker = Join-Path $memoryDir ".dsh-ltm-seeded"
    if (Test-Path $marker) {
        Write-Ok "dsh-ltm seed memories already applied."
        return
    }

    Write-Step "Seeding dsh-ltm memories..."
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $code = 1
    try {
        # Seed into the repository's own project scope.
        Push-Location $PSScriptRoot
        & $NodeExe $seeder | Out-Host
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
        $ErrorActionPreference = $saved
    }
    if ($code -eq 0) {
        New-Item -ItemType Directory -Force -Path $memoryDir | Out-Null
        Set-Content -Path $marker -Value (Get-Date -Format o)
        Write-Ok "dsh-ltm seed memories applied."
    } else {
        Write-Warn2 "dsh-ltm seeding exited with code $code - will retry next launch."
    }
}

function Ensure-McpServer {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Command,
        [Parameter()][object[]]$ArgList = @(),
        [Parameter()][hashtable]$Env = @{}
    )
    $configPath = Join-Path $AgentDir "mcp.json"

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

    if ($servers.PSObject.Properties[$Name]) {
        Write-Ok "$Name already registered in $configPath."
        return
    }

    $commandJson = $Command -replace '\\', '/'
    $argsJson    = @($ArgList | ForEach-Object { $_ -replace '\\', '/' })
    $entry = [pscustomobject]@{ command = $commandJson; args = $argsJson }
    if ($Env.Count -gt 0) {
        $envObj = [pscustomobject]@{}
        foreach ($key in $Env.Keys) {
            $envObj | Add-Member -MemberType NoteProperty -Name $key -Value (($Env[$key]) -replace '\\', '/')
        }
        $entry | Add-Member -MemberType NoteProperty -Name "env" -Value $envObj
    }
    $servers | Add-Member -MemberType NoteProperty -Name $Name -Value $entry -Force

    $json = $config | ConvertTo-Json -Depth 100
    # Write UTF-8 without a BOM so Node's JSON.parse accepts the file.
    [System.IO.File]::WriteAllText($configPath, $json)
    Write-Ok "Registered $Name in $configPath."
}

Write-Step "Ensuring MCP servers are configured..."

$codebaseExe = Resolve-CodebaseMemoryExe
if ($codebaseExe) {
    Ensure-McpServer -Name "codebase-memory-mcp" -Command $codebaseExe
} else {
    Write-Warn2 "codebase-memory-mcp was not found - skipping MCP registration."
}

$synaptic = Resolve-UnitySynaptic
if ($synaptic) {
    Ensure-McpServer -Name "unity-synaptic" -Command $synaptic.Command -ArgList $synaptic.Args
} else {
    Write-Warn2 "unity-synaptic (Synaptic MCP) was not found - skipping MCP registration."
}

$dshLtmServer = Resolve-DshLtmMcp
if ($dshLtmServer) {
    $serverDir = Split-Path -Parent $dshLtmServer
    if (Ensure-DshLtmDeps -ServerDir $serverDir) {
        $nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
        if (-not $nodeExe) { $nodeExe = "E:/Program Files/nodejs/node.exe" }
        # One memory DB shared by the MCP tools and the auto-recall extension.
        if (-not $env:DSH_LTM_DB) { $env:DSH_LTM_DB = Join-Path $AgentDir "memory\ltm.db" }
        Ensure-McpServer -Name "dsh-ltm" -Command $nodeExe -ArgList @($dshLtmServer) `
            -Env @{ DSH_LTM_DB = $env:DSH_LTM_DB }
        Initialize-DshLtmSeeds -ServerDir $serverDir -NodeExe $nodeExe
    }
} else {
    Write-Warn2 "dsh-ltm MCP bridge (tools/dsh-ltm-mcp) was not found - skipping its registration."
}

# ===========================================================================
# 5. Run Pi
# ===========================================================================
if (-not (Get-Command pi -ErrorAction SilentlyContinue)) {
    Write-Warn2 "'pi' was not found on PATH. Install it with: npm install -g @earendil-works/pi-coding-agent"
    exit 1
}

# Auto-recall: inject pinned/recent memories into the system prompt. Only the
# changed section is re-sent each turn (prefix-cache friendly).
$recallExt = Join-Path $PSScriptRoot "tools\dsh-ltm-mcp\dsh-ltm-recall.ts"
if (Test-Path $recallExt) {
    Write-Ok "Auto-recall extension enabled."
    Write-Step "Launching Pi..."
    & pi --extension $recallExt @args
} else {
    Write-Warn2 "dsh-ltm auto-recall extension not found - starting without it."
    Write-Step "Launching Pi..."
    & pi @args
}
exit $LASTEXITCODE
