# Changelog

## 2026-09-20

### Added — SKIDS-005

- `schemas/sakhalin/pose.schema.json` — reusable Pose domain contract.
- `schemas/sakhalin/action.schema.json` — timed Action domain contract.
- `tests/sakhalin/test_pose_schema.py` — 20 Pose contract tests.
- `tests/sakhalin/test_action_schema.py` — 20 Action contract tests.
- `docs/sakhalin/MOTION_CONTRACT.md` — motion ownership, talk/viseme boundary, and future compiler boundary.

### Changed — SKIDS-005

- Pose and Action marked VERIFIED in OpenMontage compatibility documentation.
- Character format now references the canonical motion contract instead of duplicating Pose/Action examples.
- Mouth ownership is explicit: Pose/Action cannot control `mouth`; VisemeTimeline owns lip-sync data.
- No canonical pose/action library or OpenMontage adapter/compiler added in this milestone.

## 2026-09-20

### Added — SKIDS-003

- `tools/character/sakhalin/__init__.py` — Sakhalin character tools package.
- `tools/character/sakhalin/character_loader.py` — CharacterLoader domain service for persistent core characters.
- `tests/sakhalin/test_character_loader.py` — 24 loader test cases (68 total with SKIDS-002).

### Changed — SKIDS-003

- CharacterLoader domain service distinguishes from OpenMontage tool adapter in compatibility docs.

### Fixed — SKIDS-003 hardening

- Eliminated double-resolve TOCTOU: single `_resolve_contained_manifest_path` method.
- Bounded file read: `fh.read(MAX + 1)` instead of unbounded `read_bytes()`.
- Schema validation errors redacted: report field + validator, not raw manifest values.
- Identifier pattern extracted from CharacterSpec schema `$defs.identifier.pattern`.
- `Draft202012Validator.check_schema` errors wrapped in `CharacterLoadError`.

## 2026-09-20

### Added — SKIDS-004

- `schemas/sakhalin/rig_profile.schema.json` — RigProfile domain contract (JSON Schema Draft 2020-12).
- `library/rig_profiles/fox_cartoon.yaml` — canonical fox rig profile.
- `library/rig_profiles/sea_lion_cartoon.yaml` — canonical sea lion rig profile.
- `tests/sakhalin/test_rig_profile_schema.py` — 35 RigProfile schema tests.

### Changed — SKIDS-004

- RigProfile marked VERIFIED in compatibility docs.
- CharacterSpec/RigProfile identifier patterns verified consistent.

## 2026-09-20

### Added — SKIDS-002

- `schemas/sakhalin/character_spec.schema.json` — CharacterSpec domain contract (JSON Schema Draft 2020-12).
- `tests/sakhalin/test_character_spec_schema.py` — 44 targeted schema validation tests.

### Changed — SKIDS-002

- SKIDS-002 narrowed from "all character schemas" to "CharacterSpec only".
- `dialogue_manifest` target milestone moved from SKIDS-002 to Milestone 02.
- `OPENCODE_START.md` and `plan.md` updated to reflect revised task scope.

## 2026-09-20

### Added

- SKIDS-001 repository scaffolding: allowed cast policy, OpenMontage compatibility matrix, verification script.
- `config/sakhalin/allowed_cast.json` — core cast policy with closed roster.
- `docs/sakhalin/OPENMONTAGE_COMPATIBILITY.md` — pinned upstream, compatibility matrix, domain boundary.
- `scripts/verify-skids-001.py` — automated verification for manifest, cast, line gate, secrets.

### Changed

- Initial Sakhalin Kids Studio architecture on top of OpenMontage.
- Core project documentation for architecture, character format, implementation plan, and Russian lip-sync.
- Initial `sakhalin-kids` pipeline manifest.
- `AGENTS.md` with persistent OpenCode project instructions.
- `OPENCODE_START.md` as the primary OpenCode bootstrap brief.
- `docs/sakhalin/CONTROL_PLANE.md` defining Hermes as the future operator/control plane.
- `docs/sakhalin/HARNESS_INTEGRATION.md` defining DeepSeek Harness as a future bounded cognitive layer for research/review/QA.
- Runtime/upstream specification defining the Production Director role and pinned OpenMontage integration.
- Asset lifecycle specification covering versions, provenance, rights, storage, backup, and selective invalidation.
- Job execution specification covering idempotency, retries, resume, costs, approvals, and future workers.
- Media delivery specification covering editable delivery, FFmpeg QA, Russian alignment, pronunciation, and future ComfyUI integration.
- Editorial/publishing specification covering educational claims, safety, rights, platform review, and analytics.

### Changed

- OpenCode is now the primary coding-agent workflow for this repository.
- README updated to point development sessions to `AGENTS.md` and `OPENCODE_START.md`.
- `sakhalin-kids.yaml` changed from unsupported `stability: experimental` to `stability: beta` for the pinned OpenMontage manifest schema.
- Sakhalin pipeline now explicitly permits registered custom tools required by project-specific runtime integrations.

### Notes

- `CODEX_START.md` is retained as legacy bootstrap documentation and is not the primary workflow.
- First implementation target remains `SKIDS-001 -> SKIDS-013`: the 10–15 second Makar + Leva Character Runtime Proof.
- Hermes and DeepSeek Harness integration is explicitly deferred until after that proof is accepted.
- PostgreSQL, S3/object storage, ComfyUI orchestration, WhisperX, OpenTimelineIO, restic, Langfuse, and automated publishing are documented as planned/candidate integrations, not current runtime dependencies.