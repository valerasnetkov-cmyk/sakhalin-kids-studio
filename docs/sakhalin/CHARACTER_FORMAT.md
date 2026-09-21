# Sakhalin Kids — Character Format

## 1. Цель

Character format должен позволять:

- хранить героя независимо от конкретного выпуска;
- не перегенерировать базовый дизайн;
- использовать героя в разных сценах;
- подключать разные render runtimes;
- проверять continuity автоматически.

## 2. Directory contract

```text
library/characters/<character-id>/
  character.yaml
  art/
    front.svg
    three-quarter.svg
    side.svg
    back.svg
  parts/
  face/
  mouth/
  expressions/
  poses/
  actions/
  props/
  reference_frames/
```

Не все views обязательны на MVP.

`character.yaml` определяет required views.

## 3. Core character IDs

Canonical identity/species/role reference: `docs/sakhalin/TEAM_CANON.md`.


```text
makar
leva
tikhon
anna
antoshka
```

IDs являются стабильными.

Display names могут локализоваться, IDs — нет.

## 4. Character definition

Пример:

```yaml
version: "1.0"

id: makar
display_name: "Макар"

species: fox
rig_profile: fox_cartoon

role: lead_researcher

story:
  primary_question: "Почему?"
  catchphrase: "А давайте проверим!"

visual:
  palette_locked: true
  proportions_locked: true
  wardrobe_locked: true
  base_regeneration_allowed: false

required_views:
  - front
  - three_quarter
  - side

required_expressions:
  - neutral
  - happy
  - curious
  - thinking
  - surprised
  - worried

required_actions:
  - idle
  - blink
  - look
  - point
  - inspect
  - think
  - talk
  - wave

props:
  required:
    - backpack
  optional:
    - notebook
    - binoculars

voice:
  profile: makar

continuity:
  identity_locked: true
  redesign_requires_approval: true
```

## 5. Visual lock

После утверждения production character:

```yaml
visual:
  base_regeneration_allowed: false
```

Запрещено автоматически:

- менять species;
- менять цвет;
- менять пропорции;
- менять глаза;
- менять signature wardrobe;
- менять signature props;
- заменять character art на новую AI-generation без отдельного approval.

## 6. Rig profile

Character не должен содержать renderer implementation.

Он только ссылается:

```yaml
rig_profile: fox_cartoon
```

Rig profile определяет structure.

Пример:

```yaml
id: fox_cartoon

parts:
  required:
    - body
    - head
    - eye_left
    - eye_right
    - pupil_left
    - pupil_right
    - mouth
    - arm_left
    - arm_right
    - leg_left
    - leg_right
    - tail

capabilities:
  blink: true
  gaze: true
  mouth_visemes: true
  head_turn: true
  arm_gestures: true
  tail_motion: true
```

## 7. Expressions

Expression является декларативным состоянием.

Пример:

```yaml
id: curious

face:
  eyebrows: raised_soft
  eyes: wide

head:
  rotation: -4

body:
  lean: 0.03
```

Expression не должен содержать произвольный JS.

## 8. Pose and Action

Pose и Action определены отдельным motion-domain контрактом.

См. `docs/sakhalin/MOTION_CONTRACT.md`.

Ключевая граница:

- Pose хранит reusable state;
- Action хранит timed sequence ссылок на Pose;
- mouth animation не принадлежит Pose/Action и определяется через VisemeTimeline;
- renderer/OpenMontage mapping выполняется будущим resolver/compiler.

## 9. Mouth set

Все production characters должны поддерживать единые semantic viseme IDs:

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

Character art для viseme отличается, semantic IDs одинаковы.

## 10. Voice profile reference

В character definition:

```yaml
voice:
  profile: makar
```

В отдельном voice profile:

```yaml
character_id: makar

performance:
  energy: 0.78
  tempo: 1.04
  pitch: medium_high
  curiosity: high

provider:
  preferred: google
  fallback:
    - openai
    - elevenlabs

secret_refs:
  voice_id_env: MAKAR_VOICE_ID
```

Нельзя хранить secret value.

## 11. Character scale

Нужно зафиксировать относительный scale персонажей.

Пример:

```yaml
stage_scale:
  makar: 1.00
  leva: 1.18
  tikhon: 1.15
  anna: 0.92
  antoshka: 0.82
```

Точные значения должны быть утверждены после финальных model sheets.

## 12. Cast validation

Episode cast:

```yaml
cast:
  - makar
  - leva
```

Validator должен отклонять unknown core IDs.

Для временного героя:

```yaml
guest_characters:
  - id: lighthouse_keeper
    persistence: episode_only
```

Guest character не добавляется автоматически в core library.

## 13. Scene character state

Scene plan может задавать:

```yaml
character_state:
  makar:
    position: left
    expression: curious
    gaze: leva
    action: point
```

Runtime связывает scene state с библиотекой assets.

## 14. Character QA reference frames

Для каждого production hero:

```text
reference_frames/
  front.png
  three-quarter.png
  side.png
  happy.png
  surprised.png
  talking.png
```

QA не должен полагаться только на perceptual similarity score.

Нужны структурные checks:

- parts присутствуют;
- palette соответствует lock;
- required props присутствуют;
- scale не выходит за пределы;
- wrong character ID невозможен.

## 15. MVP profiles

Milestone 01 поддерживает:

### Макар

`fox_cartoon`

### Лёва

`sea_lion_cartoon`

Остальные профили добавляются после успешного proof.

## 16. Data migration

Character format должен иметь:

```yaml
version: "1.0"
```

Любое несовместимое изменение schema требует migration path.

Нельзя silently reinterpret старые character assets.
