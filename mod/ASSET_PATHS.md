# Ассеты звука летающего черепа

Найдено сканированием индекса `FSD-WindowsNoEditor.pak` и разбором распакованных ассетов (build, сентябрь–октябрь 2026).
Пути в игре меняются между обновлениями — после крупного патча DRG их стоит перепроверить.

## Что заменяет мод

Cue `Audio/SFX/Season_Halloween/HalloweenSkullIdle_Cue` — это `SoundNodeMixer` с четырьмя `SoundNodeWavePlayer`.
Мод **не трогает cue**, а подменяет две его SoundWave (cue, затухание и SoundClass остаются оригинальными):

| Что звучит | Путь (FSD/Content/…) | Длит. | Каналы | Громкость |
|---|---|---|---|---|
| Idle-звук черепа, вариант A | `Audio/SFX/Season_Halloween/HalloweenSkull/HalloweenSkullIdleA_1` | 20.5 с | 2 × 48 кГц, OGG | −20.1 LUFS |
| Idle-звук черепа, вариант B | `Audio/SFX/Season_Halloween/HalloweenSkull/HalloweenSkullIdleB_1` | 18.4 с | 2 × 48 кГц, OGG | −17.4 LUFS |

В том же cue есть ещё два звука огненных шаров босса (`Audio/SFX/Enemies/GlyphidDreadnaught/Fireball/SpiderTankBoss_FireballB_1`, `…FireballC_1`) —
они **не заменяются** (их используют другие враги), поэтому поверх трека может быть слышен тихий «огненный» слой.

Затухание по расстоянию: `Audio/SoundControl/AttenuationGroups/HalloweenSkullSoundAttenuation`
(cue ссылается на `GenericNarrowLargeAttenuation` — какое реально применяется, проверить в игре).

## Другие звуки черепа (не заменяются, кандидаты для следующих версий)

| Cue | Когда |
|---|---|
| `Audio/SFX/Season_Halloween/HalloweenSkullJaw_Cue` | щёлкает челюсть |
| `Audio/SFX/Season_Halloween/HalloweenSkull_Hurt_Cue` | урон |
| `Audio/SFX/Season_Halloween/HalloweenSkull_Dies_Cue` | смерть |
| `Audio/SFX/Season_Halloween/HalloweenSkull_Drop_Cue` | падение / подбор |

Блюпринты черепа: `GameElements/Holidays/Halloween/BP_Halloween_Skull`, `BP_Halloween_Skull_Throwable`.

## Как перепроверять после обновления игры

1. `repak list` по `FSD-WindowsNoEditor.pak` — искать `Season_Halloween/HalloweenSkull`.
2. Распаковать нужные ассеты (`repak unpack -i 'FSD/Content/Audio/SFX/Season_Halloween/*'`) и посмотреть имена в `.uasset`.
3. `scripts/build_mod.py` сам проверяет структуру SoundWave и остановится с ошибкой, если она изменилась.
