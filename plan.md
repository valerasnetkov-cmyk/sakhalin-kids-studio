# Sakhalin Kids Studio — Plan

## Current phase

Pre-scaffold architecture is complete.

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

- [ ] SKIDS-001 — repository scaffolding for runtime modules.
- [ ] SKIDS-002 — character/rig/pose/action/viseme schemas.
- [ ] SKIDS-003 — character loader.
- [ ] SKIDS-004 — rig profile contract.
- [ ] SKIDS-005 — pose/action contract.
- [ ] SKIDS-006 — viseme contract.
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
