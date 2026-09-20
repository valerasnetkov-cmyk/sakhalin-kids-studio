# Sakhalin Kids Studio

AI-assisted production layer for a children's educational YouTube channel about Sakhalin, designed to run on top of OpenMontage. OpenCode is the primary coding agent for this repository.

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

- `AGENTS.md` — persistent project instructions for OpenCode.\n- `OPENCODE_START.md` — first-session implementation brief for OpenCode.\n- `CODEX_START.md` — legacy bootstrap brief retained for history.
- `docs/sakhalin/ARCHITECTURE.md` — system architecture.
- `docs/sakhalin/IMPLEMENTATION_PLAN.md` — milestones and acceptance criteria.
- `docs/sakhalin/CHARACTER_FORMAT.md` — reusable character contract.
- `docs/sakhalin/LIPSYNC.md` — Russian viseme/lip-sync design.
- `pipeline_defs/sakhalin-kids.yaml` — initial pipeline manifest draft.
- `docs/sakhalin/CONTROL_PLANE.md` — approved future Hermes control-plane architecture.
- `docs/sakhalin/HARNESS_INTEGRATION.md` — approved future DeepSeek Harness research/review/QA architecture.

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

## OpenCode workflow

Use OpenCode as the primary development workflow.

Before substantial implementation:

1. Read `AGENTS.md`.
2. Read `OPENCODE_START.md` for the current bootstrap cycle.
3. Load only the relevant durable docs under `docs/sakhalin/`.
4. Implement the smallest complete SKIDS slice.
5. Run the available verification gates before reporting completion.

The first implementation cycle remains `SKIDS-001 -> SKIDS-013`.

## Future operator and agent layers

After the first Character Runtime proof is accepted:

- Hermes is planned as the operator / Telegram control plane through a narrow MCP/API surface.
- OpenMontage remains the single owner of production workflow state.
- DeepSeek Harness is planned only for bounded cognitive workflows such as research, script review, factual QA, and production QA.
- These layers must not be implemented during `SKIDS-001 -> SKIDS-013`.
