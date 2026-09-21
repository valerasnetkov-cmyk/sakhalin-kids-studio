# Sakhalin Kids Studio — Hypit Integration

## Status

Approved candidate architecture.

This is a documentation-only decision. Hypit is not a current runtime dependency and must not enter Milestone 01.

A sandbox pilot may begin only after the Character Runtime Proof `SKIDS-001 -> SKIDS-013` is visually accepted. Production adoption is a separate decision gate and should not occur before episode/scene contracts are stable.

## Objective

Evaluate Hypit as an optional semantic-composition and derivative-production adapter for Sakhalin Kids Studio.

The intended value is not mass cloning of viral videos. The intended value is to automate repeatable video grammar around our own approved scripts, characters, Sakhalin media, educational graphics, captions, and delivery profiles.

## Responsibility split

```text
OpenCode
  -> development

Hermes
  -> future operator/control plane

OpenMontage / Sakhalin Kids
  -> production state, scene routing, approvals, budgets, artifacts

Character Runtime
  -> locked core-character identity and acting renders

Hypit
  -> optional semantic composition and derivatives

HyperFrames / Remotion
  -> deterministic graphics/composition runtimes

FFmpeg
  -> assembly, encode, technical QA

DeepSeek Harness
  -> bounded research/review/QA
```

Hypit is subordinate to approved Sakhalin/OpenMontage artifacts. It does not become a competing workflow engine.

## Core invariants

1. OpenMontage/Sakhalin Kids remains the single production-state owner.
2. Core characters are supplied by the local Character Runtime or approved locked renders/assets.
3. Hypit must not silently replace a core character with text-to-video generation.
4. Inputs are schema-validated and reference explicit episode/scene revisions.
5. Paid provider calls remain behind the normal estimate/validate/budget/reserve/call/reconcile boundary.
6. Secrets remain outside prompts, composition artifacts, logs, and provenance.
7. Hypit receives no arbitrary shell, filesystem, or network authority.
8. Every derivative records lineage to its approved source revision and asset versions.
9. Human editorial approvals remain authoritative.
10. Automated publishing is outside this integration.

## Semantic handoff

A future adapter should receive a narrow package similar to:

```yaml
episode_revision: ep-001:r4
scene_plan_revision: scenes:r3
render_profile: youtube-master

scenes:
  - id: scene-001
    type: character_dialogue
    video_asset: render:scene-001:v2
    dialogue_timing: timing:scene-001:v3
    captions: captions:scene-001:v3

  - id: scene-002
    type: real_footage
    video_asset: okhotsk-sea-drone-001:v1

outputs:
  - youtube-master
  - vertical-short
  - teaser
```

Exact schema must be designed only when the pilot is implemented.

The adapter may compose approved inputs, but it must not mutate the source episode revision or character definitions.

## Character-driven format library

Hypit may later help encode repeatable dramaturgic patterns, not character-specific rendering code.

Candidate format IDs:

- `makar_question` — notice -> ask -> hypothesis -> check;
- `leva_explain` — question -> facts -> model -> test -> conclusion;
- `tikhon_safety` — situation -> risk -> safe action -> explanation;
- `anna_deeper` — surface observation -> hidden process -> comparison -> discovery;
- `antoshka_journey` — place/story -> clue -> route -> meeting/discovery.

These formats describe editorial structure. They must not duplicate rig, pose, viseme, or renderer logic.

## Reference-video policy

Reference or viral videos may be analyzed only when rights and intended use permit it.

Preferred use:

- pacing pattern;
- hook structure;
- shot rhythm;
- caption density;
- transition grammar;
- information sequencing.

Do not treat a reference as permission to copy protected footage, audio, artwork, script text, or distinctive creative expression.

For the children's channel, mass production of near-identical variants is explicitly not a target. One approved story may produce a limited set of meaningful platform adaptations.

## HYPIT-P01 pilot

### Preconditions

- `SKIDS-013` is complete and visually accepted;
- core character asset locks are working;
- a stable render path exists without Hypit;
- pilot work does not block the active SKIDS milestone;
- exact Hypit release/commit is selected and pinned;
- license and security review is completed before production adoption.

A sandbox experiment may happen after `SKIDS-013`; the production adoption decision should wait until Milestone 07 has exercised mixed scene types and delivery contracts.

### Scope

Use one 45–60 second educational short based on approved Sakhalin Kids material.

Minimum outputs:

- base 16:9 composition;
- 9:16 vertical derivative;
- approximately 15 second teaser;
- subtitles/captions;
- review metadata linking all outputs to the same source revision.

Use only characters currently approved for production at the time of the pilot.

### Prohibited in pilot

- automatic YouTube publishing;
- 100-variant generation;
- unbounded provider calls;
- arbitrary third-party URL ingestion;
- character redesign;
- hidden character regeneration;
- replacement of OpenMontage checkpoints/state;
- production database introduction solely for Hypit.

### Acceptance

The pilot is successful only if:

- exact Hypit version/commit is recorded;
- source revision and asset lineage survive into every output;
- locked character identity remains unchanged;
- one source revision can produce the required derivatives without manual reconstruction;
- captions/timing remain correct after one controlled dialogue/timing change;
- provider calls are visible, bounded, and cost-accounted;
- technical QA remains reproducible;
- human edit time, render time, retries/failures, and provider cost are measured;
- result is compared against the existing non-Hypit production path.

After the pilot, record one explicit decision:

- `adopt as optional adapter`;
- `keep sandbox-only`;
- `reject`.

## Production adoption gate

If adopted, implementation should remain an adapter boundary:

```text
Sakhalin/OpenMontage artifacts
        |
validated Hypit handoff
        |
Hypit composition
        |
render profiles / delivery artifacts
```

Do not make screenplay data depend on a Hypit-specific provider contract.

Do not make OpenMontage core depend on Hypit.

## Reproducibility metadata

When Hypit is used, record at minimum:

- Sakhalin Kids commit;
- OpenMontage commit;
- Hypit release/commit;
- episode and scene revision IDs;
- character asset versions;
- source media asset IDs/versions;
- output render profile;
- external model/provider identifiers where applicable;
- important seeds/settings where applicable;
- cost report reference.

## Security review checklist

Before production adoption verify:

- package/source provenance and pinned dependency;
- license terms for internal/commercial use;
- credential handling;
- network destinations and provider access;
- filesystem write boundaries;
- HTML/script execution boundaries if composition uses generated markup;
- dependency/supply-chain posture;
- resource/time/concurrency limits;
- redacted logs;
- failure behavior when budget, provider, or state is unavailable.

## Non-goals

This integration does not:

- replace OpenMontage;
- replace the Character Runtime;
- replace HyperFrames/Remotion automatically;
- create a new episode state machine;
- authorize literal cloning of arbitrary third-party viral videos;
- optimize for maximum variant count;
- enable automated publishing;
- change the current `SKIDS-005` implementation priority.
