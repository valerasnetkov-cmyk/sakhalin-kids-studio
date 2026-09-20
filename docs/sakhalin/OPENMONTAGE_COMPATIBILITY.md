# Sakhalin Kids Studio — OpenMontage Compatibility

## Pinned upstream

```text
OpenMontage
https://github.com/calesthio/OpenMontage
commit: 08e2151fa02de28a5d6a312b3d575692bf147ad7
```

Do not silently follow upstream `main`.

Before upgrading, compare schema/tool contracts and rerun the Character Runtime proof.

## How to obtain pinned checkout

Clone separately; do not vendor into this repository:

```bash
git clone https://github.com/calesthio/OpenMontage.git /path/to/OpenMontage
cd /path/to/OpenMontage
git checkout 08e2151fa02de28a5d6a312b3d575692bf147ad7
```

Then verify with:

```bash
OPENMONTAGE_ROOT=/path/to/OpenMontage python scripts/verify-skids-001.py
```

## Compatibility Matrix

Statuses:

- **COMPATIBLE** — upstream component exists and can be reused without Sakhalin-specific replacement.
- **SAKHALIN_EXTENSION_REQUIRED** — upstream does not contain the needed domain contract/tool/skill; a separate Sakhalin extension is required.
- **MISSING** — component should exist per current architecture but is not yet implemented.
- **NOT_VERIFIED** — could not verify; no assumptions made.

### Pipeline manifest and infrastructure

| Item | Upstream location | Status | Notes |
|---|---|---|---|
| pipeline manifest schema | `schemas/pipelines/pipeline_manifest.schema.json` | COMPATIBLE | reuse upstream validation |
| pipeline loader | `lib/pipeline_loader.py` | COMPATIBLE | reuse |
| `stability: beta` | schema enum `["production", "beta"]` | COMPATIBLE | already set correctly |
| `extensions.custom_tools: true` | schema field | COMPATIBLE | already set correctly |

### Meta skills

| Item | Upstream location | Status | Notes |
|---|---|---|---|
| `meta/reviewer` | `skills/meta/reviewer.md` | COMPATIBLE | reuse |
| `meta/checkpoint-protocol` | `skills/meta/checkpoint-protocol.md` | COMPATIBLE | reuse |
| `meta/animation-runtime-selector` | `skills/meta/animation-runtime-selector.md` | COMPATIBLE | do not remove |
| `meta/voice-performance-director` | `skills/meta/voice-performance-director.md` | COMPATIBLE | do not remove |

### Upstream artifact schemas

| Item | Upstream location | Status | Notes |
|---|---|---|---|
| `research_brief` | `schemas/artifacts/research_brief.schema.json` | COMPATIBLE | reuse |
| `proposal_packet` | `schemas/artifacts/proposal_packet.schema.json` | COMPATIBLE | reuse |
| `decision_log` | `schemas/artifacts/decision_log.schema.json` | COMPATIBLE | reuse |
| `script` | `schemas/artifacts/script.schema.json` | COMPATIBLE | reuse |
| `scene_plan` | `schemas/artifacts/scene_plan.schema.json` | COMPATIBLE | reuse |
| `asset_manifest` | `schemas/artifacts/asset_manifest.schema.json` | COMPATIBLE | reuse/adapt carefully |
| `edit_decisions` | `schemas/artifacts/edit_decisions.schema.json` | COMPATIBLE | reuse |
| `render_report` | `schemas/artifacts/render_report.schema.json` | COMPATIBLE | reuse |
| `final_review` | `schemas/artifacts/final_review.schema.json` | COMPATIBLE | reuse |
| `publish_log` | `schemas/artifacts/publish_log.schema.json` | COMPATIBLE | reuse |
| `character_design` | `schemas/artifacts/character_design.schema.json` | COMPATIBLE | upstream run artifact; not our long-lived CharacterSpec |
| `rig_plan` | `schemas/artifacts/rig_plan.schema.json` | COMPATIBLE | adapter likely required; RigProfile != rig_plan semantically |
| `pose_library` | `schemas/artifacts/pose_library.schema.json` | COMPATIBLE | adapter likely required |
| `action_timeline` | `schemas/artifacts/action_timeline.schema.json` | COMPATIBLE | adapter likely required |
| `character_qa_report` | `schemas/artifacts/character_qa_report.schema.json` | COMPATIBLE | adapter likely required for Sakhalin extensions |

### Sakhalin domain contracts (SAKHALIN_EXTENSION_REQUIRED)

| Item | Status | Target milestone |
|---|---|---|
| `CharacterSpec` | VERIFIED | SKIDS-002 |
| `RigProfile` | VERIFIED | SKIDS-004 |
| `Pose` | VERIFIED | SKIDS-005 |
| `Action` | VERIFIED | SKIDS-005 |
| `VisemeTimeline` | VERIFIED | SKIDS-006 |
| `dialogue_manifest` | SAKHALIN_EXTENSION_REQUIRED | Milestone 02 |
| `viseme_timelines` | SAKHALIN_EXTENSION_REQUIRED | SKIDS-006 |
| `child_content_qa` | SAKHALIN_EXTENSION_REQUIRED | post-proof |
| `factual_qa` | SAKHALIN_EXTENSION_REQUIRED | post-proof |
| `production_qa` | SAKHALIN_EXTENSION_REQUIRED | post-proof |

### Sakhalin domain services (implemented)

| Item | Status | Notes |
|---|---|---|
| `CharacterLoader` domain service | IMPLEMENTED | SKIDS-003; standalone domain service, no OpenMontage coupling |

### Sakhalin custom tools (SAKHALIN_EXTENSION_REQUIRED)

| Item | Status | Target milestone |
|---|---|---|
| `sakhalin_lipsync` | SAKHALIN_EXTENSION_REQUIRED | SKIDS-006 |
| `sakhalin_character_loader` | SAKHALIN_EXTENSION_REQUIRED | pending; thin adapter over domain `CharacterLoader` |
| `sakhalin_media_library` | SAKHALIN_EXTENSION_REQUIRED | post-proof |
| `sakhalin_action_timeline` | SAKHALIN_EXTENSION_REQUIRED | SKIDS-007 |
| `sakhalin_character_renderer` | SAKHALIN_EXTENSION_REQUIRED | SKIDS-008 |
| `sakhalin_character_reviewer` | SAKHALIN_EXTENSION_REQUIRED | SKIDS-010 |

### Sakhalin director skills (MISSING)

| Item | Status | Notes |
|---|---|---|
| `pipelines/sakhalin-kids/executive-producer` | MISSING | create per stage |
| `pipelines/sakhalin-kids/research-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/proposal-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/script-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/storyboard-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/voice-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/lipsync-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/asset-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/animation-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/compose-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/qa-director` | MISSING | create per stage |
| `pipelines/sakhalin-kids/publish-director` | MISSING | create per stage |

### Custom playbook

| Item | Status | Notes |
|---|---|---|
| `sakhalin-kids` playbook | SAKHALIN_EXTENSION_REQUIRED | not implemented; referenced in `compatible_playbooks` |

## Sakhalin / OpenMontage Domain Boundary

```
Sakhalin long-lived domain
--------------------------
CharacterSpec
RigProfile
Pose
Action
VisemeTimeline
Character asset versions

        |
        | adapters
        v

OpenMontage production artifacts
--------------------------------
character_design
rig_plan
pose_library
action_timeline
asset_manifest
character_qa_report
scene_plan
edit_decisions
render_report
```

CharacterSpec describes a persistent channel character.

character_design is a production-run artifact.

They must not automatically become the same entity.

The same applies to RigProfile vs rig_plan, Pose vs pose_library entries, and Action vs action_timeline. Pose/Action contracts are defined by SKIDS-005, but runtime mapping remains intentionally deferred. Lifecycle and semantics may differ; adapters are required.

## Verified against pinned checkout (SKIDS-001)

All checks below were executed against the pinned OpenMontage checkout at `08e2151fa02de28a5d6a312b3d575692bf147ad7`:

- pipeline manifest schema validation (name, version, stability, extensions, stage count);
- meta skills file existence (`reviewer`, `checkpoint-protocol`, `animation-runtime-selector`, `voice-performance-director`);
- upstream artifact schema file existence (all 15 production artifacts);
- upstream character tool file existence (`character_animation.py`, `__init__.py`);
- `compatible_playbooks` references (recommended + also_works);
- Sakhalin extension cross-reference (24/24 referenced in manifest).

See `scripts/verify-skids-001.py` output for full details.

## Known gaps (expected, non-blocking for SKIDS-001)

1. Sakhalin director skills are not yet implemented.
2. Sakhalin custom tools are not yet implemented.
3. `dialogue_manifest` and `viseme_timelines` require Sakhalin contracts.
4. child/factual/production QA artifacts require Sakhalin contracts.
5. Custom Sakhalin playbook is not yet implemented.
6. Full pipeline execution is not possible until subsequent milestones.

These are planned extension points, not defects.

## NOT_VERIFIED items (future integration)

- HyperFrames/Remotion Sakhalin render integration.
- TTS provider integration.
- Custom Sakhalin tools until implemented.
- Custom Sakhalin playbook until implemented.
