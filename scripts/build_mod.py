#!/usr/bin/env python3
"""Build SkullJoke_P.pak without the Unreal Editor.

The skull idle SoundWaves are cooked assets whose audio is a plain OGG Vorbis blob stored
inline in the .uexp. We unpack the originals from the game pak, swap that blob for the user's
track (re-encoded with ffmpeg) and patch the few fields that depend on it (sizes, Duration,
TotalSamples, NumChannels), so every name/path/reference stays byte-identical to vanilla.

HalloweenSkullIdle_Cue mixes IdleA and IdleB at the same time, so the track goes into IdleA only
and IdleB gets silence. The cue itself is patched in place (same byte size) to play the track
as-is: no speed-driven pitch, no random detune, full volume. See mod/ASSET_PATHS.md.

    python scripts/build_mod.py [--input track.mp3] [--game-dir "<DRG dir>"] [--repak repak.exe]
"""
import argparse
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / "build"
AUDIO_EXT = {".mp3", ".ogg", ".flac", ".wav", ".m4a", ".opus", ".aac"}
DEFAULT_GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Deep Rock Galactic")

HALLOWEEN = "Audio/SFX/Season_Halloween/"
WAVE_TRACK = HALLOWEEN + "HalloweenSkull/HalloweenSkullIdleA_1"
WAVE_SILENT = HALLOWEEN + "HalloweenSkull/HalloweenSkullIdleB_1"
CUE = HALLOWEEN + "HalloweenSkullIdle_Cue"

SAMPLE_RATE = 48000      # same as the vanilla waves, so SampleRate needs no patching
DEFAULT_LUFS = -14.0     # vanilla waves measure -20.1 / -17.4 LUFS, but they play doubled
TRUE_PEAK = -2.0         # Vorbis overshoots by ~1 dB, keep the decoded peak below 0 dBFS
SILENCE_SECONDS = 1.0

# Fixed layout of these cooked waves (identical for A and B, asserted below).
PROP_NUM_CHANNELS, PROP_SAMPLE_RATE, PROP_DURATION, PROP_TOTAL_SAMPLES = 25, 54, 83, 112
BULK_ELEMENTS, BULK_SIZE, OGG_START = 148, 152, 164
TRAILER = 20             # CompressedDataGuid (16) + package tag (4) after the bulk data
UASSET_SERIAL_SIZE, UASSET_BULK_START = 694, 169

# In-place cue patches: (uexp offset, format, vanilla value, new value, what).
CUE_PATCHES = [
    (29 + 25, "<f", 0.5, 1.0, "SoundCue.VolumeMultiplier"),
    (930 + 25, "<f", 0.7, 1.0, "root ModulatorContinuous pitch MinOutput (Speed 0)"),
    (959 + 25, "<f", 2.0, 1.0, "root ModulatorContinuous pitch MaxOutput (Speed 1)"),
    # Mixer_1.ChildNodes[0]: Modulator_0 (random pitch 0.95-1.05) -> WavePlayer_0 (IdleA) directly
    (340, "<i", 5, 11, "Mixer_1.ChildNodes[0]"),
]


def die(msg):
    sys.exit(f"error: {msg}")


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        die(f"{Path(str(cmd[0])).name} failed:\n{r.stderr[-2000:]}")
    return r


def pick_input(arg):
    if arg:
        return Path(arg)
    src = sorted(p for p in (REPO / "audio" / "source").glob("*") if p.suffix.lower() in AUDIO_EXT)
    if src:
        return src[0]
    print("audio/source is empty - using audio/placeholder.wav")
    return REPO / "audio" / "placeholder.wav"


def encode_ogg(src, dst, channels, max_seconds, fade, lufs):
    af = []
    if lufs is not None:
        af.append(f"loudnorm=I={lufs}:TP={TRUE_PEAK}:LRA=11")
        # single-pass loudnorm doesn't always hold TP; a hard limiter does
        af.append(f"alimiter=limit={10 ** (TRUE_PEAK / 20):.3f}:level=false")
    if fade > 0:
        # fade-out so a trimmed track doesn't end with a click
        af.append(f"afade=t=out:st={max(max_seconds - fade, 0)}:d={fade}")
    filters = ["-af", ",".join(af)] if af else []
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-t", max_seconds,
         "-vn", "-ac", channels, "-ar", SAMPLE_RATE, *filters,
         "-c:a", "libvorbis", "-q:a", "5", "-f", "ogg", dst])
    return read_ogg(dst)


def encode_silence(dst, channels):
    layout = "stereo" if channels == 2 else "mono"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
         "-i", f"anullsrc=r={SAMPLE_RATE}:cl={layout}", "-t", SILENCE_SECONDS,
         "-c:a", "libvorbis", "-q:a", "0", "-f", "ogg", dst])
    return read_ogg(dst)


def read_ogg(path):
    data = Path(path).read_bytes()
    if not data.startswith(b"OggS"):
        die(f"ffmpeg did not produce an OGG file: {path}")
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path])
    return data, float(r.stdout.strip())


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


def patch_cue(uexp):
    ux = bytearray(uexp)
    if len(ux) != 1672:
        die("unexpected SoundCue size - the game was probably updated; re-check the cue (see README)")
    for off, fmt, old, new, what in CUE_PATCHES:
        cur = struct.unpack_from(fmt, ux, off)[0]
        if abs(cur - old) > 1e-4:
            die(f"unexpected {what} = {cur} (expected {old}) - re-check the cue (see README)")
        struct.pack_into(fmt, ux, off, new)
    return bytes(ux)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="track to play (default: first file in audio/source, else placeholder)")
    ap.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    ap.add_argument("--repak", default="repak")
    ap.add_argument("--mod-name", default="SkullJoke")
    ap.add_argument("--max-seconds", type=float, default=20.0,
                    help="trim the track to this length; it loops in game (vanilla waves are 20.5 s)")
    ap.add_argument("--fade", type=float, default=1.0, help="fade-out length in seconds, 0 to disable")
    ap.add_argument("--lufs", type=float, default=DEFAULT_LUFS, help="loudness target, integrated LUFS")
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

    src = pick_input(args.input)
    channels = 2 if args.stereo else 1
    if BUILD.exists():
        shutil.rmtree(BUILD)
    vanilla, stage = BUILD / "vanilla", BUILD / "stage"
    vanilla.mkdir(parents=True)

    print(f"track: {src.name}")
    lufs = None if args.no_loudnorm else args.lufs
    track = encode_ogg(src, BUILD / "track.ogg", channels, args.max_seconds, args.fade, lufs)
    print(f"encoded: {track[1]:.2f} s, {channels} ch, {len(track[0]) / 1024:.0f} KiB")
    silence = encode_silence(BUILD / "silence.ogg", channels)

    includes = [x for a in (WAVE_TRACK, WAVE_SILENT, CUE) for x in ("-i", f"FSD/Content/{a}.*")]
    run([args.repak, "unpack", *includes, "-o", vanilla, game_pak])

    def files(root, asset):
        base = root / "FSD" / "Content" / asset
        return base.with_name(base.name + ".uasset"), base.with_name(base.name + ".uexp")

    for asset, (ogg, duration) in ((WAVE_TRACK, track), (WAVE_SILENT, silence), (CUE, (None, None))):
        ua_path, ux_path = files(vanilla, asset)
        if not ua_path.exists() or not ux_path.exists():
            die(f"asset not found in the game pak: {asset}")
        ua, ux = ua_path.read_bytes(), ux_path.read_bytes()
        if asset == CUE:
            ux = patch_cue(ux)
        else:
            ua, ux = patch_wave(ua, ux, ogg, channels, duration)
        out_ua, out_ux = files(stage, asset)
        out_ua.parent.mkdir(parents=True, exist_ok=True)
        out_ua.write_bytes(ua)
        out_ux.write_bytes(ux)
        print(f"patched {asset}")

    pak = BUILD / f"{args.mod_name}_P.pak"
    run([args.repak, "pack", "--version", "V11", stage, pak])
    print(run([args.repak, "list", pak]).stdout.strip())
    print(f"done: {pak}")


if __name__ == "__main__":
    main()
