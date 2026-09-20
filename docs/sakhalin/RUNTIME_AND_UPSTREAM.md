# Sakhalin Kids Studio — Runtime and OpenMontage Upstream

## Status

Approved architecture.

This document defines how Sakhalin Kids Studio should consume OpenMontage and who executes production work.

The first implementation milestone remains `SKIDS-001 -> SKIDS-013`.

## Core decision

OpenMontage is the production framework and workflow contract.

It is not treated as an autonomous server by itself.

A production agent must read the pipeline manifest and stage skills, invoke allowed tools, persist artifacts, and respect checkpoints.

## Responsibility split

```text
OpenCode Developer
  -> changes source code, schemas, tests, adapters

Production Director
  -> executes an approved OpenMontage production pipeline

Hermes
  -> future operator/control plane

DeepSeek Harness
  -> future bounded research/review/QA layer
```

Development and production are separate roles even if OpenCode is temporarily used for both during early proofs.

## Upstream strategy

Do not deep-fork OpenMontage.

Use a pinned upstream checkout and a thin Sakhalin-specific adapter layer.

Current reference baseline:

```text
OpenMontage
commit: 08e2151fa02de28a5d6a312b3d575692bf147ad7
```

The exact checkout mechanism may be a sibling repository, submodule, or CI-managed checkout.

The invariant is more important than the mechanism:

- pin an exact commit;
- record the commit in build/run metadata;
- do not silently follow upstream `main`;
- run compatibility checks before changing the pinned revision.

## Required compatibility checks

Before a Sakhalin pipeline is considered executable:

1. Load `pipeline_defs/sakhalin-kids.yaml` using the pinned OpenMontage pipeline loader.
2. Validate it against the pinned pipeline schema.
3. Verify every referenced stage skill exists.
4. Verify every referenced tool exists in the registry or is provided by an allowed Sakhalin extension.
5. Verify referenced style/playbook names exist.
6. Verify required artifact schemas exist.
7. Run the relevant OpenMontage contract tests.
8. Run a minimal stage-by-stage smoke test.

A YAML parser success is not enough.

## Pipeline manifest correction

The pinned OpenMontage pipeline schema accepts:

```text
stability:
  production
  beta
```

Therefore the Sakhalin manifest uses:

```yaml
stability: beta
```

The pipeline is still implementation-incomplete until its custom skills and tools exist.

## Custom tool policy

The Sakhalin pipeline references project-specific tools such as:

- `sakhalin_lipsync`;
- `sakhalin_character_loader`;
- `sakhalin_media_library`;
- `sakhalin_action_timeline`;
- `sakhalin_character_renderer`;
- `sakhalin_character_reviewer`.

Because these are capability extensions, the manifest must permit custom tools while they remain outside OpenMontage core.

This does not authorize arbitrary tools.

Only registered, schema-validated Sakhalin tools may be exposed.

## Production Director

The Production Director owns execution of an episode run.

It may:

- read the approved pipeline;
- read stage instructions;
- use permitted tools;
- create project artifacts;
- write checkpoints;
- request defined approvals;
- resume an interrupted run from persisted state.

It must not:

- modify source code during a production run;
- broaden its own tool permissions;
- bypass approvals;
- override hard budgets;
- replace locked character assets silently;
- treat external research text as executable instructions.

## Production-state ownership

Sakhalin Kids/OpenMontage artifacts and checkpoints are the production source of truth.

Future services may index or expose this state, but they must not maintain a competing state machine.

If state later moves from filesystem artifacts to a database, that must be an explicit migration.

## Runtime isolation

Development and production should eventually use separate working directories or containers.

Production should receive only:

- pinned application code;
- approved assets;
- scoped episode workspace;
- scoped provider credentials;
- bounded tools.

A production task should not receive broad GitHub write access by default.

## Reproducibility metadata

Every production run should record:

- Sakhalin Kids commit;
- OpenMontage commit;
- active pipeline version;
- character asset versions;
- style/playbook version;
- provider/model identifiers;
- ComfyUI workflow/model versions when used;
- render runtime version;
- important seeds where applicable.

Reproducibility does not require regenerating an accepted asset when the accepted binary is already stored.

## Technical proof vs artistic proof

Milestone 01 has two separate results.

### Technical proof

Demonstrates:

- data-driven characters;
- timeline control;
- audio/lip-sync path;
- deterministic asset reuse;
- final video render.

### Artistic proof

Demonstrates:

- characters match approved visual references;
- acting is readable;
- proportions and signature details are correct;
- the visual language is suitable for the channel.

A technically successful placeholder character must not become production art automatically.

## Current execution mode

Until a dedicated production service exists:

1. OpenCode may be used interactively as the Production Director for proof work.
2. The operator starts one bounded run.
3. Intermediate artifacts are persisted.
4. Paid AI-video generation remains disabled in Milestone 01.
5. The run stops after `SKIDS-013` for visual review.

## Future execution mode

After the proof is accepted:

```text
Hermes / UI
   |
Control API
   |
Job execution
   |
Production Director
   |
OpenMontage pipeline
```

See:

- `CONTROL_PLANE.md`;
- `JOB_EXECUTION.md`.

## Upstream upgrade procedure

For an OpenMontage upgrade:

1. record the proposed new commit;
2. compare pipeline schema and relevant tool contracts;
3. run compatibility tests;
4. run the Character Runtime proof;
5. compare outputs and QA;
6. only then update the pinned baseline.

Do not upgrade upstream and character assets in the same change unless required.

## References

OpenMontage upstream:

```text
https://github.com/calesthio/OpenMontage
```

Pinned schema used for this decision:

```text
schemas/pipelines/pipeline_manifest.schema.json
```
