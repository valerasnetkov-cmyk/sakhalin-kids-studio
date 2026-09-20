# Sakhalin Kids — Motion Contract

## 1. Purpose

SKIDS-005 defines renderer-agnostic, reusable motion contracts:

- `Pose` — reusable character state;
- `Action` — timed sequence of Pose references.

Schemas:

```text
schemas/sakhalin/pose.schema.json
schemas/sakhalin/action.schema.json
```

These are long-lived domain contracts, not production-run artifacts.

## 2. Pose

A Pose belongs to one `rig_profile` and contains at least one state component:

```yaml
version: "1.0"
id: point_right
rig_profile: fox_cartoon
state:
  parts:
    arm_right:
      rotation_deg: -42
  expression: curious
  gaze:
    direction: right
```

`state` may contain only `parts`, `expression`, and `gaze`.

Pose has no scene timing, character placement, renderer code, or asset paths.

## 3. PartState

`state.parts` is keyed by symbolic rig part IDs.

A part may define `variant`, `rotation_deg`, or both:

```yaml
eye_left:
  variant: closed
head:
  rotation_deg: -4
```

A PartState cannot be empty.

It does not contain coordinates, SVG paths, CSS, transform matrices, scale, opacity, layers, or asset paths.

Those concerns belong to character assets and the future resolver/renderer.

## 4. Expression and gaze

`state.expression` is a symbolic identifier such as `curious` or `thinking`.

Pose does not embed the expression implementation.

Reusable gaze is direction-only:

```text
left | center | right | up | down
```

Target-based gaze such as `look_at: leva` is a scene/runtime concern and is not part of Pose.

## 5. Mouth ownership

Pose cannot author a part named `mouth`.

The schema rejects `state.parts.mouth` through `propertyNames`.

Ownership is explicit:

```text
body / head / eyes / gesture / expression -> Pose + Action
mouth animation                           -> VisemeTimeline
```

VisemeTimeline is defined in SKIDS-006.

## 6. Action

Action is a reusable timed sequence of Pose references:

```yaml
version: "1.0"
id: point
rig_profile: fox_cartoon
phases:
  - name: anticipation
    duration_ms: 180
    pose: idle
  - name: move
    duration_ms: 320
    pose: point_right
  - name: hold
    duration_ms: 500
    pose: point_right
  - name: settle
    duration_ms: 260
    pose: idle
```

Each phase contains exactly `name`, `duration_ms`, and `pose`.

`duration_ms` is a positive integer.

Action contains no easing, scene timestamps, audio, visemes, character IDs, or renderer instructions.

## 7. Talk action

`talk` controls acting only: reusable body, head, gaze, and expression poses while dialogue is active.

It must not contain mouth shapes, phonemes, visemes, audio timestamps, or lip-sync metadata.

A future runtime may combine acting and VisemeTimeline without one overwriting the other.

## 8. Cross-document validation

JSON Schema validates document shape only.

A future resolver/compiler must verify that:

- `rig_profile` resolves;
- each Pose part exists in that RigProfile;
- each Action pose reference resolves;
- Action and referenced Pose use the same `rig_profile`;
- requested behavior matches rig capabilities.

These semantic checks are intentionally outside SKIDS-005.

## 9. Canonical motion data

SKIDS-005 is contract-only.

Do not create global `library/poses/` or `library/actions/` data yet.

Final motion values depend on approved character art, proportions, pivots, and readable motion ranges.

Makar and Leva fixtures are created with SKIDS-011 and SKIDS-012.

## 10. OpenMontage boundary

```text
Sakhalin Pose + Sakhalin Action + character assets
        |
        | future compiler / resolver
        v
OpenMontage pose_library / action_timeline
```

No adapter or compiler is implemented in SKIDS-005.

`Pose` and `Action` remain distinct lifecycle concepts from OpenMontage production artifacts.

## 11. Versioning

Current schema version is `1.0`.

Incompatible changes require a version bump and migration path. Existing motion data must not be silently reinterpreted.
