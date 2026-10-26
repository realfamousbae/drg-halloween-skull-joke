# DRG Halloween Skull Joke

Аудио-мод для **Deep Rock Galactic**: летающий хэллоуинский череп играет ваш трек вместо своего звука.

Принцип — **замена ассета**: собираем `SoundWave` с тем же путём и именем, что у оригинала,
кладём в `.pak`, и игра грузит его вместо исходного. Ни Blueprint-логики, ни мод-лоадера не нужно,
мод клиентский (на mod.io — тег **Audio**).

## Структура

| Путь | Что там |
|---|---|
| `audio/placeholder.wav` | Заглушка (3 с, 44.1 кГц, 16-bit, моно), пока нет трека |
| `audio/source/` | Сюда кладётся исходный трек (не коммитится) |
| `scripts/convert_track.sh` / `.ps1` | Любой формат → WAV для UE 4.27 (нормализация громкости, обрезка) |
| `scripts/build_mod.py` | Трек → `build/SkullJoke_P.pak` (без UE, через repak + ffmpeg) |
| `scripts/pack.ps1` | Альтернатива: cooked-ассеты из UE → `.pak` |
| `scripts/install_local.ps1` | Копирует `.pak` в `FSD/Mods` для локальной проверки |
| `mod/ASSET_PATHS.md` | Найденные пути звуков черепа (заполнить!) |
| `mod/assets.txt` | Тот же список для `pack.ps1` |
| `modio/description.md` | Текст и теги для страницы на mod.io |

## Инструменты

- **repak** — распаковка/упаковка `.pak`: <https://github.com/trumank/repak/releases>
- **ffmpeg** (с `libvorbis`) — конвертация трека (`winget install Gyan.FFmpeg`)
- **Python 3** — `scripts/build_mod.py`

Unreal Engine не нужен: звук в `SoundWave` хранится как готовый OGG Vorbis внутри `.uexp`.
`build_mod.py` достаёт оригиналы из игрового `.pak`, подменяет OGG вашим треком и правит зависящие
от него поля (размеры, `Duration`, `TotalSamples`, `NumChannels`). Все имена и ссылки остаются как у оригинала.

## Шаги

### 1. Положить трек
Скопируйте файл (mp3/ogg/flac/wav/m4a) в `audio/source/` — берётся первый по алфавиту.
Если папка пуста, используется `audio/placeholder.wav` (3-секундная заглушка).

### 2. Собрать
```powershell
python scripts\build_mod.py --repak X:\DRGModding\tools\repak\repak.exe
```
Что делает: обрезает трек до `--max-seconds` (20 с; в игре он зациклен), нормализует громкость
до −14 LUFS (`--lufs`), кодирует в OGG **моно** 48 кГц (только моно позиционируется в 3D — звук идёт от черепа;
`--stereo` оставит стерео), кладёт трек в волну IdleA, тишину в IdleB, патчит cue (громкость ×2, без
изменения pitch от скорости черепа и без рандомного детюна) и пакует `build\SkullJoke_P.pak`.
Какие ассеты заменяются — см. [`mod/ASSET_PATHS.md`](mod/ASSET_PATHS.md) и `mod/assets.txt`.

> Альтернатива «как у всех»: импорт WAV в UE 4.27 → cook → `scripts/pack.ps1`. Нужна, только если
> понадобится заменить ассет другого формата (например, стриминговый).

### 3. Проверка локально
```powershell
.\scripts\install_local.ps1 -GameDir 'D:\SteamLibrary\steamapps\common\Deep Rock Galactic'
```
В игре: меню **Modding** → включить локальный мод → перезапуск. Дальше — миссия во время хэллоуинского ивента.
Дополнительно откройте свой `.pak` в FModel и сравните путь ассета с оригиналом — если путь не совпадает, замена молча не сработает.

### 4. Публикация на mod.io
1. Запакуйте `SkullJoke_P.pak` в zip.
2. mod.io → Deep Rock Galactic → Add mod. Текст и теги — из [`modio/description.md`](modio/description.md). Обязательно тег **Audio**.
3. Дождитесь одобрения модерацией.

> ⚠️ На mod.io нельзя выкладывать чужую музыку без разрешения правообладателя — используйте свой трек или трек со свободной лицензией.

## После обновлений DRG
Если игра переименует или переместит ассет, мод перестанет работать: повторите шаг 1 и пересоберите.
