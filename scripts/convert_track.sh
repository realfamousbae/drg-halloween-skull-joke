#!/usr/bin/env bash
# Converts any audio file into a WAV that UE 4.27 imports cleanly:
# 44.1 kHz, 16-bit PCM, loudness-normalised, mono by default (mono is required
# for 3D spatialisation, so the track will come from the skull, not from everywhere).
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 <input> [--out FILE] [--max-seconds N] [--stereo] [--fade-out SECONDS]

  --out FILE          output path (default: audio/converted/<name>.wav)
  --max-seconds N     cut the track to N seconds
  --stereo            keep stereo (NOT spatialised in-game)
  --fade-out S        fade out over the last S seconds (default: 0.5 when --max-seconds is set)
USAGE
}

[[ $# -ge 1 ]] || { usage; exit 1; }
input="$1"; shift
out=""; max=""; channels=1; fade=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) out="$2"; shift 2 ;;
    --max-seconds) max="$2"; shift 2 ;;
    --stereo) channels=2; shift ;;
    --fade-out) fade="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -f "$input" ]] || { echo "File not found: $input" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is not installed" >&2; exit 1; }

if [[ -z "$out" ]]; then
  repo_root="$(cd "$(dirname "$0")/.." && pwd)"
  name="$(basename "${input%.*}")"
  out="$repo_root/audio/converted/$name.wav"
fi
mkdir -p "$(dirname "$out")"

filters="loudnorm=I=-16:TP=-1.5:LRA=11"
trim=()
if [[ -n "$max" ]]; then
  trim=(-t "$max")
  fade="${fade:-0.5}"
fi
if [[ -n "$fade" ]]; then
  [[ -n "$max" ]] || { echo "--fade-out needs --max-seconds" >&2; exit 1; }
  start=$(awk "BEGIN { s = $max - $fade; print (s < 0 ? 0 : s) }")
  filters="$filters,afade=t=out:st=$start:d=$fade"
fi

ffmpeg -hide_banner -loglevel error -y -i "$input" "${trim[@]}" \
  -af "$filters" -ar 44100 -ac "$channels" -c:a pcm_s16le "$out"

echo "Written: $out"
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels:format=duration \
  -of default=noprint_wrappers=1 "$out"
