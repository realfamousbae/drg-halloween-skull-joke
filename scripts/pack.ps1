<#
.SYNOPSIS
  Packs the cooked replacement assets into a .pak for DRG (UE 4.27, pak V11) using repak.

.DESCRIPTION
  Reads asset paths from mod/assets.txt, copies their cooked files
  (.uasset/.uexp/.ubulk) from <ProjectDir>\Saved\Cooked\WindowsNoEditor\FSD\Content
  into build\stage\FSD\Content and runs `repak pack`.

.EXAMPLE
  .\scripts\pack.ps1 -ProjectDir C:\Modding\FSD-Template
#>
param(
    [Parameter(Mandatory = $true)][string]$ProjectDir,
    [string]$ModName = 'SkullJoke',
    [string]$Repak = 'repak'
)
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path $PSScriptRoot -Parent
$cookedContent = Join-Path $ProjectDir 'Saved\Cooked\WindowsNoEditor\FSD\Content'
if (-not (Test-Path $cookedContent)) {
    throw "Cooked content not found: $cookedContent. Run File -> Cook Content for Windows in UE 4.27 first."
}
if (-not (Get-Command $Repak -ErrorAction SilentlyContinue)) {
    throw "repak not found. Download it from https://github.com/trumank/repak/releases and add to PATH or pass -Repak <path>."
}

$assets = Get-Content (Join-Path $repoRoot 'mod\assets.txt') |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith('#') }
if (-not $assets) { throw 'mod\assets.txt has no asset paths. Fill it in first (see mod\ASSET_PATHS.md).' }

$buildDir = Join-Path $repoRoot 'build'
$stage = Join-Path $buildDir 'stage'
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }

foreach ($asset in $assets) {
    $rel = $asset -replace '/', '\'
    $files = Get-ChildItem -Path (Join-Path $cookedContent (Split-Path $rel -Parent)) `
        -Filter "$(Split-Path $rel -Leaf).*" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.uasset', '.uexp', '.ubulk' }
    if (-not $files) { throw "No cooked files for '$asset'. Check the path and that the asset was cooked." }

    $dest = Join-Path $stage (Join-Path 'FSD\Content' (Split-Path $rel -Parent))
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $files | Copy-Item -Destination $dest
    Write-Host "+ $asset ($($files.Name -join ', '))"
}

$pak = Join-Path $buildDir "${ModName}_P.pak"
& $Repak pack --version V11 $stage $pak
if ($LASTEXITCODE -ne 0) { throw "repak failed with exit code $LASTEXITCODE" }

& $Repak list $pak
Write-Host "Done: $pak"
