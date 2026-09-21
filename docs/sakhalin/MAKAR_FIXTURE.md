# Sakhalin Kids — Makar Fixture (SKIDS-011)

## Purpose

Technical PROOF FIXTURE for the first reusable structured Makar character bundle.
This validates rig/runtime behavior only. It is NOT final approved production artwork.

SKIDS-011 fixture validates rig/runtime behavior only.
It is not final approved production artwork.

## File structure

```text
library/characters/makar/
  character.yaml          # CharacterSpec
  art/
    front.svg             # Structured rigged SVG
  poses/
    idle.yaml             # Default idle pose
    blink_closed.yaml     # Eyes closed (blink)
    look_left.yaml        # Gaze left
    look_right.yaml       # Gaze right
    point.yaml            # Pointing gesture
    talk.yaml             # Talk body acting
    curious.yaml          # Curious expression
  actions/
    idle.yaml             # Idle hold (1000ms)
    blink.yaml            # Blink cycle (300ms)
    look.yaml             # Look left and return (800ms)
    point.yaml            # Point gesture (1260ms)
    talk.yaml             # Talk acting (1000ms)
  reference_frames/
    (deferred)
```

## Rig profile

`fox_cartoon` — 12 required parts:

```text
body, head, eye_left, eye_right, pupil_left, pupil_right,
mouth, arm_left, arm_right, leg_left, leg_right, tail
```

## Expressions

- `neutral` — default state
- `curious` — raised eyebrows, head tilt

## Poses

| Pose | Parts | Expression | Gaze |
|---|---|---|---|
| idle | — | neutral | center |
| blink_closed | eye_left=closed, eye_right=closed | — | — |
| look_left | pupil_left=left, pupil_right=left | — | left |
| look_right | pupil_left=right, pupil_right=right | — | right |
| point | arm_right=rotation_deg(-45) | curious | right |
| talk | head=rotation_deg(-3) | — | — |
| curious | head=rotation_deg(-5) | curious | — |

No pose controls mouth. Mouth animation is VisemeTimeline only.

## Actions

| Action | Phases | Total duration |
|---|---|---|
| idle | hold (1000ms) | 1000ms |
| blink | open (100ms) → closed (80ms) → open (120ms) | 300ms |
| look | start (150ms) → hold (500ms) → return (150ms) | 800ms |
| point | anticipation (180ms) → move (320ms) → hold (500ms) → settle (260ms) | 1260ms |
| talk | start (200ms) → speak (600ms) → end (200ms) | 1000ms |

## Visemes

All 10 semantic visemes present in SVG mouth part:

```text
REST, A, E, O, U, MBP, FV, SH, L, S
```

No duplicates. Mouth is exclusively controlled by VisemeTimeline.

## Gaze

All 5 directions supported via pupil variants:

```text
left, center, right, up, down
```

## Blink

Structurally real blink support:
- `eye_left` and `eye_right` parts have `open` and `closed` variants
- `blink_closed` pose activates `closed` variant
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

The Makar SVG is fully compatible with SvgSceneRenderer (SKIDS-008):
- idle render: deterministic
- blink state: observable via eye variant change
- gaze state: observable via pupil variant change
- point gesture: observable via arm rotation
- viseme state: observable via mouth viseme switching

## Artistic QA boundary

This fixture validates rig/runtime structural behavior.

**NOT validated:**
- Final 3D-stylized character design
- Artistic proportions and silhouette quality
- Approved production palette fidelity
- Prop visual verification
- Scale consistency with other characters

Artistic identity remains `not_verified` until approved production artwork is available.
