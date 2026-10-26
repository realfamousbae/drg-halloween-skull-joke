# Ассеты звука летающего черепа

Найдено сканированием индекса `FSD-WindowsNoEditor.pak` и разбором распакованных ассетов (build, сентябрь–октябрь 2026).
Пути в игре меняются между обновлениями — после крупного патча DRG их стоит перепроверить.

## Что заменяет мод

Граф `Audio/SFX/Season_Halloween/HalloweenSkullIdle_Cue` (VolumeMultiplier 0.5, все WavePlayer с `bLooping`):

```
ModulatorContinuous_0  (pitch по параметру Speed: 0.7 → 2.0)
└─ Mixer_3
   ├─ Mixer_1
   │  ├─ Modulator_0 (рандом pitch/volume 0.95–1.05) ─ IdleA
   │  └─ ModulatorContinuous_2 (volume по Speed: 1 → 10) ─ Modulator_1 ─ IdleB
   └─ Mixer_2
      ├─ Modulator_4 (pitch 1.7–1.8) ─ FireballB
      └─ Modulator_5 ─ FireballC
```

IdleA и IdleB играют **одновременно**, а pitch всего cue зависит от скорости черепа — у висящего черепа ~0.7×,
отсюда «замедленный» звук. Поэтому `build_mod.py`:

- кладёт трек только в **IdleA**, в **IdleB** — 1 с тишины (иначе две копии с разным рандомным pitch дают «флэнжер»);
- патчит cue на месте (размеры не меняются): `VolumeMultiplier` 0.5 → 1.0, pitch `ModulatorContinuous_0` 0.7/2.0 → 1.0/1.0,
  `Mixer_1.ChildNodes[0]` переключён с `Modulator_0` прямо на WavePlayer IdleA (без рандомного детюна).

Оригинальные волны:

| Что звучит | Путь (FSD/Content/…) | Длит. | Каналы | Громкость |
|---|---|---|---|---|
| Idle-звук черепа, вариант A | `Audio/SFX/Season_Halloween/HalloweenSkull/HalloweenSkullIdleA_1` | 20.5 с | 2 × 48 кГц, OGG | −20.1 LUFS |
| Idle-звук черепа, вариант B | `Audio/SFX/Season_Halloween/HalloweenSkull/HalloweenSkullIdleB_1` | 18.4 с | 2 × 48 кГц, OGG | −17.4 LUFS |

В том же cue есть ещё два звука огненных шаров босса (`Audio/SFX/Enemies/GlyphidDreadnaught/Fireball/SpiderTankBoss_FireballB_1`, `…FireballC_1`) —
они **не заменяются** (их используют другие враги), поэтому поверх трека слышен «огненный» слой. После патча cue он тоже
стал в 2 раза громче и без зависимости от скорости. Заглушить его можно, обнулив `Mixer_2.InputVolume` в cue.

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
