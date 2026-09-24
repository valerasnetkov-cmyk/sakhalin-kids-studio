# Changelog

## 2026-09-25

### Fixed — Fixture refinements (SKIDS-011, SKIDS-012)

- `library/characters/makar/art/front.svg`, `library/characters/leva/art/front.svg` — `open` eye variants now draw only the sclera; drawn pupils removed so pupils belong exclusively to `pupil_left`/`pupil_right`.
- Pupil parts (makar, leva) — added `hidden` variant (empty layer) for closed-eye states.
- `blink_closed` poses (makar, leva) — eyes `closed`, `pupil_left`/`pupil_right` `hidden`.
- Gaze-pupil synchronization — every pose declaring `gaze.direction` now sets pupil variants to the same direction (makar idle=center, point=right; leva idle=center, think=up).
- `tests/sakhalin/test_makar_fixture.py`, `tests/sakhalin/test_leva_fixture.py` — strengthened from frame inequality to explicit `data-variant`/`display` state assertions; added tests for eye/pupil separation, hidden pupil variant, and gaze-pupil synchronization (30 → 33 tests each).
- `docs/sakhalin/MAKAR_FIXTURE.md`, `docs/sakhalin/LEVA_FIXTURE.md` — updated poses, gaze, blink, and renderer compatibility sections.

## 2026-09-22

### Added — SKIDS-012

- `library/characters/leva/` — first reusable structured Leva character bundle (proof fixture).
- `library/characters/leva/character.yaml` — Leva CharacterSpec (sea_lion, sea_lion_cartoon, calm_reasoning_partner).
- `library/characters/leva/art/front.svg` — structured rigged SVG with 9 sea_lion_cartoon parts, 10 visemes, 5 gaze directions, 2 expressions, blink variants.
- `library/characters/leva/poses/` — 6 proof poses: idle, blink_closed, look_left, look_right, think, talk.
- `library/characters/leva/actions/` — 5 proof actions: idle, blink, look, think, talk.
- `tests/sakhalin/test_leva_fixture.py` — 30 tests covering spec schema, identity, art structure, visemes, gaze, expressions, action existence, pose/action validation, mouth ownership, CharacterQA pass, SvgSceneRenderer proof (idle, blink, gaze, think, viseme, deterministic), security, and size limits.
- `docs/sakhalin/LEVA_FIXTURE.md` — fixture documentation with artistic QA boundary.

### Changed — SKIDS-012

- plan.md SKIDS-012 marked complete.

## 2026-09-22

### Added — SKIDS-011

- `library/characters/makar/` — first reusable structured Makar character bundle (proof fixture).
- `library/characters/makar/character.yaml` — Makar CharacterSpec (fox, fox_cartoon, lead_researcher).
- `library/characters/makar/art/front.svg` — structured rigged SVG with 12 fox_cartoon parts, 10 visemes, 5 gaze directions, 2 expressions, blink variants.
- `library/characters/makar/poses/` — 7 proof poses: idle, blink_closed, look_left, look_right, point, talk, curious.
- `library/characters/makar/actions/` — 5 proof actions: idle, blink, look, point, talk.
- `tests/sakhalin/test_makar_fixture.py` — 30 tests covering spec schema, identity, art structure, visemes, gaze, expressions, action existence, pose/action validation, mouth ownership, CharacterQA pass, SvgSceneRenderer proof (idle, blink, gaze, point, viseme, deterministic), security, and size limits.
- `docs/sakhalin/MAKAR_FIXTURE.md` — fixture documentation with artistic QA boundary.

### Changed — SKIDS-011

- plan.md SKIDS-011 marked complete.

## 2026-09-21

### Added — SKIDS-010

- `tools/character/sakhalin/character_qa.py` — CharacterReviewer domain service for deterministic structural character QA.
- `tests/sakhalin/test_character_qa.py` — 48 character QA tests covering canon, schema, rig, visemes, gaze, expressions, blink, poses, actions, continuity, determinism, OpenMontage report, and visual boundary.
- `config/sakhalin/team_canon.json` — machine-readable team canon (version 1.0).
- `docs/sakhalin/CHARACTER_QA.md` — character QA documentation.

### Changed — SKIDS-010

- CharacterReviewer marked IMPLEMENTED in OpenMontage compatibility documentation.
- TEAM_CANON.md updated with machine-readable canon reference (section 12).
- CHARACTER_FORMAT.md duplicate section numbering fixed (9→10–16).
- ARCHITECTURE.md character runtime flow updated to include CharacterReviewer.
- plan.md SKIDS-010 marked complete.

### Changed — Core character canon

- Added `docs/sakhalin/TEAM_CANON.md` as the canonical persistent-cast identity reference.
- Corrected `antoshka`: Antoshka is a small human boy, traveler and storyteller, not a seagull/animal mascot.
- Replaced stale future `seagull_cartoon` references for Antoshka with candidate `human_child_cartoon` terminology.
- Added explicit SKIDS-010/011/012 character QA and fixture priorities without expanding the current Makar + Leva proof scope.

## 2026-09-21

- `tools/character/sakhalin/hyperframes_handoff.py` — HyperFramesHandoff domain service for deterministic offline workspace generation.
- `tests/sakhalin/test_hyperframes_handoff.py` — 23 handoff tests covering boundary union, interval generation, ms→seconds conversion, determinism, immutability, path safety, workspace structure, and SvgSceneRenderer integration.

### Changed — SKIDS-009

- HyperFramesHandoff marked IMPLEMENTED in OpenMontage compatibility documentation.
- ARCHITECTURE.md character runtime flow updated to include TimelineMerger → SvgSceneRenderer → HyperFrames handoff.

### Changed — Core character canon

- Added `docs/sakhalin/TEAM_CANON.md` as the canonical persistent-cast identity reference.
- Corrected `antoshka`: Antoshka is a small human boy, traveler and storyteller, not a seagull/animal mascot.
- Replaced stale future `seagull_cartoon` references for Antoshka with candidate `human_child_cartoon` terminology.
- Added explicit SKIDS-010/011/012 character QA and fixture priorities without expanding the current Makar + Leva proof scope.

## 2026-09-21

### Added — SKIDS-008

- `tools/character/sakhalin/svg_scene_renderer.py` — SvgSceneRenderer domain service for deterministic frame-oriented SVG scene composition.
- `tests/sakhalin/test_svg_scene_renderer.py` — 33 renderer tests covering composition, timestamp boundary, pose resolution, rig matching, SVG state application, expression/gaze/viseme, placement, safety, and immutability.

### Changed — SKIDS-008

- SvgSceneRenderer marked IMPLEMENTED in OpenMontage compatibility documentation.

## 2026-09-20

### Added — SKIDS-007

- `tools/character/sakhalin/timeline_merger.py` — TimelineMerger domain service for deterministic acting + mouth merge.
- `tests/sakhalin/test_timeline_merger.py` — 34 merger tests covering validation, temporal semantics, output invariants, and ownership boundary.
- `docs/sakhalin/TIMELINE_MERGE.md` — merge algorithm, duration policy, and output contract documentation.

### Changed — SKIDS-007

- TimelineMerger marked IMPLEMENTED in OpenMontage compatibility documentation.
- MOTION_CONTRACT.md references timeline merge in the ownership boundary section.

## 2026-09-20

### Added — SKIDS-006

- `schemas/sakhalin/viseme_timeline.schema.json` — renderer-agnostic VisemeTimeline domain contract for Russian lip-sync.
- `tests/sakhalin/test_viseme_timeline_schema.py` — 31 VisemeTimeline contract tests.

### Changed — SKIDS-006

- VisemeTimeline marked VERIFIED in OpenMontage compatibility documentation.
- LIPSYNC.md data model section updated to reference VisemeTimeline domain contract.
- Mouth ownership boundary documented: VisemeTimeline owns lip-sync data; Pose/Action cannot control mouth.
- VisemeTimeline is character-independent and provider-independent.

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