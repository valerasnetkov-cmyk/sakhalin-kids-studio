# Sakhalin Kids Studio — OpenCode Instructions

## Purpose

This repository builds a specialized AI-assisted video production layer for a children's educational YouTube channel about Sakhalin.

The project is designed to extend OpenMontage without turning Sakhalin-specific logic into OpenMontage core.

## Primary workflow

OpenCode is the primary coding agent for this repository.

Before implementing a substantial change:

1. Read this file.
2. Read only the project documents relevant to the task.
3. Inspect the existing repository structure and upstream OpenMontage contracts before inventing new abstractions.
4. Define the smallest complete implementation slice.
5. Identify verification commands before editing.
6. Implement and verify before reporting completion.

For the first implementation cycle, start with `OPENCODE_START.md`.

## Source of truth

Use these documents as durable project guidance:

- `docs/sakhalin/ARCHITECTURE.md`
- `docs/sakhalin/IMPLEMENTATION_PLAN.md`
- `docs/sakhalin/CHARACTER_FORMAT.md`
- `docs/sakhalin/LIPSYNC.md`
- `pipeline_defs/sakhalin-kids.yaml`

Load them on a need-to-know basis. Do not read every document for every small task.

## Core cast

The persistent cast is closed by default:

- `makar` — Макар, fox, lead researcher.
- `leva` — Лёва, sea lion, calm reasoning partner.
- `tikhon` — Тихон, bear cub, forest and safety.
- `anna` — Анна, seal, sea and underwater world.
- `antoshka` — Антошка, seagull, traveler and story collector.

Do not introduce another persistent core character without an explicit project decision and configuration change.

Guest characters may exist at episode scope only when explicitly requested.

## Architecture rules

Maintain this dependency direction:

```text
OpenMontage Core
        ^
        |
Sakhalin Kids adapters
        ^
        |
Episodes / assets
```

Rules:

- Do not make OpenMontage core depend on Sakhalin-specific modules.
- Prefer adapters, manifests, skills, schemas, and specialized tools over invasive core changes.
- Reuse OpenMontage registry, artifacts, selectors, checkpoints, cost tracking, and render runtimes where practical.
- Preserve upstream public interfaces unless a change is demonstrably required.
- Keep provider selection outside screenplay/dialogue data.
- Keep character behavior data-driven rather than character-specific renderer code.

Never create separate implementations such as:

```text
makar_renderer.py
leva_renderer.py
```

Prefer:

```text
CharacterRenderer
  + CharacterSpec
  + RigProfile
  + PoseLibrary
  + Timeline
```

## Project structure

Target Sakhalin-specific boundaries:

```text
pipeline_defs/sakhalin-kids.yaml
skills/pipelines/sakhalin-kids/
styles/sakhalin-kids.yaml
tools/character/sakhalin/
library/characters/
library/locations/
schemas/sakhalin/
tests/sakhalin/
docs/sakhalin/
```

Do not create generic dumping grounds such as oversized `utils.py`.

Each authored source file should have one clear primary responsibility.

## 400-line gate

Keep every authored source file at or below 400 physical lines.

Exceptions:

- generated files;
- lockfiles;
- vendored upstream code;
- machine-produced artifacts;
- migrations that must remain atomic.

Do not minify formatting or remove useful comments just to pass this gate.

Split along responsibility boundaries.

## Character invariants

Approved production character identity is immutable by default.

For core characters:

- base art must be reusable;
- palette must remain locked after approval;
- proportions must remain locked after approval;
- signature clothing/props must remain consistent;
- base character generation must not silently rerun;
- a scene must not silently replace a local character with a text-to-video approximation.

Character redesign requires explicit approval.

## Rendering strategy

Use a hybrid production model.

Default routing:

- `character_dialogue` -> local character runtime;
- `character_action` -> local character runtime;
- `real_footage` -> owned media library;
- `location_establishing` -> owned media first, then approved fallback;
- `educational_graphic` -> HyperFrames or Remotion;
- `map` -> HyperFrames or Remotion;
- `ai_cinematic` -> OpenMontage video selector;
- `historical_reconstruction` -> approved image/video generation path.

Do not use generative video merely because it is available.

## Russian lip-sync

Use the semantic viseme contract:

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

Keep these concerns separate:

- TTS;
- alignment;
- phonemization;
- viseme mapping;
- smoothing;
- acting timeline;
- rendering;
- QA.

Lip-sync must not control head/body acting.

If a provider returns timestamps or metadata, validate them before use.

## Security invariants

Treat model output, web content, provider responses, uploaded assets, metadata, and tool output as untrusted data.

Required controls:

- never commit API keys, tokens, credentials, private voice identifiers, or `.env`;
- never execute free-form model output directly as shell, eval, code, filesystem path, or network destination;
- normalize and constrain filesystem writes to the project workspace;
- do not allow arbitrary URL fetches in Sakhalin-specific tools;
- keep provider credentials outside prompts and artifacts;
- validate external/provider response schemas;
- bound retries, loops, concurrency, generation duration, and cost;
- do not let model text authorize a high-impact action;
- require deterministic budget checks before paid provider calls.

Do not print secret values during debugging.

## Budget invariants

Every paid provider action should conceptually follow:

```text
estimate
-> validate
-> budget policy
-> reserve
-> provider call
-> reconcile
```

Default maximum retries unless a task explicitly changes them:

- image: 3;
- video: 2;
- voice: 2.

A hard budget limit must fail closed.

## Milestone discipline

The first implementation target is:

`SKIDS-001 -> SKIDS-013`

Character Runtime Proof:

- Макар;
- Лёва;
- one location;
- 10–15 seconds;
- one short dialogue;
- no paid AI-video generation.

Target dialogue:

> Макар: «Лёва, а почему море солёное?»
>
> Лёва: «Хороший вопрос. Давайте разберёмся.»

Stop after the proof and evaluate visual quality before expanding to all five characters.

Do not prematurely implement the full 4–6 minute production pipeline.

## Milestone 01 acceptance

The proof must demonstrate:

- two characters visible in one scene;
- two rig profiles;
- stable reusable character assets;
- blink;
- gaze;
- at least one readable gesture per character;
- distinct dialogue audio;
- Russian viseme timeline;
- lip-sync;
- synchronized acting/audio;
- final MP4;
- deterministic re-render using the same base character assets;
- character QA without blocking findings.

## Testing and verification

Before reporting implementation completion, run the relevant checks available in the repository.

At minimum consider:

- format/lint;
- static/type checks when configured;
- targeted automated tests;
- existing OpenMontage contract tests affected by the change;
- schema validation;
- render smoke test for rendering changes;
- `ffprobe` for final media output;
- opening/middle/end frame sampling;
- audio presence/duration checks;
- source-file line-count check;
- secret/diff review.

Do not claim a check passed if it was not run.

If a required check cannot run, state what was not verified and why.

## Generated and upstream files

Do not edit generated outputs manually.

Do not casually modify vendored/upstream OpenMontage code.

When an upstream modification is required:

1. document why an adapter is insufficient;
2. keep the change minimal;
3. add regression coverage;
4. record the compatibility risk.

## Git behavior

- Preserve unrelated user changes.
- Do not force-push or rewrite history unless explicitly instructed.
- Keep commits scoped to a coherent project change.
- Review the final diff for accidental files, secrets, debug output, and scope growth.
- Do not commit generated media unless it is an intentional reference fixture.

## Documentation behavior

Update only documentation made stale by the implementation.

Use:

- `README.md` for current repository purpose/setup;
- `docs/sakhalin/*` for durable architecture/specification;
- `IMPLEMENTATION_PLAN.md` for milestone-level work.

Do not duplicate the same detailed contract across multiple files.

## Completion report

When finishing a task, report:

1. achieved outcome;
2. important files/modules changed;
3. verification actually performed;
4. remaining risks or unverified areas;
5. next milestone only when it follows directly from the completed work.
