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
| `scripts/pack.ps1` | Cooked-ассеты → `build/SkullJoke_P.pak` через repak |
| `scripts/install_local.ps1` | Копирует `.pak` в `FSD/Mods` для локальной проверки |
| `mod/ASSET_PATHS.md` | Найденные пути звуков черепа (заполнить!) |
| `mod/assets.txt` | Тот же список для `pack.ps1` |
| `modio/description.md` | Текст и теги для страницы на mod.io |

## Инструменты

- **Unreal Engine 4.27** (Epic Games Launcher)
- **FSD-Template** — шаблонный проект DRG из сообщества DRG Modding (ссылка в их Discord / на сайте DRG Modding)
- **FModel** — просмотр ассетов игры (+ mappings `.usmap` для DRG)
- **repak** — упаковка `.pak`: <https://github.com/trumank/repak/releases>
- **ffmpeg** — конвертация трека (`winget install Gyan.FFmpeg`)

## Шаги

### 1. Найти звук черепа
Подробно — в [`mod/ASSET_PATHS.md`](mod/ASSET_PATHS.md). Итог шага: точные пути `SoundWave`
(например, `Audio/Halloween/SW_FlyingSkull_Loop`), которые вписываются в таблицу и в `mod/assets.txt`.
Заодно выпишите у оригинала **Looping**, **Sound Class**, **Attenuation** и длительность.

> Если череп играет `SoundCue`, заменяйте `SoundWave` внутри него, а не сам cue: тогда
> громкость, затухание по расстоянию и ползунки в настройках продолжат работать как в оригинале.

### 2. Подготовить трек
```powershell
.\scripts\convert_track.ps1 -InputFile audio\source\my_track.mp3 -MaxSeconds 30
```
По умолчанию получается **моно** — только моно-звук позиционируется в 3D (трек будет звучать от черепа).
`-Stereo` оставит стерео, но тогда звук будет «в голове» у игрока. Пока трека нет — берите `audio/placeholder.wav`.

### 3. Импорт в UE 4.27
1. Откройте FSD-Template.
2. В Content Browser создайте папки, **точно** повторяющие путь из шага 1 (`Content/Audio/Halloween/…`).
3. Перетащите WAV в эту папку и переименуйте ассет **точно** в имя оригинала.
4. В свойствах `SoundWave` выставьте Looping / Sound Class / Attenuation как у оригинала.
   Ассеты Sound Class и Attenuation в шаблоне есть заглушками по тем же путям, что и в игре.

### 4. Cook
`File → Cook Content for Windows`. Результат — `FSD-Template\Saved\Cooked\WindowsNoEditor\FSD\Content\…`

### 5. Pack
```powershell
.\scripts\pack.ps1 -ProjectDir C:\Modding\FSD-Template
```
Скрипт возьмёт только ассеты из `mod/assets.txt` (чтобы не утащить в мод весь шаблон) и соберёт `build\SkullJoke_P.pak`.

### 6. Проверка локально
```powershell
.\scripts\install_local.ps1 -GameDir 'D:\SteamLibrary\steamapps\common\Deep Rock Galactic'
```
В игре: меню **Modding** → включить локальный мод → перезапуск. Дальше — миссия во время хэллоуинского ивента.
Дополнительно откройте свой `.pak` в FModel и сравните путь ассета с оригиналом — если путь не совпадает, замена молча не сработает.

### 7. Публикация на mod.io
1. Запакуйте `SkullJoke_P.pak` в zip.
2. mod.io → Deep Rock Galactic → Add mod. Текст и теги — из [`modio/description.md`](modio/description.md). Обязательно тег **Audio**.
3. Дождитесь одобрения модерацией.

> ⚠️ На mod.io нельзя выкладывать чужую музыку без разрешения правообладателя — используйте свой трек или трек со свободной лицензией.

## После обновлений DRG
Если игра переименует или переместит ассет, мод перестанет работать: повторите шаг 1 и пересоберите.
