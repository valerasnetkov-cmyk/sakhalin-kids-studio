# Changelog

## 2026-09-20

### Added

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