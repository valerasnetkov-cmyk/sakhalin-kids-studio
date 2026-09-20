# Sakhalin Kids — Russian Lip Sync

## 1. Цель

Не стремиться к фотореалистичной артикуляции.

Нужна читаемая, приятная и стабильная мультяшная речь, синхронизированная с русским TTS.

## 2. Pipeline

```text
dialogue text
    |
TTS
    |
audio.wav
    |
timestamps/alignment
    |
Russian phonemization
    |
phoneme timeline
    |
viseme mapping
    |
smoothing
    |
mouth timeline
    |
acting timeline merge
    |
render
```

## 3. Separation of concerns

Модули должны быть разделены:

```text
tts_adapter
alignment_adapter
phonemizer
viseme_mapper
viseme_smoother
timeline_merger
qa
```

TTS provider не должен содержать Sakhalin-specific character logic.

## 4. Semantic viseme set

MVP:

```text
REST
A
E
O
U
MBP
FV
SH
L
S
```

Рекомендованное приблизительное соответствие:

| Viseme | Русские звуки |
|---|---|
| A | а, я |
| E | э, е, и, ы |
| O | о, ё |
| U | у, ю |
| MBP | м, б, п |
| FV | ф, в |
| SH | ш, ж, щ, ч |
| L | л, р |
| S | с, з, ц, т, д |
| REST | пауза |

Это animation mapping, а не лингвистическая фонетическая модель.

## 5. Domain contract: VisemeTimeline

Renderer-agnostic mouth-only domain contract:

```text
schemas/sakhalin/viseme_timeline.schema.json
$sid: sakhalin/viseme_timeline
```

`VisemeTimeline` is a long-lived domain contract, not a production-run artifact.

Root fields: `version`, `id`, `duration_ms`, `cues`.

Each cue contains `start_ms` (inclusive), `end_ms` (exclusive), and `viseme`.

Cue interval convention: `[start_ms, end_ms)`.

`duration_ms` is local to the associated utterance, not a scene timestamp.

`VisemeTimeline` does not contain: `character_id`, `rig_profile`, `audio_path`, `scene_id`, `provider`, `fps`, `renderer`, or any body/head/gaze/expression fields.

See: `docs/sakhalin/MOTION_CONTRACT.md` for ownership boundaries.

## 6. MVP alignment

Первый вариант может использовать:

1. TTS word timestamps, если provider их возвращает;
2. phonemization текста;
3. распределение phoneme duration внутри word interval;
4. smoothing.

Если TTS не возвращает word timestamps, допускается отдельный alignment adapter.

## 7. Forced alignment

Не делать обязательным для Milestone 01.

Подключать после video proof, если approximate alignment заметно ухудшает качество.

Интерфейс должен позволять заменить aligner без изменения renderer.

## 8. Smoothing rules

### Minimum duration

Целевой минимум:

```text
70–100 ms
```

Слишком короткие viseme events объединяются.

### Duplicate collapse

```text
A A A -> A
```

### Pause

Между словами при достаточной паузе:

```text
REST
```

### Look-ahead

Runtime может слегка anticipatory переключать рот перед акустическим onset, но это должно быть ограничено и тестируемо.

### No chatter

Не переключать mouth asset на каждой краткой фонеме, если результат визуально дрожит.

## 9. Timeline composition

Lip-sync не заменяет acting.

Финальный character timeline объединяет:

```text
body
head
eyes
eyebrows
arms
tail/wings
mouth
```

Mouth track не должен менять head/body state.

## 10. Dialogue manifest

Пример:

```yaml
scene_id: scene_01

lines:
  - id: line_001
    character_id: makar
    text: "Лёва, а почему море солёное?"
    voice_profile: makar

    acting:
      emotion: curious
      gaze: leva
      gesture: point_to_sea

  - id: line_002
    character_id: leva
    text: "Хороший вопрос. Давайте разберёмся."
    voice_profile: leva

    acting:
      emotion: thoughtful
      gaze: makar
```

TTS получает только текст и performance settings.

Renderer получает audio + visemes + acting.

## 11. Voice rules

Каждый core hero имеет стабильный voice profile.

Не клонировать голос реального ребёнка без отдельного правового и этического решения.

Для production предпочтительны специально созданные синтетические персонажные голоса.

## 12. Provider abstraction

Использовать существующий OpenMontage `tts_selector`.

Sakhalin layer задаёт:

- desired performance;
- language;
- voice profile;
- timing requirements.

Он не должен напрямую вызывать конкретный cloud endpoint.

## 13. QA checks

Минимум:

- audio asset существует;
- duration > 0;
- viseme timeline отсортирован;
- event timestamps в пределах audio duration;
- unknown viseme запрещён;
- character поддерживает требуемый mouth set;
- long silence содержит REST;
- events не имеют отрицательной duration;
- нет excessive events/sec.

## 14. Drift target

Для MVP использовать ориентир:

```text
audio/video lip-sync error <= ~150 ms
```

Это target для проверки, а не абсолютная гарантия качества.

Финальная оценка обязательно включает visual review.

## 15. Performance

Кешировать результаты:

```text
hash(text + voice profile + TTS settings)
 -> audio
 -> alignment
 -> viseme timeline
```

Повторный render не должен повторно оплачивать TTS без причины.

## 16. Security

- audio filenames не строятся напрямую из model output;
- output path только внутри project workspace;
- provider credentials не входят в dialogue manifest;
- third-party timestamps валидируются;
- malformed provider output fail closed;
- retries ограничены;
- стоимость TTS учитывается cost tracker.

## 17. Milestone 01 fallback

Если natural TTS timestamps недоступны:

- использовать локальную тестовую дорожку;
- вручную создать fixture word timings;
- доказать renderer и viseme engine;
- provider integration вынести в Milestone 02.

Главное в Milestone 01 — доказать character runtime, а не конкретного TTS-провайдера.
