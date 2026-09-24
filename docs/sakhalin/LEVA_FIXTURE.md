# Sakhalin Kids — Leva Fixture (SKIDS-012)

## Purpose

Technical PROOF FIXTURE for the first reusable structured Leva character bundle.
This validates rig/runtime behavior only. It is NOT final approved production artwork.

SKIDS-012 fixture validates rig/runtime behavior only.
It is not final approved production artwork.

## File structure

```text
library/characters/leva/
  character.yaml          # CharacterSpec
  art/
    front.svg             # Structured rigged SVG
  poses/
    idle.yaml             # Default calm idle
    blink_closed.yaml     # Eyes closed
    look_left.yaml        # Gaze left
    look_right.yaml       # Gaze right
    think.yaml            # Contemplative pose
    talk.yaml             # Talk body acting
  actions/
    idle.yaml             # Calm idle hold (1000ms)
    blink.yaml            # Blink cycle (300ms)
    look.yaml             # Look and return (800ms)
    think.yaml            # Think gesture (1200ms)
    talk.yaml             # Talk acting (1000ms)
```

## Rig profile

`sea_lion_cartoon` — 9 required parts:

```text
body, head, eye_left, eye_right, pupil_left, pupil_right,
mouth, flipper_left, flipper_right
```

Note: sea_lion uses flippers (not arms/legs/tail).
`flipper_gestures: true`, `arm_gestures: false`, `tail_motion: false`.

## Visual identity

- sea lion / sivuch silhouette
- rounded, calm body proportions
- grey-blue palette (`#6B7B8D`, `#B0C4D8`)
- marine/exploration scarf accent (`#E85D3A`)
- whisker pads (species特征)
- small ear nubs
- calm, friendly expression
- clearly different silhouette from Makar (fox)

## Eye / pupil separation

- `eye_left` / `eye_right` `open` variants draw only the sclera (white eye shape).
- Pupil belongs exclusively to `pupil_left` / `pupil_right` parts.
- Pupil parts define 6 variants: `left`, `center`, `right`, `up`, `down`, `hidden`.
- `hidden` renders an empty layer — used when the eye is closed.

## Expressions

- `neutral` — default calm state
- `thinking` — raised inner eyebrows, contemplative, chin tuck

## Poses

| Pose | Parts | Expression | Gaze |
|---|---|---|---|
| idle | pupil_left=center, pupil_right=center | neutral | center |
| blink_closed | eye_left=closed, eye_right=closed, pupil_left=hidden, pupil_right=hidden | — | — |
| look_left | pupil_left=left, pupil_right=left | — | left |
| look_right | pupil_left=right, pupil_right=right | — | right |
| think | head=rotation_deg(-4), pupil_left=up, pupil_right=up | thinking | up |
| talk | head=rotation_deg(-2) | — | — |

Gaze and pupils stay in sync: every pose that declares `gaze.direction` also sets
`pupil_left` / `pupil_right` variants to the same direction. When the eye is closed,
pupils switch to `hidden`.

Motion style: calmer than Makar. Smaller head changes, slower readable gestures.

No pose controls mouth. Mouth animation is VisemeTimeline only.

## Actions

| Action | Phases | Total duration |
|---|---|---|
| idle | hold (1000ms) | 1000ms |
| blink | open (100ms) → closed (80ms) → open (120ms) | 300ms |
| look | start (150ms) → hold (500ms) → return (150ms) | 800ms |
| think | settle (200ms) → contemplate (800ms) → return (200ms) | 1200ms |
| talk | start (200ms) → speak (600ms) → end (200ms) | 1000ms |

Think action is intentionally longer than other gestures — Leva takes time to reason.

## Visemes

All 10 semantic visemes present in SVG mouth part:

```text
REST, A, E, O, U, MBP, FV, SH, L, S
```

No duplicates. Mouth is exclusively controlled by VisemeTimeline.

## Gaze

All 5 directions supported as pupil variants and gaze layers:

```text
left, center, right, up, down
```

Additional pupil variant `hidden` covers closed-eye states.

Every pose with a declared gaze synchronizes pupil variants to that direction.

## Blink

Structurally real blink support:
- `eye_left` and `eye_right` parts have `open` and `closed` variants
- `blink_closed` pose activates `closed` variants and `hidden` pupils
- `blink` action cycles open → closed → open
- Blink in `required_actions` passes SKIDS-010 hardened blink rule

## CharacterReviewer result

```json
{
  "status": "pass",
  "findings": [],
  "checks": {
    "schema_valid": true,
    "canon_valid": true,
    "rig_valid": true,
    "poses_defined": true,
    "actions_timed": true
  },
  "metadata": {
    "visual_reference_status": "not_verified",
    "prop_visual_verification": "not_verified",
    "scale_check": "not_verified"
  }
}
```

Structural PASS is NOT final artistic approval.

## Renderer compatibility

The Leva SVG is fully compatible with SvgSceneRenderer (SKIDS-008), verified by
state-level assertions on the rendered frame (not just inequality):
- idle render: deterministic; eyes `open`, pupils `center`, expression `neutral`, gaze `center`, viseme `REST`
- blink state: eyes `closed`, pupils `hidden`
- gaze state: pupil variants and gaze layer match the pose direction
- think gesture: head `rotate(-4)`, expression `thinking`, gaze `up`, pupils `up`
- viseme state: selected `data-viseme` matches the timeline viseme

## Artistic QA boundary

This fixture validates rig/runtime structural behavior.

**NOT validated:**
- Final production character design
- Artistic proportions and silhouette quality
- Approved production palette fidelity
- Prop visual verification
- Scale consistency with other characters

Artistic identity remains `not_verified` until approved production artwork is available.
