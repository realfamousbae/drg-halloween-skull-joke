# Ассеты звука летающего черепа

> Заполняется после поиска в FModel (README → шаг 1). Пути в игре меняются между
> обновлениями, поэтому после каждого крупного патча DRG их стоит перепроверить.

| Что звучит | Тип | Путь (FSD/Content/…) | Длит. | Looping | Sound Class | Attenuation |
|---|---|---|---|---|---|---|
| Полёт черепа (луп) | SoundWave / SoundCue | `?` | ? | ? | ? | ? |
| Подбор черепа | SoundWave / SoundCue | `?` | ? | ? | ? | ? |

## Как искать

1. FModel → загрузить `FSD/Content/Paks/FSD-WindowsNoEditor.pak`, указать UE4.27 и mappings-файл DRG.
2. Поиск пакетов (Ctrl+Shift+F) по `Skull`, `Halloween`, `Spooky`, `Pumpkin`.
3. Найти Blueprint самого черепа (обычно `BP_…Skull…`), открыть его JSON и посмотреть
   ссылки на `SoundCue` / `SoundWave` (`AudioComponent` → `Sound`, или вызовы `PlaySound…`).
4. Если ссылка ведёт на `SoundCue`, открыть его и выписать все `SoundWave` внутри:
   проще всего заменить их (cue при этом остаётся оригинальным — громкость и затухание не сломаются).
5. Перенести найденные пути в таблицу выше и в `mod/assets.txt`.
