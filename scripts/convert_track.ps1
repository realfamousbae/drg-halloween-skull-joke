<#
.SYNOPSIS
  Converts any audio file into a WAV that UE 4.27 imports cleanly:
  44.1 kHz, 16-bit PCM, loudness-normalised, mono by default
  (mono is required for 3D spatialisation in-game).

.EXAMPLE
  .\scripts\convert_track.ps1 -InputFile audio\source\my_track.mp3 -MaxSeconds 30
#>
param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [string]$Out,
    [double]$MaxSeconds = 0,
    [double]$FadeOut = 0.5,
    [switch]$Stereo
)
$ErrorActionPreference = 'Stop'

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'ffmpeg is not installed or not in PATH (winget install Gyan.FFmpeg)'
}
if (-not (Test-Path $InputFile)) { throw "File not found: $InputFile" }

if (-not $Out) {
    $repoRoot = Split-Path $PSScriptRoot -Parent
    $name = [IO.Path]::GetFileNameWithoutExtension($InputFile)
    $Out = Join-Path $repoRoot "audio\converted\$name.wav"
}
New-Item -ItemType Directory -Force -Path (Split-Path $Out -Parent) | Out-Null

$filters = 'loudnorm=I=-16:TP=-1.5:LRA=11'
$ffArgs = @('-hide_banner', '-loglevel', 'error', '-y', '-i', $InputFile)
if ($MaxSeconds -gt 0) {
    $ffArgs += @('-t', "$MaxSeconds")
    $start = [Math]::Max(0, $MaxSeconds - $FadeOut)
    $filters += ",afade=t=out:st=$($start.ToString([Globalization.CultureInfo]::InvariantCulture)):d=$($FadeOut.ToString([Globalization.CultureInfo]::InvariantCulture))"
}
$channels = if ($Stereo) { 2 } else { 1 }
$ffArgs += @('-af', $filters, '-ar', '44100', '-ac', "$channels", '-c:a', 'pcm_s16le', $Out)

& ffmpeg @ffArgs
if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed with exit code $LASTEXITCODE" }

Write-Host "Written: $Out"
& ffprobe -v error -show_entries stream=codec_name,sample_rate,channels:format=duration -of default=noprint_wrappers=1 $Out
