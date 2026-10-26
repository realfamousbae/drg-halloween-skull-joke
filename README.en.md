# Halloween Skull Joke

[Русский](README.md) · **English**

A **Deep Rock Galactic** mod: the flying Halloween skull plays your track instead of its idle sound.

- **Audio only.** The pak contains nothing but SoundWave assets and one patched skull Sound Cue; gameplay and blueprints are untouched.
- **Client-side.** Only players who have the mod hear the music; nobody else in the lobby needs it.
- **The sound comes from the skull itself** (3D), fades with distance and plays without the speed-based pitch shift.

## How it works

The skull's sound is played by `HalloweenSkullIdle_Cue`: it mixes two waves, `HalloweenSkullIdleA_1` and `HalloweenSkullIdleB_1`, and shifts pitch with the skull's speed. The mod replaces those assets **with the same paths and names**, so no blueprints or mod loader are needed. Unreal Engine isn't needed either: the audio in a SoundWave is a ready-made OGG Vorbis blob inside the `.uexp`.

| What changes | How |
|---|---|
| `HalloweenSkullIdleA_1` | your track instead of the original, mono 48 kHz |
| `HalloweenSkullIdleB_1` | 1 s of silence: two copies at different pitch cause a flanger effect |
| `HalloweenSkullIdle_Cue` | patched in place, sizes unchanged: speed-based pitch off, no random detune, track volume ×4 (the UE cap), the fire layer under the skull sound muted |

Findings along the way:

- **Only mono is positioned in 3D.** The track is encoded as mono so the sound comes from the skull; `--stereo` keeps stereo.
- **The track is cut to 20 s** (`--max-seconds`): the wave loops in game.
- **Vanilla is quiet** (−20.1 and −17.4 LUFS). The track is normalized to −10 LUFS (`--lufs`) with a limiter and a −4 dB true-peak ceiling: Vorbis overshoots by up to 3 dB when decoded.
- The fire layer in the same cue belongs to the Dreadnought boss and its waves are used by other enemies, so they are not replaced; only the layer inside the skull cue is muted.

Asset paths and the cue layout: [mod/ASSET_PATHS.md](mod/ASSET_PATHS.md).

## Layout

```
audio/
  placeholder.wav         placeholder (3 s, 44.1 kHz, 16-bit, mono) until there is a track
  source/                 put your source track here, not stored in git
mod/
  ASSET_PATHS.md          skull sound paths and the cue layout
  assets.txt              the same list for pack.ps1
modio/
  description.md          mod.io page texts and settings
  logo.png                mod.io cover
CHANGELOG.md              version history
scripts/
  build_mod.py            track → build/SkullJoke_P.pak (no UE, via repak + ffmpeg)
  convert_track.sh / .ps1 any format → WAV for UE 4.27 (loudness, trim)
  pack.ps1                alternative: cooked assets from UE → .pak
  install_local.ps1       copies the .pak into FSD/Mods for local testing
```

## Building

Requires Windows, [repak](https://github.com/trumank/repak/releases), Python 3, ffmpeg with `libvorbis` (`winget install Gyan.FFmpeg`) and an installed DRG: the original assets are read from `FSD-WindowsNoEditor.pak`.

Put your track (mp3, ogg, flac, wav, m4a) into `audio/source/`; the first one alphabetically is used. If the folder is empty, `audio/placeholder.wav` is used.

```
python scripts\build_mod.py --repak <repak.exe>
```

Output: `build\SkullJoke_P.pak`. Zip it for mod.io.

Options:

- `--max-seconds 20` — track length, longer is cut.
- `--lufs -10` — loudness target.
- `--volume 4` — track volume in the cue.
- `--fade 1` — fade-out length in seconds, `0` disables it.
- `--stereo` — keep stereo, but then the sound isn't tied to the skull.

For local testing:

```
.\scripts\install_local.ps1 -GameDir '<DRG>'
```

In game: **Modding** menu → enable the local mod → restart. Then play a mission during the Halloween event. You can open your `.pak` in FModel and compare the asset path with the original: if the path differs, the replacement silently does nothing.

## After a DRG patch

```
repak list "<DRG>\FSD\Content\Paks\FSD-WindowsNoEditor.pak"
```

Look for `Season_Halloween/HalloweenSkull`. If the asset paths haven't changed, there's no need to rebuild. `build_mod.py` checks the SoundWave structure itself and stops with an error if it has changed. Then rebuild and upload the new file to the same mod on mod.io.

## See also

- [RFB Jukebox](https://github.com/realfamousbae/drg-rfb-jukebox-music): Space Rig jukebox music.
- [RFB Battle Music](https://github.com/realfamousbae/drg-rfb-battle-music): mission music.

---

The mod is hidden and meant for friends. Don't upload music you don't have the rights to on mod.io.
