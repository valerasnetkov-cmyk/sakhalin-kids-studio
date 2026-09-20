# Sakhalin Kids Studio

AI-assisted production layer for a children's educational YouTube channel about Sakhalin, designed to run on top of OpenMontage.

## Status

Pre-scaffold / architecture stage. The first implementation target is a 10-15 second deterministic dialogue proof with Makar and Leva.

## Core cast

- Makar — fox, lead researcher.
- Leva — sea lion, calm partner and reasoning voice.
- Tikhon — bear cub, forest and safety.
- Anna — seal, sea and underwater world.
- Antoshka — seagull, traveler and story collector.

The core cast is closed by default. New persistent characters require an explicit project decision and configuration change.

## Architecture

This repository is a thin product layer for OpenMontage rather than a deep rewrite. The intended dependency direction is:

```text
OpenMontage Core
      ^
      |
Sakhalin Kids adapters
      ^
      |
Episodes / assets
```

Key documents:

- `CODEX_START.md` — first instructions for Codex.
- `docs/sakhalin/ARCHITECTURE.md` — system architecture.
- `docs/sakhalin/IMPLEMENTATION_PLAN.md` — milestones and acceptance criteria.
- `docs/sakhalin/CHARACTER_FORMAT.md` — reusable character contract.
- `docs/sakhalin/LIPSYNC.md` — Russian viseme/lip-sync design.
- `pipeline_defs/sakhalin-kids.yaml` — initial pipeline manifest draft.

## OpenMontage upstream

Canonical upstream:

```text
https://github.com/calesthio/OpenMontage.git
```

Reference baseline used for this bootstrap:

```text
08e2151fa02de28a5d6a312b3d575692bf147ad7
```

## First milestone

`SKIDS-001 -> SKIDS-013`: Character Runtime Proof.

Target scene:

```text
Макар: «Лёва, а почему море солёное?»
Лёва: «Хороший вопрос. Давайте разберёмся.»
```

Acceptance focuses on stable identity, two rig profiles, gaze, blink, gesture, Russian viseme timeline, audio sync, deterministic reuse, QA, and final MP4 output.

## Security and cost rules

- Never commit `.env`, provider credentials, private voice IDs, or tokens.
- Model output is untrusted data and cannot directly authorize shell, filesystem, network, or provider operations.
- Paid provider calls must pass explicit budget checks.
- No silent fallback from local core-character animation to regenerated text-to-video characters.
- Keep authored source files at or below 400 physical lines.
