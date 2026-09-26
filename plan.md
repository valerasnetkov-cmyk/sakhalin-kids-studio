# Sakhalin Kids Studio — Plan

## Current phase

SKIDS-001 repository scaffolding complete.
SKIDS-002 CharacterSpec schema complete.
SKIDS-003 CharacterLoader domain service complete.
SKIDS-004 RigProfile contract and canonical profiles complete.\nSKIDS-005 Pose/Action declarative contracts complete.\nSKIDS-006 Semantic viseme timeline contract complete.

Primary development workflow: OpenCode.

## Active milestone

### Milestone 01 — Character Runtime Proof

Scope:

- Makar;
- Leva;
- one location;
- 10–15 seconds;
- one short Russian dialogue;
- no paid AI-video generation.

Tasks:

- [x] SKIDS-001 — repository scaffolding for runtime modules.
- [x] SKIDS-002 — CharacterSpec domain schema.
- [x] SKIDS-003 — character loader.
- [x] SKIDS-004 — rig profile contract.
- [x] SKIDS-005 — pose/action contract.
- [x] SKIDS-006 — viseme contract.
- [ ] SKIDS-007 — acting + mouth timeline merge.
- [ ] SKIDS-008 — SVG scene renderer.
- [ ] SKIDS-009 — HyperFrames or Remotion handoff.
- [ ] SKIDS-010 — character QA.
- [ ] SKIDS-011 — Makar fixture assets.
- [ ] SKIDS-012 — Leva fixture assets.
- [ ] SKIDS-013 — 10–15 second render smoke test.

## Stop condition

After SKIDS-013, stop implementation and evaluate the visual proof before expanding scope.

Do not proceed automatically to all five production characters.

## Next milestone after approval

Milestone 02 — Russian Voice + Lip Sync refinement.

## Current constraints

- Keep Sakhalin-specific logic outside OpenMontage core where possible.
- Authored source files must stay at or below 400 physical lines.
- No secrets in Git.
- No silent character regeneration.
- No paid AI-video in Milestone 01.
- Provider calls must be budget bounded.

## Approved future architecture

After the visual proof is accepted:

### Control plane

- [ ] Add a narrow Sakhalin Kids Control API.
- [ ] Expose bounded MCP tools for episode/status/approval/render operations.
- [ ] Connect a dedicated Hermes `sakhalin-kids` profile.
- [ ] Keep OpenMontage as the only production-state owner.

See: `docs/sakhalin/CONTROL_PLANE.md`.

### DeepSeek Harness

Roll out only after the core production contracts are stable:

- [ ] H1 — research workflow.
- [ ] H2 — script review.
- [ ] H2 — factual QA.
- [ ] H3 — production QA.

Do not use Harness for episode state transitions, publishing, render orchestration, or core-character mutation.

See: `docs/sakhalin/HARNESS_INTEGRATION.md`.

### Hypit semantic composition

Hypit is approved only as a candidate optional adapter; it is not part of the active Character Runtime milestone.

- [ ] HYPIT-P01 — start only after `SKIDS-013` visual acceptance.
- [ ] Pin exact Hypit release/commit for the pilot.
- [ ] Complete license/security review before any production adoption.
- [ ] Define a narrow semantic-composition handoff from approved Sakhalin/OpenMontage artifacts.
- [ ] Reuse locked core-character outputs/assets; prohibit hidden text-to-video character regeneration.
- [ ] Produce 16:9, 9:16 and teaser outputs from one approved source revision.
- [ ] Measure edit time, render time, retries/failures and provider cost against the non-Hypit path.
- [ ] Make production adoption decision only after the Milestone 07 integration episode contracts are stable.

See: `docs/sakhalin/HYPIT_INTEGRATION.md`.

## Production architecture backlog

These items are approved but deferred until the Character Runtime Proof is accepted.

### Runtime / upstream

- [ ] Pin and integrate an executable OpenMontage checkout.
- [ ] Validate `sakhalin-kids.yaml` with the pinned OpenMontage loader/schema.
- [ ] Implement all referenced Sakhalin director skills/tools before declaring the pipeline executable.
- [ ] Define and test the Production Director execution role.
- [ ] Add upstream compatibility/upgrade checks.

See: `docs/sakhalin/RUNTIME_AND_UPSTREAM.md`.

### Asset lifecycle

- [ ] Add stable asset IDs, versions, checksums, provenance, and rights metadata.
- [ ] Pin exact asset versions per episode revision.
- [ ] Add dependency invalidation so only affected outputs become stale.
- [ ] Separate Git, durable media storage, and workspace/cache.
- [ ] Add S3-compatible storage only when needed.
- [ ] Add backup plus tested restore procedure.

See: `docs/sakhalin/ASSET_LIFECYCLE.md`.

### Job execution

- [ ] Add explicit job/attempt states and idempotency for paid/long-running work.
- [ ] Track external provider request IDs and unknown external state.
- [ ] Add resume/retry/cancel semantics.
- [ ] Add approval receipts bound to revision/hash.
- [ ] Add per-job/attempt cost reservation and reconciliation.
- [ ] Introduce PostgreSQL only when multi-worker/control-plane reliability requires it.

See: `docs/sakhalin/JOB_EXECUTION.md`.

### Media delivery

- [ ] Define named proof/review/master render profiles.
- [ ] Keep dialogue/music/SFX stems where practical.
- [ ] Evaluate WhisperX for Russian alignment after the proof.
- [ ] Add pronunciation dictionary and listening review.
- [ ] Add deterministic FFmpeg media QA.
- [ ] Evaluate OpenTimelineIO/editable timeline export before routine full episodes.
- [ ] Add curated ComfyUI workflows only after character/runtime contracts stabilize.

See: `docs/sakhalin/MEDIA_DELIVERY.md`.

### Editorial / publishing

- [ ] Define explicit target age/audience and episode editorial contract.
- [ ] Add a claims ledger mapping educational claims to sources and script/scene usage.
- [ ] Track documentary vs generated/reconstructed visual provenance.
- [ ] Add rights, safety, pronunciation, and character-continuity release checks.
- [ ] Keep YouTube publication manual-first.
- [ ] Verify current YouTube audience/synthetic-media requirements before automation.
- [ ] Later connect production cost/revision data to audience-retention analytics.

See: `docs/sakhalin/EDITORIAL_AND_PUBLISHING.md`.
