# Исходный трек

Положите сюда свой трек (`.mp3`, `.ogg`, `.flac`, `.wav` — любой формат, который понимает ffmpeg).

Затем сконвертируйте его для UE 4.27:

```bash
./scripts/convert_track.sh audio/source/my_track.mp3
```

```powershell
.\scripts\convert_track.ps1 -InputFile audio\source\my_track.mp3
```

Результат появится в `audio/converted/`. Файлы из этой папки не коммитятся (см. `.gitignore`),
чтобы случайно не выложить чужую музыку.
