#!/usr/bin/env python3
"""Build SkullJoke_P.pak without the Unreal Editor.

The two skull idle SoundWaves are cooked assets whose audio is a plain OGG Vorbis blob stored
inline in the .uexp. We unpack the originals from the game pak, swap that blob for the user's
track (re-encoded with ffmpeg) and patch the few fields that depend on it (sizes, Duration,
TotalSamples, NumChannels), so every name/path/reference stays byte-identical to vanilla.

    python scripts/build_mod.py [--input track.mp3] [--game-dir "<DRG dir>"] [--repak repak.exe]
"""
import argparse
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / "build"
AUDIO_EXT = {".mp3", ".ogg", ".flac", ".wav", ".m4a", ".opus", ".aac"}
DEFAULT_GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Deep Rock Galactic")

SAMPLE_RATE = 48000      # same as the vanilla waves, so SampleRate needs no patching
TARGET_LUFS = -18.5      # vanilla waves measure -20.1 / -17.4 LUFS
TRUE_PEAK = -3.0

# Fixed layout of these cooked waves (identical for A and B, asserted below).
PROP_NUM_CHANNELS, PROP_SAMPLE_RATE, PROP_DURATION, PROP_TOTAL_SAMPLES = 25, 54, 83, 112
BULK_ELEMENTS, BULK_SIZE, OGG_START = 148, 152, 164
TRAILER = 20             # CompressedDataGuid (16) + package tag (4) after the bulk data
UASSET_SERIAL_SIZE, UASSET_BULK_START = 694, 169


def die(msg):
    sys.exit(f"error: {msg}")


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        die(f"{Path(str(cmd[0])).name} failed:\n{r.stderr[-2000:]}")
    return r


def read_assets():
    lines = (REPO / "mod" / "assets.txt").read_text(encoding="utf-8").splitlines()
    assets = [l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")]
    if not assets:
        die("mod/assets.txt is empty")
    return assets


def pick_input(arg):
    if arg:
        return Path(arg)
    src = sorted(p for p in (REPO / "audio" / "source").glob("*") if p.suffix.lower() in AUDIO_EXT)
    if src:
        return src[0]
    print("audio/source is empty - using audio/placeholder.wav")
    return REPO / "audio" / "placeholder.wav"


def encode_ogg(src, dst, channels, max_seconds, fade, loudness):
    af = []
    if loudness:
        af.append(f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA=11")
    # fade-out so a trimmed track doesn't end with a click
    af.append(f"afade=t=out:st={max(max_seconds - fade, 0)}:d={fade}")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-t", max_seconds,
         "-vn", "-ac", channels, "-ar", SAMPLE_RATE, "-af", ",".join(af),
         "-c:a", "libvorbis", "-q:a", "5", "-f", "ogg", dst])
    data = Path(dst).read_bytes()
    if not data.startswith(b"OggS"):
        die("ffmpeg did not produce an OGG file")
    return data


def duration_of(ogg_path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", ogg_path])
    return float(r.stdout.strip())


def patch_wave(uasset, uexp, ogg, channels, duration):
    ua, ux = bytearray(uasset), bytearray(uexp)
    old_len = struct.unpack_from("<i", ux, BULK_ELEMENTS)[0]
    # sanity-check the layout we rely on, so a game update fails loudly instead of corrupting audio
    ok = (struct.unpack_from("<i", ux, PROP_SAMPLE_RATE)[0] == SAMPLE_RATE
          and ux[OGG_START:OGG_START + 4] == b"OggS"
          and struct.unpack_from("<i", ux, BULK_SIZE)[0] == old_len
          and len(ux) == OGG_START + old_len + TRAILER
          and struct.unpack_from("<q", ua, UASSET_SERIAL_SIZE)[0] == len(ux) - 4
          and struct.unpack_from("<q", ua, UASSET_BULK_START)[0] == len(ua) + len(ux) - 4)
    if not ok:
        die("unexpected SoundWave layout - the game was probably updated; re-check the asset (see README)")

    new_ux = bytearray(ux[:OGG_START]) + ogg + ux[OGG_START + old_len:]
    struct.pack_into("<i", new_ux, PROP_NUM_CHANNELS, channels)
    struct.pack_into("<f", new_ux, PROP_DURATION, duration)
    struct.pack_into("<f", new_ux, PROP_TOTAL_SAMPLES, duration * SAMPLE_RATE)
    struct.pack_into("<i", new_ux, BULK_ELEMENTS, len(ogg))
    struct.pack_into("<i", new_ux, BULK_SIZE, len(ogg))
    struct.pack_into("<q", ua, UASSET_SERIAL_SIZE, len(new_ux) - 4)
    struct.pack_into("<q", ua, UASSET_BULK_START, len(ua) + len(new_ux) - 4)
    return bytes(ua), bytes(new_ux)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="track to play (default: first file in audio/source, else placeholder)")
    ap.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    ap.add_argument("--repak", default="repak")
    ap.add_argument("--mod-name", default="SkullJoke")
    ap.add_argument("--max-seconds", type=float, default=20.0,
                    help="trim the track to this length (vanilla waves are 20.5 s and 18.4 s)")
    ap.add_argument("--fade", type=float, default=1.0, help="fade-out length in seconds")
    ap.add_argument("--stereo", action="store_true",
                    help="keep stereo (vanilla); default is mono, which is positioned in 3D at the skull")
    ap.add_argument("--no-loudnorm", action="store_true")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe", args.repak):
        if not shutil.which(tool):
            die(f"{tool} not found in PATH")
    game_pak = args.game_dir / "FSD" / "Content" / "Paks" / "FSD-WindowsNoEditor.pak"
    if not game_pak.exists():
        die(f"game pak not found: {game_pak} (use --game-dir)")

    assets = read_assets()
    src = pick_input(args.input)
    channels = 2 if args.stereo else 1
    if BUILD.exists():
        shutil.rmtree(BUILD)
    vanilla, stage = BUILD / "vanilla", BUILD / "stage"
    vanilla.mkdir(parents=True)

    print(f"track: {src.name}")
    ogg_file = BUILD / "track.ogg"
    ogg = encode_ogg(src, ogg_file, channels, args.max_seconds, args.fade, not args.no_loudnorm)
    duration = duration_of(ogg_file)
    print(f"encoded: {duration:.2f} s, {channels} ch, {len(ogg) / 1024:.0f} KiB")

    includes = [x for a in assets for x in ("-i", f"FSD/Content/{a}.*")]
    run([args.repak, "unpack", *includes, "-o", vanilla, game_pak])

    for a in assets:
        base = vanilla / "FSD" / "Content" / a
        ua_path, ux_path = base.with_name(base.name + ".uasset"), base.with_name(base.name + ".uexp")
        if not ua_path.exists() or not ux_path.exists():
            die(f"asset not found in the game pak: {a}")
        ua, ux = patch_wave(ua_path.read_bytes(), ux_path.read_bytes(), ogg, channels, duration)
        out = stage / "FSD" / "Content" / (a + ".uasset")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(ua)
        out.with_suffix(".uexp").write_bytes(ux)
        print(f"patched {a}")

    pak = BUILD / f"{args.mod_name}_P.pak"
    run([args.repak, "pack", "--version", "V11", stage, pak])
    print(run([args.repak, "list", pak]).stdout.strip())
    print(f"done: {pak}")


if __name__ == "__main__":
    main()
