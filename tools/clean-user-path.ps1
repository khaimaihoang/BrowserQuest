<#
    clean-user-path.ps1
    -------------------
    Make the per-user PATH sane:

      1. Back up the current User and Machine PATH (raw, unexpanded) to
         ~/path-backup-<timestamp>.txt first.
      2. Drop duplicate User entries (case-insensitive, ignoring a trailing "\").
      3. Drop User entries already present in the Machine PATH (redundant).
      4. Guarantee the npm global dir and Pi's bin dir stay reachable.

    Only HKCU\Environment\Path is modified, and its value kind (REG_SZ vs
    REG_EXPAND_SZ) is preserved. Already-open terminals/explorer keep their old
    copy until restarted; open a NEW terminal (or re-login) to pick up changes.

    Usage:
      powershell -ExecutionPolicy Bypass -File .\clean-user-path.ps1 -DryRun
      powershell -ExecutionPolicy Bypass -File .\clean-user-path.ps1
#>
[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Strip surrounding spaces and a trailing backslash, while keeping drive roots
# like "C:\" intact ("C:" would mean the current directory on drive C:).
function Get-Norm([string]$p) {
    $t = "$p".Trim()
    if ($t -match '^[A-Za-z]:\\$') { return $t }
    return $t.TrimEnd('\')
}
# Comparison key: expand %VARS% and lowercase so equivalent entries collapse.
function Get-Key([string]$p) {
    return ([Environment]::ExpandEnvironmentVariables((Get-Norm $p))).ToLowerInvariant()
}

$doNotExpand = [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames
$userKey    = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', (-not $DryRun))
$machineKey = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SYSTEM\CurrentControlSet\Control\Session Manager\Environment', $false)

$userRaw    = [string]$userKey.GetValue('Path', '', $doNotExpand)
$userKind   = $userKey.GetValueKind('Path')
$machineRaw = [string]$machineKey.GetValue('Path', '', $doNotExpand)

$npmDir = Get-Norm (Join-Path $env:APPDATA 'npm')
$piBin  = Get-Norm (Join-Path $HOME '.pi\agent\bin')

$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $HOME "path-backup-$stamp.txt"
[System.IO.File]::WriteAllText($backup, (@(
    "PATH backup - $stamp",
    "",
    "USER kind=$userKind length=$($userRaw.Length)",
    $userRaw,
    "",
    "MACHINE length=$($machineRaw.Length)",
    $machineRaw
) -join "`r`n"))
Write-Host "Backup written: $backup"

$machineKeys = New-Object -TypeName 'System.Collections.Generic.HashSet[string]' -ArgumentList ([StringComparer]::OrdinalIgnoreCase)
foreach ($e in ($machineRaw -split ';')) {
    if ((Get-Norm $e)) { [void]$machineKeys.Add((Get-Key $e)) }
}

$seen = New-Object -TypeName 'System.Collections.Generic.HashSet[string]' -ArgumentList ([StringComparer]::OrdinalIgnoreCase)
$kept = New-Object -TypeName 'System.Collections.Generic.List[string]'
$duplicates = 0
$machineDup = 0

foreach ($e in ($userRaw -split ';')) {
    $n = Get-Norm $e
    if (-not $n) { continue }
    if (-not $seen.Add((Get-Key $n))) { $duplicates++; continue }
    if ($machineKeys.Contains((Get-Key $n))) { $machineDup++; continue }
    $kept.Add($n)
}

foreach ($must in @($npmDir, $piBin)) {
    if ($must -and -not $seen.Contains((Get-Key $must))) {
        $kept.Add($must)
        Write-Host "Re-added missing entry: $must"
    }
}

$newRaw = ($kept -join ';')
$oldCount = @($userRaw -split ';' | Where-Object { (Get-Norm $_) }).Count
Write-Host ("USER PATH: {0} entries / {1} chars  ->  {2} entries / {3} chars" -f $oldCount, $userRaw.Length, $kept.Count, $newRaw.Length)
Write-Host ("Removed: {0} duplicate(s), {1} already-in-Machine" -f $duplicates, $machineDup)

if ($DryRun) {
    Write-Host "DryRun: registry left untouched."
    $userKey.Close()
    exit 0
}
if ($newRaw.Length -ge $userRaw.Length) {
    Write-Host "No size improvement - leaving the registry untouched."
    $userKey.Close()
    exit 0
}

if ($userKind -eq 'ExpandString') {
    $userKey.SetValue('Path', $newRaw, [Microsoft.Win32.RegistryValueKind]::ExpandString)
} else {
    $userKey.SetValue('Path', $newRaw, [Microsoft.Win32.RegistryValueKind]::String)
}
$userKey.Close()
Write-Host "User PATH updated. Open a NEW terminal (or re-login) to pick it up."
