<#
.SYNOPSIS
  Copies the built .pak into DRG's local mods folder for testing.
  Then enable the mod in-game: Modding menu -> local mods.

.EXAMPLE
  .\scripts\install_local.ps1
  .\scripts\install_local.ps1 -GameDir 'D:\SteamLibrary\steamapps\common\Deep Rock Galactic'
#>
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Deep Rock Galactic',
    [string]$ModName = 'SkullJoke'
)
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent
$pak = Join-Path $repoRoot "build\${ModName}_P.pak"
if (-not (Test-Path $pak)) { throw "Pak not found: $pak. Run scripts\pack.ps1 first." }
if (-not (Test-Path (Join-Path $GameDir 'FSD'))) { throw "DRG not found in: $GameDir. Pass -GameDir." }

$dest = Join-Path $GameDir "FSD\Mods\$ModName"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item $pak -Destination $dest -Force
Write-Host "Installed: $(Join-Path $dest (Split-Path $pak -Leaf))"
