# Hand-drawn Canvas Integration

## Status

Approved architecture, deferred implementation.

Do not add the hand-drawn Canvas runtime to Milestone 01. The active Character Runtime Proof `SKIDS-005 -> SKIDS-013` remains the priority and must be visually accepted first.

## Purpose

Use `hand-drawn-canvas-animation` as a supplementary visual runtime for educational and editorial inserts, not as a second implementation of the persistent core-character runtime.

The intended roles are:

- local Character Runtime: persistent core characters, dialogue, gaze, blink, gestures, visemes, lip-sync and reusable acting;
- hand-drawn Canvas runtime: educational explainers, maps, diagrammatic inserts, doodles over real Sakhalin footage, stylized historical explanations and selected transitions;
- OpenMontage/Sakhalin Kids scene router: decides which runtime receives a scene;
- HyperFrames/Remotion/FFmpeg: downstream composition and delivery.

## Dependency direction

```text
approved episode / scene plan
        |
Sakhalin scene router
        |
        +--> character_dialogue / character_action
        |       |
        |       +--> local Character Runtime
        |
        +--> educational_graphic / map / selected transition
        |       |
        |       +--> hand-drawn Canvas adapter
        |
        +--> real_footage / location / cinematic paths
                |
                +--> existing Sakhalin/OpenMontage routing

approved scene outputs
        |
HyperFrames / Remotion / FFmpeg
        |
final derivatives
```

The Canvas layer must not become an owner of episode state, character identity, approvals or provider selection.

## Core invariant

Never use Canvas integration to create a parallel persistent-character implementation.

In particular, do not introduce:

```text
canvas_makar_renderer
canvas_leva_renderer
...
```

Core character identity remains defined by the existing data-driven Character Runtime:

```text
CharacterRenderer
  + CharacterSpec
  + RigProfile
  + PoseLibrary
  + Timeline
```

A Canvas scene may visually reference an already approved character asset or approved derivative when the scene brief requires it, but it must not silently regenerate or redefine that character.

## Approved scene types

The initial Canvas adapter may be considered for:

- `educational_graphic`;
- `map`;
- selected `transition`;
- selected `historical_reconstruction` when the creative path is explicitly hand-drawn rather than generative video;
- mixed real-footage + doodle inserts when source media rights/provenance are known.

It is not the default path for:

- `character_dialogue`;
- `character_action`;
- persistent character acting;
- Russian lip-sync;
- base character asset generation.

## Sakhalin visual modes

Future project-specific art direction may expose three controlled presets:

### sakhalin-sketch

Use for short educational explanations.

Characteristics:

- visible pencil/ink gestures;
- restrained paper texture;
- readable silhouettes;
- limited accent colours;
- deliberate held drawings and redrawn poses;
- no decorative frame-to-frame jitter without purpose.

### sakhalin-doodle

Use over owned/approved real Sakhalin photography or footage.

Characteristics:

- annotations attached to real scene geometry;
- arrows, circles, hand-written labels and simple character reactions;
- doodles must track their anchor objects;
- source media provenance remains attached to the output.

### sakhalin-map

Use for routes, geography and location context.

Characteristics:

- simplified Sakhalin silhouette;
- route drawing;
- location markers;
- restrained labels;
- camera movement only when it improves geographic understanding.

## Character-specific editorial roles

Canvas inserts should preserve the existing character functions:

- Makar initiates a question or hypothesis;
- Leva structures the explanation or mechanism;
- Tikhon frames safety and environmental risk;
- Anna reveals processes below the surface or inside marine systems;
- Antoshka connects place, travel, people and history.

These are editorial roles, not separate renderers.

## First pilot after SKIDS-013

After the Character Runtime Proof is visually accepted, run a bounded pilot:

`CANVAS-P01 — Lighthouse Educational Insert`

Target:

- 10–15 seconds;
- 16:9;
- topic: how lighthouse light reaches the horizon;
- Makar asks the question;
- Leva explains through a hand-drawn diagram;
- no paid AI-video generation;
- no new core-character identity generation.

Acceptance:

- visual style is recognizably part of Sakhalin Kids;
- diagram remains understandable at normal playback speed;
- any core-character appearance uses approved assets or approved derivatives;
- rerender is deterministic enough for the selected medium;
- output decodes successfully;
- integration does not alter Character Runtime contracts;
- scene router can select the Canvas path without screenplay-level provider binding.

## Implementation gate

Do not start `CANVAS-P01` until:

1. `SKIDS-013` is complete;
2. the Character Runtime visual proof is accepted;
3. the exact upstream Canvas skill/runtime revision is pinned;
4. license and source-media rules are reviewed;
5. the adapter boundary is defined without modifying core character contracts.

## Non-goals

The Canvas integration must not:

- replace OpenMontage orchestration;
- replace the local Character Runtime;
- own character identity or asset approval;
- add a second lip-sync system;
- trigger hidden text-to-video character generation;
- expand Milestone 01 scope;
- become a general-purpose UI animation dependency.

## Upstream

Candidate upstream:

`alesha-pro/tools/skills/hand-drawn-canvas-animation`

Pin an exact repository commit before implementation. Do not follow upstream `main` silently.
